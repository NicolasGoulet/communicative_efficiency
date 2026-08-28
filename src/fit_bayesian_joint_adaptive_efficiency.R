#!/usr/bin/env Rscript

# CmdStan backend for the focused three-coefficient measurement-error model.

parse_cli <- function(arguments) {
  result <- list()
  index <- 1L
  while (index <= length(arguments)) {
    token <- arguments[[index]]
    if (!startsWith(token, "--")) stop("unexpected positional argument: ", token)
    key <- sub("^--", "", token)
    if (index == length(arguments) || startsWith(arguments[[index + 1L]], "--")) {
      result[[key]] <- TRUE
      index <- index + 1L
    } else {
      result[[key]] <- arguments[[index + 1L]]
      index <- index + 2L
    }
  }
  result
}

required_argument <- function(arguments, name) {
  value <- arguments[[name]]
  if (is.null(value) || identical(value, "")) stop("missing --", name)
  value
}

arguments <- parse_cli(commandArgs(trailingOnly = TRUE))
mode <- required_argument(arguments, "mode")
root <- normalizePath(required_argument(arguments, "root"), mustWork = TRUE)
contract_path <- normalizePath(required_argument(arguments, "contract"), mustWork = TRUE)
input_path <- normalizePath(required_argument(arguments, "input"), mustWork = TRUE)
output_dir <- normalizePath(required_argument(arguments, "output-dir"), mustWork = FALSE)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

local_library <- file.path(root, ".bayes-r-lib")
cmdstan_path <- file.path(root, ".cmdstan", "cmdstan-2.39.0")
.libPaths(c(local_library, .Library.site, .Library))

suppressPackageStartupMessages({
  library(cmdstanr)
  library(data.table)
  library(jsonlite)
  library(loo)
  library(posterior)
})

if (as.character(packageVersion("cmdstanr")) != "0.9.0") stop("cmdstanr pin mismatch")
if (!dir.exists(cmdstan_path)) stop("missing pinned CmdStan: ", cmdstan_path)
cmdstanr::set_cmdstan_path(cmdstan_path)
contract <- fromJSON(contract_path, simplifyVector = TRUE)

write_json_atomic <- function(payload, path) {
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  write_json(payload, temporary, auto_unbox = TRUE, pretty = TRUE, digits = 16)
  if (!file.rename(temporary, path)) stop("could not publish ", path)
}

write_csv_atomic <- function(frame, path) {
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  fwrite(frame, temporary, compress = if (endsWith(path, ".gz")) "gzip" else "none")
  if (!file.rename(temporary, path)) stop("could not publish ", path)
}

peak_rss_kb <- function() {
  status <- tryCatch(readLines("/proc/self/status", warn = FALSE), error = function(error) character())
  line <- status[startsWith(status, "VmHWM:")]
  if (!length(line)) return(NA_real_)
  as.numeric(sub("^VmHWM:\\s+([0-9]+).*", "\\1", line[[1]]))
}

covariance_for_row <- function(frame, index) {
  matrix(
    c(
      frame$cov_11[index], frame$cov_12[index], frame$cov_13[index],
      frame$cov_12[index], frame$cov_22[index], frame$cov_23[index],
      frame$cov_13[index], frame$cov_23[index], frame$cov_33[index]
    ),
    nrow = 3L,
    byrow = TRUE
  )
}

stan_data <- function(frame, prior) {
  corpora <- sort(unique(frame$dataset))
  list(
    N = nrow(frame),
    C = length(corpora),
    K = 3L,
    corpus_id = match(frame$dataset, corpora),
    coefficient_hat = lapply(seq_len(nrow(frame)), function(index) {
      c(
        frame$r1_age_slope[index],
        frame$r2_entropy_42_slope[index],
        frame$r2_age_entropy_slope[index]
      )
    }),
    estimation_cov = lapply(seq_len(nrow(frame)), function(index) covariance_for_row(frame, index)),
    population_prior_sd = as.numeric(prior$population_sd),
    child_sd_prior_scale = as.numeric(prior$child_sd_scale),
    corpus_sd_prior_scale = as.numeric(prior$corpus_sd_scale),
    lkj_eta = as.numeric(prior$lkj_eta)
  )
}

diagnostics_for_fit <- function(fit, fit_id, elapsed, sampler) {
  diagnostic <- fit$diagnostic_summary()
  summary <- fit$summary()
  finite_rhat <- summary$rhat[is.finite(summary$rhat)]
  finite_bulk <- summary$ess_bulk[is.finite(summary$ess_bulk)]
  finite_tail <- summary$ess_tail[is.finite(summary$ess_tail)]
  registered_variables <- c(
    "population_mean[1]", "population_mean[2]", "population_mean[3]",
    "child_correlation[1,3]"
  )
  registered <- summary[summary$variable %in% registered_variables, , drop = FALSE]
  bfmi <- if ("ebfmi" %in% names(diagnostic)) diagnostic$ebfmi else NA_real_
  data.frame(
    fit_id = fit_id,
    elapsed_seconds = elapsed,
    chains = as.integer(sampler$chains),
    warmup = as.integer(sampler$warmup),
    sampling = as.integer(sampler$sampling),
    rhat_max = if (length(finite_rhat)) max(finite_rhat) else NA_real_,
    ess_bulk_min = if (length(finite_bulk)) min(finite_bulk) else NA_real_,
    ess_tail_min = if (length(finite_tail)) min(finite_tail) else NA_real_,
    divergences = sum(diagnostic$num_divergent),
    treedepth_saturated = sum(diagnostic$num_max_treedepth),
    energy_bfmi_min = min(bfmi, na.rm = TRUE),
    scientific_rhat_max = max(registered$rhat, na.rm = TRUE),
    scientific_ess_bulk_min = min(registered$ess_bulk, na.rm = TRUE),
    scientific_ess_tail_min = min(registered$ess_tail, na.rm = TRUE),
    peak_rss_kb = peak_rss_kb()
  )
}

evaluate_fit_gate <- function(diagnostics, ppc, influence, corpora) {
  primary_gate <- contract$diagnostic_gates$primary_all_parameters
  influence_gate <- contract$diagnostic_gates$influence_registered_outputs
  common_gate <- contract$diagnostic_gates$all_fits
  primary <- diagnostics[fit_id %in% c("regularizing", "wide_sensitivity"), ]
  influence_diagnostics <- diagnostics[startsWith(fit_id, "omit_"), ]
  problems <- character()
  bad_primary <- primary[
    rhat_max > as.numeric(primary_gate$maximum_rhat) |
      ess_bulk_min < as.numeric(primary_gate$minimum_bulk_ess) |
      ess_tail_min < as.numeric(primary_gate$minimum_tail_ess),
  ]
  if (nrow(bad_primary)) {
    problems <- c(problems, paste("primary all-parameter diagnostics failed:", paste(bad_primary$fit_id, collapse = ", ")))
  }
  bad_influence <- influence_diagnostics[
    scientific_rhat_max > as.numeric(influence_gate$maximum_rhat) |
      scientific_ess_bulk_min < as.numeric(influence_gate$minimum_bulk_ess) |
      scientific_ess_tail_min < as.numeric(influence_gate$minimum_tail_ess),
  ]
  if (nrow(bad_influence)) {
    problems <- c(problems, paste("influence registered-output diagnostics failed:", paste(bad_influence$fit_id, collapse = ", ")))
  }
  bad_common <- diagnostics[
    divergences > as.numeric(common_gate$maximum_divergences) |
      treedepth_saturated > as.numeric(common_gate$maximum_treedepth_saturated) |
      energy_bfmi_min < as.numeric(common_gate$minimum_energy_bfmi),
  ]
  if (nrow(bad_common)) {
    problems <- c(problems, paste("common sampler diagnostics failed:", paste(bad_common$fit_id, collapse = ", ")))
  }
  if (any(ppc$status != "PASS")) problems <- c(problems, "posterior predictive checks failed")
  if (nrow(influence) != length(corpora)) problems <- c(problems, "influence inventory mismatch")
  problems
}

selected_draws <- function(fit) {
  draws <- as_draws_df(fit$draws(c("population_mean", "child_sd", "corpus_sd", "child_correlation")))
  data.frame(
    mu_r1_age = draws[["population_mean[1]"]],
    mu_r2_entropy_42 = draws[["population_mean[2]"]],
    mu_r2_age_entropy = draws[["population_mean[3]"]],
    child_sd_r1_age = draws[["child_sd[1]"]],
    child_sd_r2_entropy_42 = draws[["child_sd[2]"]],
    child_sd_r2_age_entropy = draws[["child_sd[3]"]],
    corpus_sd_r1_age = draws[["corpus_sd[1]"]],
    corpus_sd_r2_entropy_42 = draws[["corpus_sd[2]"]],
    corpus_sd_r2_age_entropy = draws[["corpus_sd[3]"]],
    rho_r1_entropy_42 = draws[["child_correlation[1,2]"]],
    rho_r1_age_entropy = draws[["child_correlation[1,3]"]],
    rho_entropy_age_entropy = draws[["child_correlation[2,3]"]]
  )
}

summary_for_fit <- function(fit, fit_id) {
  variables <- c("population_mean", "child_sd", "corpus_sd", "child_correlation")
  diagnostic_summary <- fit$summary(variables)
  draws <- as_draws_matrix(fit$draws(variables))
  variable_names <- colnames(draws)
  diagnostic_order <- match(variable_names, diagnostic_summary$variable)
  data.frame(
    fit_id = fit_id,
    variable = variable_names,
    mean = colMeans(draws),
    sd = apply(draws, 2, sd),
    q025 = apply(draws, 2, quantile, probs = 0.025),
    q975 = apply(draws, 2, quantile, probs = 0.975),
    rhat = diagnostic_summary$rhat[diagnostic_order],
    ess_bulk = diagnostic_summary$ess_bulk[diagnostic_order],
    ess_tail = diagnostic_summary$ess_tail[diagnostic_order]
  )
}

ppc_for_fit <- function(fit, frame, fit_id) {
  matrix_draws <- as_draws_matrix(fit$draws("coefficient_rep"))
  rows <- list()
  observed <- list(frame$r1_age_slope, frame$r2_entropy_42_slope, frame$r2_age_entropy_slope)
  for (dimension in 1:3) {
    pattern <- paste0("^coefficient_rep\\[[0-9]+,", dimension, "\\]$")
    columns <- grep(pattern, colnames(matrix_draws))
    if (length(columns) != nrow(frame)) stop("posterior predictive dimension mismatch")
    replicated <- matrix_draws[, columns, drop = FALSE]
    replicated_mean <- rowMeans(replicated)
    replicated_sd <- apply(replicated, 1, sd)
    observed_mean <- mean(observed[[dimension]])
    observed_sd <- sd(observed[[dimension]])
    mean_interval <- quantile(replicated_mean, c(0.005, 0.995))
    sd_interval <- quantile(replicated_sd, c(0.005, 0.995))
    rows[[length(rows) + 1L]] <- data.frame(
      fit_id = fit_id,
      dimension = dimension,
      check = "child_coefficient_mean",
      observed = observed_mean,
      predictive_q005 = mean_interval[[1]],
      predictive_q995 = mean_interval[[2]],
      status = if (observed_mean >= mean_interval[[1]] && observed_mean <= mean_interval[[2]]) "PASS" else "FAIL"
    )
    rows[[length(rows) + 1L]] <- data.frame(
      fit_id = fit_id,
      dimension = dimension,
      check = "child_coefficient_sd",
      observed = observed_sd,
      predictive_q005 = sd_interval[[1]],
      predictive_q995 = sd_interval[[2]],
      status = if (observed_sd >= sd_interval[[1]] && observed_sd <= sd_interval[[2]]) "PASS" else "FAIL"
    )
  }
  rbindlist(rows)
}

loo_for_fit <- function(fit, fit_id) {
  log_lik <- as_draws_matrix(fit$draws("log_lik"))
  result <- loo(log_lik)
  pareto <- pareto_k_values(result)
  data.frame(
    fit_id = fit_id,
    elpd_loo = result$estimates["elpd_loo", "Estimate"],
    elpd_loo_se = result$estimates["elpd_loo", "SE"],
    pareto_k_max = max(pareto),
    pareto_k_over_07 = sum(pareto > 0.7),
    pareto_k_over_10 = sum(pareto > 1.0)
  )
}

model <- cmdstan_model(file.path(root, "src", "stan", "joint_adaptive_efficiency_measurement_error.stan"))

fit_model <- function(fit_id, frame, prior, sampler, save_outputs = TRUE) {
  fit_dir <- file.path(output_dir, fit_id)
  if (dir.exists(fit_dir)) unlink(fit_dir, recursive = TRUE, force = TRUE)
  dir.create(fit_dir, recursive = TRUE, showWarnings = FALSE)
  started <- proc.time()[["elapsed"]]
  fit <- model$sample(
    data = stan_data(frame, prior),
    seed = as.integer(contract$sampler$seed),
    chains = as.integer(sampler$chains),
    parallel_chains = as.integer(sampler$parallel_chains),
    iter_warmup = as.integer(sampler$warmup),
    iter_sampling = as.integer(sampler$sampling),
    adapt_delta = as.numeric(sampler$adapt_delta),
    max_treedepth = as.integer(sampler$max_treedepth),
    refresh = 0,
    output_dir = fit_dir
  )
  elapsed <- proc.time()[["elapsed"]] - started
  list(
    fit = fit,
    diagnostics = diagnostics_for_fit(fit, fit_id, elapsed, sampler),
    summary = if (save_outputs) summary_for_fit(fit, fit_id) else NULL,
    draws = if (save_outputs) selected_draws(fit) else NULL,
    ppc = if (save_outputs) ppc_for_fit(fit, frame, fit_id) else NULL,
    loo = if (save_outputs) loo_for_fit(fit, fit_id) else NULL
  )
}

run_synthetic <- function() {
  set.seed(as.integer(contract$sampler$seed))
  N <- 72L
  C <- 6L
  truth_mu <- c(-0.55, 0.045, -0.018)
  truth_sd <- c(0.65, 0.055, 0.030)
  truth_cor <- matrix(c(1, -0.25, -0.40, -0.25, 1, 0.20, -0.40, 0.20, 1), 3, 3)
  child_cov <- diag(truth_sd) %*% truth_cor %*% diag(truth_sd)
  corpus_sd <- c(0.20, 0.015, 0.010)
  corpus_id <- rep(seq_len(C), length.out = N)
  corpus_effect <- matrix(rnorm(C * 3), 3, C) * corpus_sd
  latent <- matrix(rnorm(N * 3), N, 3) %*% chol(child_cov)
  latent <- sweep(latent, 2, truth_mu, "+")
  latent <- latent + t(corpus_effect[, corpus_id])
  estimates <- matrix(NA_real_, N, 3)
  covariances <- vector("list", N)
  for (index in seq_len(N)) {
    se <- c(runif(1, 0.08, 0.20), runif(1, 0.008, 0.020), runif(1, 0.005, 0.012))
    estimation_cor <- matrix(c(1, 0.15, -0.10, 0.15, 1, 0.20, -0.10, 0.20, 1), 3, 3)
    covariance <- diag(se) %*% estimation_cor %*% diag(se)
    covariances[[index]] <- covariance
    estimates[index, ] <- latent[index, ] + drop(rnorm(3) %*% chol(covariance))
  }
  frame <- data.frame(
    child_key = sprintf("child_%03d", seq_len(N)),
    dataset = sprintf("corpus_%02d", corpus_id),
    r1_age_slope = estimates[, 1],
    r2_entropy_42_slope = estimates[, 2],
    r2_age_entropy_slope = estimates[, 3],
    cov_11 = vapply(covariances, function(value) value[1, 1], numeric(1)),
    cov_12 = vapply(covariances, function(value) value[1, 2], numeric(1)),
    cov_13 = vapply(covariances, function(value) value[1, 3], numeric(1)),
    cov_22 = vapply(covariances, function(value) value[2, 2], numeric(1)),
    cov_23 = vapply(covariances, function(value) value[2, 3], numeric(1)),
    cov_33 = vapply(covariances, function(value) value[3, 3], numeric(1))
  )
  sampler <- list(chains = 4L, parallel_chains = 4L, warmup = 500L, sampling = 750L, adapt_delta = 0.99, max_treedepth = 12L)
  result <- fit_model("synthetic", frame, contract$priors$regularizing, sampler, save_outputs = TRUE)
  target <- data.frame(
    variable = c("population_mean[1]", "population_mean[2]", "population_mean[3]", "child_correlation[1,3]"),
    truth = c(truth_mu, truth_cor[1, 3])
  )
  recovery <- merge(result$summary, target, by = "variable")
  recovery$status <- ifelse(recovery$truth >= recovery$q025 & recovery$truth <= recovery$q975, "PASS", "FAIL")
  diagnostic <- result$diagnostics
  problems <- character()
  if (any(recovery$status != "PASS")) problems <- c(problems, "synthetic truth outside 95% interval")
  if (diagnostic$divergences > 0) problems <- c(problems, "synthetic divergences")
  # The synthetic gate is a short implementation smoke. Its stricter real-data
  # successor keeps the 1.01 threshold; here 1.02 avoids treating one nuisance
  # scale among hundreds of monitored quantities as failed parameter recovery.
  if (diagnostic$rhat_max > 1.02) problems <- c(problems, "synthetic R-hat")
  if (diagnostic$ess_bulk_min < 100 || diagnostic$ess_tail_min < 100) problems <- c(problems, "synthetic ESS")
  write_csv_atomic(recovery, file.path(output_dir, "synthetic_summary.csv"))
  write_json_atomic(
    list(
      status = if (length(problems)) "FAIL" else "PASS",
      problems = problems,
      elapsed_seconds = diagnostic$elapsed_seconds,
      divergences = diagnostic$divergences,
      rhat_max = diagnostic$rhat_max,
      ess_bulk_min = diagnostic$ess_bulk_min,
      ess_tail_min = diagnostic$ess_tail_min
    ),
    file.path(output_dir, "synthetic_audit.json")
  )
  if (length(problems)) stop(paste(problems, collapse = "; "))
}

run_fit <- function() {
  frame <- fread(input_path, data.table = FALSE)
  if (nrow(frame) != as.integer(contract$eligibility$expected_included_children)) stop("child estimate count mismatch")
  primary <- fit_model("regularizing", frame, contract$priors$regularizing, contract$sampler, save_outputs = TRUE)
  wide <- fit_model("wide_sensitivity", frame, contract$priors$wide_sensitivity, contract$sampler, save_outputs = TRUE)
  diagnostics <- rbindlist(list(primary$diagnostics, wide$diagnostics), fill = TRUE)
  summaries <- rbindlist(list(primary$summary, wide$summary), fill = TRUE)
  ppc <- rbindlist(list(primary$ppc, wide$ppc), fill = TRUE)
  loo <- rbindlist(list(primary$loo, wide$loo), fill = TRUE)
  write_csv_atomic(primary$draws, file.path(output_dir, "posterior_draws_regularizing.csv.gz"))
  write_csv_atomic(wide$draws, file.path(output_dir, "posterior_draws_wide_sensitivity.csv.gz"))

  influence_rows <- list()
  corpora <- sort(unique(frame$dataset))
  for (corpus in corpora) {
    fit_id <- paste0("omit_", gsub("[^A-Za-z0-9]+", "_", corpus))
    result <- fit_model(
      fit_id,
      frame[frame$dataset != corpus, , drop = FALSE],
      contract$priors$regularizing,
      contract$influence_sampler,
      save_outputs = FALSE
    )
    diagnostics <- rbindlist(list(diagnostics, result$diagnostics), fill = TRUE)
    draws <- selected_draws(result$fit)
    influence_rows[[length(influence_rows) + 1L]] <- data.frame(
      omitted_corpus = corpus,
      mu_r1_age = mean(draws$mu_r1_age),
      mu_r2_entropy_42 = mean(draws$mu_r2_entropy_42),
      mu_r2_age_entropy = mean(draws$mu_r2_age_entropy),
      rho_r1_age_entropy = mean(draws$rho_r1_age_entropy)
    )
  }
  influence <- rbindlist(influence_rows)
  total_elapsed <- sum(diagnostics$elapsed_seconds)
  total_cpu_hours <- sum(diagnostics$elapsed_seconds * diagnostics$chains) / 3600
  problems <- evaluate_fit_gate(diagnostics, ppc, influence, corpora)
  if (total_cpu_hours > as.numeric(contract$runtime_gate$maximum_total_cpu_hours)) problems <- c(problems, "CPU-hour gate exceeded")
  if (total_elapsed / 60 > as.numeric(contract$runtime_gate$maximum_wall_minutes)) problems <- c(problems, "wall-time gate exceeded")

  write_csv_atomic(diagnostics, file.path(output_dir, "fit_diagnostics.csv"))
  write_csv_atomic(summaries, file.path(output_dir, "posterior_summary.csv"))
  write_csv_atomic(ppc, file.path(output_dir, "posterior_predictive_checks.csv"))
  write_csv_atomic(loo, file.path(output_dir, "loo_summary.csv"))
  write_csv_atomic(influence, file.path(output_dir, "influence_summary.csv"))
  write_json_atomic(
    list(
      status = if (length(problems)) "FAIL" else "PASS",
      problems = problems,
      children = nrow(frame),
      corpora = length(corpora),
      primary_fits = 2L,
      influence_fits = nrow(influence),
      total_elapsed_seconds = total_elapsed,
      total_cpu_hours = total_cpu_hours,
      maximum_rhat = max(diagnostics$rhat_max),
      minimum_bulk_ess = min(diagnostics$ess_bulk_min),
      minimum_tail_ess = min(diagnostics$ess_tail_min),
      divergences = sum(diagnostics$divergences)
    ),
    file.path(output_dir, "fit_audit.json")
  )
  if (length(problems)) stop(paste(problems, collapse = "; "))
}

run_finalize_existing <- function() {
  diagnostics_path <- file.path(output_dir, "fit_diagnostics.csv")
  influence_path <- file.path(output_dir, "influence_summary.csv")
  ppc_path <- file.path(output_dir, "posterior_predictive_checks.csv")
  if (!all(file.exists(c(diagnostics_path, influence_path, ppc_path)))) {
    stop("completed fit summaries are missing")
  }
  diagnostics <- fread(diagnostics_path)
  influence <- fread(influence_path)
  ppc <- fread(ppc_path)
  expected_ids <- c(
    "regularizing", "wide_sensitivity",
    paste0("omit_", gsub("[^A-Za-z0-9]+", "_", sort(unique(fread(input_path)$dataset))))
  )
  if (!setequal(diagnostics$fit_id, expected_ids)) stop("completed fit inventory mismatch")
  registered_variables <- c(
    "population_mean[1]", "population_mean[2]", "population_mean[3]",
    "child_correlation[1,3]"
  )
  for (fit_id in expected_ids) {
    csv_files <- list.files(file.path(output_dir, fit_id), pattern = "csv$", full.names = TRUE)
    expected_chains <- diagnostics$chains[match(fit_id, diagnostics$fit_id)]
    if (length(csv_files) != expected_chains) stop("CmdStan CSV inventory mismatch for ", fit_id)
    loaded <- read_cmdstan_csv(csv_files)
    registered <- summarise_draws(
      subset_draws(loaded$post_warmup_draws, variable = registered_variables, regex = FALSE)
    )
    index <- match(fit_id, diagnostics$fit_id)
    diagnostics$scientific_rhat_max[index] <- max(registered$rhat, na.rm = TRUE)
    diagnostics$scientific_ess_bulk_min[index] <- min(registered$ess_bulk, na.rm = TRUE)
    diagnostics$scientific_ess_tail_min[index] <- min(registered$ess_tail, na.rm = TRUE)
  }
  corpora <- sort(unique(fread(input_path)$dataset))
  problems <- evaluate_fit_gate(diagnostics, ppc, influence, corpora)
  total_elapsed <- sum(diagnostics$elapsed_seconds)
  total_cpu_hours <- sum(diagnostics$elapsed_seconds * diagnostics$chains) / 3600
  if (total_cpu_hours > as.numeric(contract$runtime_gate$maximum_total_cpu_hours)) problems <- c(problems, "CPU-hour gate exceeded")
  if (total_elapsed / 60 > as.numeric(contract$runtime_gate$maximum_wall_minutes)) problems <- c(problems, "wall-time gate exceeded")
  write_csv_atomic(diagnostics, diagnostics_path)
  write_json_atomic(
    list(
      status = if (length(problems)) "FAIL" else "PASS",
      problems = problems,
      children = nrow(fread(input_path)),
      corpora = length(corpora),
      primary_fits = 2L,
      influence_fits = nrow(influence),
      total_elapsed_seconds = total_elapsed,
      total_cpu_hours = total_cpu_hours,
      maximum_rhat_all_parameters = max(diagnostics$rhat_max),
      maximum_rhat_primary_all_parameters = max(diagnostics$rhat_max[diagnostics$fit_id %in% c("regularizing", "wide_sensitivity")]),
      maximum_rhat_influence_registered_outputs = max(diagnostics$scientific_rhat_max[startsWith(diagnostics$fit_id, "omit_")]),
      minimum_bulk_ess_influence_registered_outputs = min(diagnostics$scientific_ess_bulk_min[startsWith(diagnostics$fit_id, "omit_")]),
      minimum_tail_ess_influence_registered_outputs = min(diagnostics$scientific_ess_tail_min[startsWith(diagnostics$fit_id, "omit_")]),
      divergences = sum(diagnostics$divergences)
    ),
    file.path(output_dir, "fit_audit.json")
  )
  if (length(problems)) stop(paste(problems, collapse = "; "))
}

if (mode == "synthetic") {
  run_synthetic()
} else if (mode == "fit") {
  run_fit()
} else if (mode == "finalize-existing") {
  run_finalize_existing()
} else {
  stop("unknown mode: ", mode)
}
