#!/usr/bin/env Rscript

# CmdStan backend for the three-coefficient bidirectional measurement-error model.

parse_cli <- function(arguments) {
  result <- list()
  index <- 1L
  while (index <= length(arguments)) {
    token <- arguments[[index]]
    if (!startsWith(token, "--")) stop("unexpected argument: ", token)
    key <- sub("^--", "", token)
    result[[key]] <- arguments[[index + 1L]]
    index <- index + 2L
  }
  result
}

required <- function(arguments, key) {
  value <- arguments[[key]]
  if (is.null(value) || identical(value, "")) stop("missing --", key)
  value
}

arguments <- parse_cli(commandArgs(trailingOnly = TRUE))
mode <- required(arguments, "mode")
root <- normalizePath(required(arguments, "root"), mustWork = TRUE)
contract_path <- normalizePath(required(arguments, "contract"), mustWork = TRUE)
input_path <- normalizePath(required(arguments, "input"), mustWork = TRUE)
output_dir <- normalizePath(required(arguments, "output-dir"), mustWork = FALSE)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

.libPaths(c(file.path(root, ".bayes-r-lib"), .Library.site, .Library))
suppressPackageStartupMessages({
  library(cmdstanr)
  library(data.table)
  library(jsonlite)
  library(MASS)
  library(posterior)
})
cmdstanr::set_cmdstan_path(file.path(root, ".cmdstan", "cmdstan-2.39.0"))
contract <- fromJSON(contract_path, simplifyVector = TRUE)
if (!identical(contract$status, "frozen_pre_fit")) stop("contract is not frozen")

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

covariance_for_row <- function(frame, index) {
  matrix(c(
    frame$cov_11[index], frame$cov_12[index], frame$cov_13[index],
    frame$cov_12[index], frame$cov_22[index], frame$cov_23[index],
    frame$cov_13[index], frame$cov_23[index], frame$cov_33[index]
  ), 3L, 3L, byrow = TRUE)
}

prior_for <- function(wide = FALSE) {
  bayes <- contract$bayesian
  if (wide) {
    list(
      population_sd = as.numeric(bayes$wide_population_prior_sd),
      child_sd_scale = as.numeric(bayes$wide_child_sd_prior_scale),
      corpus_sd_scale = as.numeric(bayes$wide_corpus_sd_prior_scale),
      lkj_eta = as.numeric(bayes$lkj_eta)
    )
  } else {
    list(
      population_sd = as.numeric(bayes$primary_population_prior_sd),
      child_sd_scale = as.numeric(bayes$child_sd_prior_scale),
      corpus_sd_scale = as.numeric(bayes$corpus_sd_prior_scale),
      lkj_eta = as.numeric(bayes$lkj_eta)
    )
  }
}

stan_data <- function(frame, prior) {
  corpora <- sort(unique(frame$dataset))
  list(
    N = nrow(frame), C = length(corpora), K = 3L,
    corpus_id = match(frame$dataset, corpora),
    coefficient_hat = lapply(seq_len(nrow(frame)), function(index) c(
      frame$adult_to_child_k3[index],
      frame$adult_to_child_effort[index],
      frame$child_to_adult_effort[index]
    )),
    estimation_cov = lapply(seq_len(nrow(frame)), function(index) covariance_for_row(frame, index)),
    population_prior_sd = prior$population_sd,
    child_sd_prior_scale = prior$child_sd_scale,
    corpus_sd_prior_scale = prior$corpus_sd_scale,
    lkj_eta = prior$lkj_eta
  )
}

sampler_for <- function(influence = FALSE) {
  source <- if (influence) contract$bayesian$influence_sampler else contract$bayesian$sampler
  list(
    chains = as.integer(source$chains),
    parallel_chains = as.integer(source$chains),
    warmup = as.integer(source$warmup),
    sampling = as.integer(source$sampling),
    adapt_delta = as.numeric(source$adapt_delta),
    max_treedepth = as.integer(source$max_treedepth)
  )
}

diagnostics_for_fit <- function(fit, fit_id, elapsed, sampler) {
  diagnostic <- fit$diagnostic_summary()
  summary <- fit$summary()
  registered_names <- c(
    "population_mean[1]", "population_mean[2]", "population_mean[3]",
    "child_correlation[1,2]", "child_correlation[1,3]", "child_correlation[2,3]"
  )
  registered <- summary[summary$variable %in% registered_names, ]
  finite_rhat <- summary$rhat[is.finite(summary$rhat)]
  finite_bulk <- summary$ess_bulk[is.finite(summary$ess_bulk)]
  finite_tail <- summary$ess_tail[is.finite(summary$ess_tail)]
  bfmi <- if ("ebfmi" %in% names(diagnostic)) diagnostic$ebfmi else NA_real_
  data.frame(
    fit_id = fit_id, elapsed_seconds = elapsed,
    chains = sampler$chains, warmup = sampler$warmup, sampling = sampler$sampling,
    rhat_max = max(finite_rhat), ess_bulk_min = min(finite_bulk), ess_tail_min = min(finite_tail),
    registered_rhat_max = max(registered$rhat, na.rm = TRUE),
    registered_ess_bulk_min = min(registered$ess_bulk, na.rm = TRUE),
    registered_ess_tail_min = min(registered$ess_tail, na.rm = TRUE),
    divergences = sum(diagnostic$num_divergent),
    treedepth_saturated = sum(diagnostic$num_max_treedepth),
    energy_bfmi_min = min(bfmi, na.rm = TRUE)
  )
}

selected_draws <- function(fit) {
  draws <- as_draws_df(fit$draws(c("population_mean", "child_sd", "corpus_sd", "child_correlation")))
  data.frame(
    mu_adult_to_child_k3 = draws[["population_mean[1]"]],
    mu_adult_to_child_effort = draws[["population_mean[2]"]],
    mu_child_to_adult_effort = draws[["population_mean[3]"]],
    rho_k3_child_effort = draws[["child_correlation[1,2]"]],
    rho_k3_adult_effort = draws[["child_correlation[1,3]"]],
    rho_reciprocal_effort = draws[["child_correlation[2,3]"]],
    child_sd_1 = draws[["child_sd[1]"]],
    child_sd_2 = draws[["child_sd[2]"]],
    child_sd_3 = draws[["child_sd[3]"]],
    corpus_sd_1 = draws[["corpus_sd[1]"]],
    corpus_sd_2 = draws[["corpus_sd[2]"]],
    corpus_sd_3 = draws[["corpus_sd[3]"]]
  )
}

summary_for_fit <- function(fit, fit_id) {
  variables <- c("population_mean", "child_sd", "corpus_sd", "child_correlation")
  summary <- fit$summary(variables)
  draws <- as_draws_matrix(fit$draws(variables))
  variable_names <- colnames(draws)
  order <- match(variable_names, summary$variable)
  data.frame(
    fit_id = fit_id, variable = variable_names, mean = colMeans(draws),
    sd = apply(draws, 2, sd), q025 = apply(draws, 2, quantile, probs = .025),
    q975 = apply(draws, 2, quantile, probs = .975),
    rhat = summary$rhat[order], ess_bulk = summary$ess_bulk[order], ess_tail = summary$ess_tail[order]
  )
}

ppc_for_fit <- function(fit, frame, fit_id) {
  draws <- as_draws_matrix(fit$draws("coefficient_rep"))
  observed <- list(frame$adult_to_child_k3, frame$adult_to_child_effort, frame$child_to_adult_effort)
  rows <- list()
  for (dimension in 1:3) {
    columns <- grep(paste0("^coefficient_rep\\[[0-9]+,", dimension, "\\]$"), colnames(draws))
    replicated <- draws[, columns, drop = FALSE]
    for (statistic in c("mean", "sd")) {
      values <- if (statistic == "mean") rowMeans(replicated) else apply(replicated, 1, sd)
      observed_value <- if (statistic == "mean") mean(observed[[dimension]]) else sd(observed[[dimension]])
      interval <- quantile(values, c(.005, .995))
      rows[[length(rows) + 1L]] <- data.frame(
        fit_id = fit_id, dimension = dimension, statistic = statistic,
        observed = observed_value, predictive_q005 = interval[[1]], predictive_q995 = interval[[2]],
        status = if (observed_value >= interval[[1]] && observed_value <= interval[[2]]) "PASS" else "FAIL"
      )
    }
  }
  rbindlist(rows)
}

model <- cmdstan_model(file.path(root, "src", "stan", "joint_adaptive_efficiency_measurement_error.stan"))

fit_model <- function(fit_id, frame, prior, sampler, save_outputs = TRUE) {
  fit_dir <- file.path(output_dir, fit_id)
  dir.create(fit_dir, recursive = TRUE, showWarnings = FALSE)
  started <- proc.time()[["elapsed"]]
  fit <- model$sample(
    data = stan_data(frame, prior),
    seed = as.integer(contract$bayesian$sampler$seed),
    chains = sampler$chains, parallel_chains = sampler$parallel_chains,
    iter_warmup = sampler$warmup, iter_sampling = sampler$sampling,
    adapt_delta = sampler$adapt_delta, max_treedepth = sampler$max_treedepth,
    refresh = 0, output_dir = fit_dir
  )
  elapsed <- proc.time()[["elapsed"]] - started
  list(
    fit = fit,
    diagnostics = diagnostics_for_fit(fit, fit_id, elapsed, sampler),
    draws = if (save_outputs) selected_draws(fit) else NULL,
    summary = if (save_outputs) summary_for_fit(fit, fit_id) else NULL,
    ppc = if (save_outputs) ppc_for_fit(fit, frame, fit_id) else NULL
  )
}

run_synthetic <- function() {
  set.seed(as.integer(contract$bayesian$sampler$seed))
  N <- 60L
  C <- 6L
  truth_mu <- c(-0.10, -0.08, -0.12)
  truth_sd <- c(.18, .15, .16)
  truth_cor <- matrix(c(1, .25, .10, .25, 1, .35, .10, .35, 1), 3, 3)
  between <- diag(truth_sd) %*% truth_cor %*% diag(truth_sd)
  corpus_id <- rep(seq_len(C), length.out = N)
  corpus_effect <- matrix(rnorm(C * 3, 0, .04), 3, C)
  latent <- mvrnorm(N, truth_mu, between) + t(corpus_effect[, corpus_id])
  covariance <- array(0, c(3, 3, N))
  observed <- matrix(NA_real_, N, 3)
  for (index in seq_len(N)) {
    standard_error <- runif(3, .025, .07)
    correlation <- matrix(c(1, .15, -.1, .15, 1, .2, -.1, .2, 1), 3, 3)
    covariance[, , index] <- diag(standard_error) %*% correlation %*% diag(standard_error)
    observed[index, ] <- mvrnorm(1, latent[index, ], covariance[, , index])
  }
  frame <- data.frame(
    child_key = sprintf("child_%03d", seq_len(N)), dataset = sprintf("corpus_%02d", corpus_id),
    adult_to_child_k3 = observed[, 1], adult_to_child_effort = observed[, 2], child_to_adult_effort = observed[, 3],
    cov_11 = covariance[1, 1, ], cov_12 = covariance[1, 2, ], cov_13 = covariance[1, 3, ],
    cov_22 = covariance[2, 2, ], cov_23 = covariance[2, 3, ], cov_33 = covariance[3, 3, ]
  )
  sampler <- list(chains = 4L, parallel_chains = 4L, warmup = 300L, sampling = 500L, adapt_delta = .99, max_treedepth = 12L)
  result <- fit_model("synthetic", frame, prior_for(FALSE), sampler, TRUE)
  summary <- result$summary[result$summary$variable %in% paste0("population_mean[", 1:3, "]"), ]
  summary$truth <- truth_mu[match(summary$variable, paste0("population_mean[", 1:3, "]"))]
  summary$recovered <- summary$truth >= summary$q025 & summary$truth <= summary$q975
  problems <- character()
  if (any(!summary$recovered)) problems <- c(problems, "synthetic population mean not recovered")
  if (result$diagnostics$divergences > 0 || result$diagnostics$treedepth_saturated > 0) problems <- c(problems, "synthetic sampler event")
  if (result$diagnostics$registered_rhat_max > 1.02) problems <- c(problems, "synthetic R-hat")
  write_csv_atomic(summary, file.path(output_dir, "synthetic_recovery.csv"))
  write_json_atomic(list(
    status = if (length(problems)) "FAIL" else "PASS", problems = problems,
    elapsed_seconds = result$diagnostics$elapsed_seconds,
    divergences = result$diagnostics$divergences,
    rhat_max = result$diagnostics$registered_rhat_max
  ), file.path(output_dir, "synthetic_audit.json"))
  if (length(problems)) stop(paste(problems, collapse = "; "))
}

run_fit <- function() {
  frame <- fread(input_path, data.table = FALSE)
  if (nrow(frame) != as.integer(contract$eligibility$expected_bayesian_children)) stop("child count mismatch")
  primary <- fit_model("regularizing", frame, prior_for(FALSE), sampler_for(FALSE), TRUE)
  wide <- fit_model("wide_sensitivity", frame, prior_for(TRUE), sampler_for(FALSE), TRUE)
  diagnostics <- rbindlist(list(primary$diagnostics, wide$diagnostics))
  summaries <- rbindlist(list(primary$summary, wide$summary))
  ppc <- rbindlist(list(primary$ppc, wide$ppc))
  write_csv_atomic(primary$draws, file.path(output_dir, "posterior_draws_regularizing.csv.gz"))
  write_csv_atomic(wide$draws, file.path(output_dir, "posterior_draws_wide_sensitivity.csv.gz"))
  influence <- list()
  for (corpus in sort(unique(frame$dataset))) {
    fit_id <- paste0("omit_", gsub("[^A-Za-z0-9]+", "_", corpus))
    result <- fit_model(fit_id, frame[frame$dataset != corpus, ], prior_for(FALSE), sampler_for(TRUE), FALSE)
    diagnostics <- rbindlist(list(diagnostics, result$diagnostics))
    draws <- selected_draws(result$fit)
    influence[[length(influence) + 1L]] <- data.frame(
      omitted_corpus = corpus,
      mu_adult_to_child_k3 = mean(draws$mu_adult_to_child_k3),
      mu_adult_to_child_effort = mean(draws$mu_adult_to_child_effort),
      mu_child_to_adult_effort = mean(draws$mu_child_to_adult_effort),
      rho_reciprocal_effort = mean(draws$rho_reciprocal_effort)
    )
  }
  influence <- rbindlist(influence)
  problems <- character()
  primary_diagnostics <- diagnostics[fit_id %in% c("regularizing", "wide_sensitivity")]
  influence_diagnostics <- diagnostics[startsWith(fit_id, "omit_")]
  if (any(primary_diagnostics$rhat_max > 1.01 | primary_diagnostics$ess_bulk_min < 400 | primary_diagnostics$ess_tail_min < 400)) problems <- c(problems, "primary all-parameter diagnostic gate")
  if (any(influence_diagnostics$registered_rhat_max > 1.02 | influence_diagnostics$registered_ess_bulk_min < 200 | influence_diagnostics$registered_ess_tail_min < 200)) problems <- c(problems, "influence registered-output diagnostic gate")
  if (any(diagnostics$divergences > 0 | diagnostics$treedepth_saturated > 0 | diagnostics$energy_bfmi_min < .3)) problems <- c(problems, "sampler event gate")
  if (any(ppc$status != "PASS")) problems <- c(problems, "posterior predictive check")
  cpu_hours <- sum(diagnostics$elapsed_seconds * diagnostics$chains) / 3600
  if (cpu_hours > as.numeric(contract$bayesian$maximum_total_cpu_hours)) problems <- c(problems, "CPU-hour gate")
  write_csv_atomic(diagnostics, file.path(output_dir, "fit_diagnostics.csv"))
  write_csv_atomic(summaries, file.path(output_dir, "posterior_summary.csv"))
  write_csv_atomic(ppc, file.path(output_dir, "posterior_predictive_checks.csv"))
  write_csv_atomic(influence, file.path(output_dir, "influence_summary.csv"))
  write_json_atomic(list(
    status = if (length(problems)) "FAIL" else "PASS", problems = problems,
    children = nrow(frame), corpora = length(unique(frame$dataset)), fits = nrow(diagnostics),
    total_elapsed_seconds = sum(diagnostics$elapsed_seconds), total_cpu_hours = cpu_hours,
    maximum_rhat = max(primary_diagnostics$rhat_max),
    minimum_bulk_ess = min(primary_diagnostics$ess_bulk_min),
    minimum_tail_ess = min(primary_diagnostics$ess_tail_min),
    divergences = sum(diagnostics$divergences), treedepth_saturated = sum(diagnostics$treedepth_saturated)
  ), file.path(output_dir, "fit_audit.json"))
  if (length(problems)) stop(paste(problems, collapse = "; "))
}

run_repair <- function() {
  frame <- fread(input_path, data.table = FALSE)
  diagnostics_path <- file.path(output_dir, "fit_diagnostics.csv")
  summary_path <- file.path(output_dir, "posterior_summary.csv")
  ppc_path <- file.path(output_dir, "posterior_predictive_checks.csv")
  influence_path <- file.path(output_dir, "influence_summary.csv")
  if (!all(file.exists(c(diagnostics_path, summary_path, ppc_path, influence_path)))) {
    stop("first-pass Bayesian artifacts are missing")
  }
  diagnostics <- fread(diagnostics_path)
  summaries <- fread(summary_path)
  ppc <- fread(ppc_path)
  influence <- fread(influence_path)
  previous_cpu_hours <- sum(diagnostics$elapsed_seconds * diagnostics$chains) / 3600
  repair_diagnostics <- list()

  primary_sampler <- list(
    chains = 4L, parallel_chains = 4L, warmup = 1500L, sampling = 1500L,
    adapt_delta = .995, max_treedepth = 13L
  )
  wide <- fit_model("repair_wide_sensitivity", frame, prior_for(TRUE), primary_sampler, TRUE)
  wide$diagnostics$fit_id <- "wide_sensitivity"
  wide$summary$fit_id <- "wide_sensitivity"
  wide$ppc$fit_id <- "wide_sensitivity"
  diagnostics <- rbindlist(list(
    diagnostics[fit_id != "wide_sensitivity"], wide$diagnostics
  ))
  summaries <- rbindlist(list(
    summaries[fit_id != "wide_sensitivity"], wide$summary
  ))
  ppc <- rbindlist(list(ppc[fit_id != "wide_sensitivity"], wide$ppc))
  write_csv_atomic(wide$draws, file.path(output_dir, "posterior_draws_wide_sensitivity.csv.gz"))
  repair_diagnostics[[length(repair_diagnostics) + 1L]] <- wide$diagnostics

  failed_ids <- diagnostics[
    startsWith(fit_id, "omit_") & (
      registered_rhat_max > 1.02 |
      registered_ess_bulk_min < 200 |
      registered_ess_tail_min < 200
    ), fit_id
  ]
  influence_sampler <- list(
    chains = 4L, parallel_chains = 4L, warmup = 750L, sampling = 1000L,
    adapt_delta = .995, max_treedepth = 13L
  )
  corpora <- sort(unique(frame$dataset))
  for (fit_id in failed_ids) {
    corpus_ids <- paste0("omit_", gsub("[^A-Za-z0-9]+", "_", corpora))
    corpus <- corpora[match(fit_id, corpus_ids)]
    result <- fit_model(paste0("repair_", fit_id), frame[frame$dataset != corpus, ], prior_for(FALSE), influence_sampler, FALSE)
    result$diagnostics$fit_id <- fit_id
    diagnostics <- rbindlist(list(diagnostics[fit_id != result$diagnostics$fit_id], result$diagnostics))
    draws <- selected_draws(result$fit)
    influence[omitted_corpus == corpus, `:=`(
      mu_adult_to_child_k3 = mean(draws$mu_adult_to_child_k3),
      mu_adult_to_child_effort = mean(draws$mu_adult_to_child_effort),
      mu_child_to_adult_effort = mean(draws$mu_child_to_adult_effort),
      rho_reciprocal_effort = mean(draws$rho_reciprocal_effort)
    )]
    repair_diagnostics[[length(repair_diagnostics) + 1L]] <- result$diagnostics
  }
  repair_diagnostics <- rbindlist(repair_diagnostics)
  problems <- character()
  primary_diagnostics <- diagnostics[fit_id %in% c("regularizing", "wide_sensitivity")]
  influence_diagnostics <- diagnostics[startsWith(fit_id, "omit_")]
  if (any(primary_diagnostics$rhat_max > 1.01 | primary_diagnostics$ess_bulk_min < 400 | primary_diagnostics$ess_tail_min < 400)) problems <- c(problems, "primary all-parameter diagnostic gate")
  if (any(influence_diagnostics$registered_rhat_max > 1.02 | influence_diagnostics$registered_ess_bulk_min < 200 | influence_diagnostics$registered_ess_tail_min < 200)) problems <- c(problems, "influence registered-output diagnostic gate")
  if (any(diagnostics$divergences > 0 | diagnostics$treedepth_saturated > 0 | diagnostics$energy_bfmi_min < .3)) problems <- c(problems, "sampler event gate")
  if (any(ppc$status != "PASS")) problems <- c(problems, "posterior predictive check")
  repair_cpu_hours <- sum(repair_diagnostics$elapsed_seconds * repair_diagnostics$chains) / 3600
  total_cpu_hours <- previous_cpu_hours + repair_cpu_hours
  if (total_cpu_hours > as.numeric(contract$bayesian$maximum_total_cpu_hours)) problems <- c(problems, "CPU-hour gate")
  write_csv_atomic(diagnostics, diagnostics_path)
  write_csv_atomic(summaries, summary_path)
  write_csv_atomic(ppc, ppc_path)
  write_csv_atomic(influence, influence_path)
  write_csv_atomic(repair_diagnostics, file.path(output_dir, "repair_diagnostics.csv"))
  write_json_atomic(list(
    status = if (length(problems)) "FAIL" else "PASS", problems = problems,
    children = nrow(frame), corpora = length(corpora), fits = nrow(diagnostics),
    repaired_fits = nrow(repair_diagnostics), original_cpu_hours = previous_cpu_hours,
    repair_cpu_hours = repair_cpu_hours, total_cpu_hours = total_cpu_hours,
    maximum_rhat = max(primary_diagnostics$rhat_max),
    minimum_bulk_ess = min(primary_diagnostics$ess_bulk_min),
    minimum_tail_ess = min(primary_diagnostics$ess_tail_min),
    divergences = sum(diagnostics$divergences), treedepth_saturated = sum(diagnostics$treedepth_saturated)
  ), file.path(output_dir, "fit_audit.json"))
  if (length(problems)) stop(paste(problems, collapse = "; "))
}

if (mode == "synthetic") {
  run_synthetic()
} else if (mode == "fit") {
  run_fit()
} else if (mode == "repair") {
  run_repair()
} else {
  stop("unknown mode")
}
