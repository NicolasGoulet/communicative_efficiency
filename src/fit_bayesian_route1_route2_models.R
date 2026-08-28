#!/usr/bin/env Rscript

# CmdStan/brms execution backend for the Bayesian Route 1/Route 2 controller.
# This file never discovers samples, formulas, or priors from fitted outcomes;
# those choices arrive from the frozen Python/JSON contract.

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
root <- normalizePath(if (is.null(arguments$root)) getwd() else arguments$root, mustWork = TRUE)
local_library <- file.path(root, ".bayes-r-lib")
cmdstan_path <- file.path(root, ".cmdstan", "cmdstan-2.39.0")
.libPaths(c(local_library, .Library.site, .Library))

suppressPackageStartupMessages({
  library(brms)
  library(cmdstanr)
  library(data.table)
  library(jsonlite)
  library(posterior)
})

if (as.character(packageVersion("brms")) != "2.23.0") stop("brms pin mismatch")
if (as.character(packageVersion("cmdstanr")) != "0.9.0") stop("cmdstanr pin mismatch")
if (!dir.exists(cmdstan_path)) stop("missing pinned CmdStan: ", cmdstan_path)
cmdstanr::set_cmdstan_path(cmdstan_path)

output_dir <- normalizePath(
  required_argument(arguments, "output-dir"), mustWork = FALSE
)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
seed <- as.integer(if (is.null(arguments$seed)) 20260828L else arguments$seed)
chains <- as.integer(if (is.null(arguments$chains)) 2L else arguments$chains)
warmup <- as.integer(if (is.null(arguments$warmup)) 100L else arguments$warmup)
sampling <- as.integer(if (is.null(arguments$sampling)) 100L else arguments$sampling)
parallel_chains <- max(1L, min(chains, 4L))

write_json_atomic <- function(payload, path) {
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  write_json(payload, temporary, auto_unbox = TRUE, pretty = TRUE, digits = 16)
  if (!file.rename(temporary, path)) stop("could not publish ", path)
}

write_csv_atomic <- function(frame, path) {
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  fwrite(frame, temporary)
  if (!file.rename(temporary, path)) stop("could not publish ", path)
}

peak_rss_kb <- function() {
  status <- tryCatch(readLines("/proc/self/status", warn = FALSE), error = function(error) character())
  line <- status[startsWith(status, "VmHWM:")]
  if (!length(line)) return(NA_real_)
  as.numeric(sub("^VmHWM:\\s+([0-9]+).*", "\\1", line[[1]]))
}

cmdstan_diagnostics <- function(fit) {
  if (inherits(fit, "brmsfit")) {
    draws <- posterior::as_draws_array(fit)
    sampler <- rstan::get_sampler_params(fit$fit, inc_warmup = FALSE)
    divergences <- sum(vapply(sampler, function(chain) sum(chain[, "divergent__"]), numeric(1)))
    maximum_depth <- 12
    treedepth_saturated <- sum(vapply(sampler, function(chain) sum(chain[, "treedepth__"] >= maximum_depth), numeric(1)))
    bfmi <- vapply(sampler, function(chain) {
      energy <- chain[, "energy__"]
      mean(diff(energy)^2) / stats::var(energy)
    }, numeric(1))
  } else {
    diagnostic <- fit$diagnostic_summary()
    draws <- posterior::as_draws_array(fit$draws())
    divergences <- sum(diagnostic$num_divergent)
    treedepth_saturated <- sum(diagnostic$num_max_treedepth)
    bfmi <- if ("ebfmi" %in% names(diagnostic)) diagnostic$ebfmi else NA_real_
  }
  summary <- posterior::summarise_draws(draws)
  finite_rhat <- summary$rhat[is.finite(summary$rhat)]
  finite_bulk <- summary$ess_bulk[is.finite(summary$ess_bulk)]
  finite_tail <- summary$ess_tail[is.finite(summary$ess_tail)]
  list(
    rhat_max = if (length(finite_rhat)) max(finite_rhat) else NA_real_,
    ess_bulk_min = if (length(finite_bulk)) min(finite_bulk) else NA_real_,
    ess_tail_min = if (length(finite_tail)) min(finite_tail) else NA_real_,
    divergences = divergences,
    treedepth_saturated = treedepth_saturated,
    energy_bfmi_min = min(bfmi, na.rm = TRUE)
  )
}

brms_sample <- function(fit_id, formula, data, family, priors) {
  fit_dir <- file.path(output_dir, fit_id)
  # A real-pilot rerun must benchmark a fresh compile/sample. Loading a
  # pre-existing brms RDS makes elapsed time look like sampling took under a
  # second and can incorrectly authorize production. These directories are
  # disposable stage outputs; remove only the exact registered fit directory.
  if (dir.exists(fit_dir)) unlink(fit_dir, recursive = TRUE, force = TRUE)
  dir.create(fit_dir, recursive = TRUE, showWarnings = FALSE)
  started <- proc.time()[["elapsed"]]
  fit <- brm(
    formula = formula,
    data = data,
    family = family,
    prior = priors,
    backend = "cmdstanr",
    chains = chains,
    cores = parallel_chains,
    iter = warmup + sampling,
    warmup = warmup,
    seed = seed,
    refresh = 0,
    control = list(adapt_delta = 0.95, max_treedepth = 12),
    file = file.path(fit_dir, "fit"),
    file_refit = "always",
    save_pars = save_pars(all = TRUE)
  )
  elapsed <- proc.time()[["elapsed"]] - started
  diagnostics <- cmdstan_diagnostics(fit)
  ess_per_hour <- diagnostics$ess_bulk_min / (elapsed / 3600)
  list(
    fit = fit,
    record = c(
      list(
        fit_id = fit_id,
        fit_status = "PASS",
        elapsed_seconds = elapsed,
        rows = nrow(data),
        chains = chains,
        warmup = warmup,
        sampling = sampling,
        output_bytes = sum(file.info(list.files(fit_dir, recursive = TRUE, full.names = TRUE))$size, na.rm = TRUE)
        , peak_rss_kb = peak_rss_kb()
        , minimum_bulk_ess_per_hour = ess_per_hour
      ),
      diagnostics
    )
  )
}

direct_b5_sample <- function(fit_id, slope_frame, priors) {
  fit_dir <- file.path(output_dir, fit_id)
  # Avoid accumulating stale CmdStan CSVs across pilot reruns, which would
  # inflate the projected output size and blur the diagnostic provenance.
  if (dir.exists(fit_dir)) unlink(fit_dir, recursive = TRUE, force = TRUE)
  dir.create(fit_dir, recursive = TRUE, showWarnings = FALSE)
  corpora <- unique(slope_frame$dataset)
  estimation_cov <- lapply(seq_len(nrow(slope_frame)), function(index) {
    matrix(
      c(
        slope_frame$r1_se[index]^2,
        slope_frame$r1_r2_cov[index],
        slope_frame$r1_r2_cov[index],
        slope_frame$r2_se[index]^2
      ),
      nrow = 2L
    )
  })
  stan_data <- list(
    N = nrow(slope_frame),
    C = length(corpora),
    corpus_id = match(slope_frame$dataset, corpora),
    slope_hat = lapply(seq_len(nrow(slope_frame)), function(index) c(slope_frame$r1_slope[index], slope_frame$r2_slope[index])),
    estimation_cov = estimation_cov,
    coefficient_sd = priors$coefficient_sd,
    random_sd = priors$random_sd,
    lkj_eta = priors$lkj_eta
  )
  model <- cmdstan_model(file.path(root, "src", "stan", "b5_bivariate_measurement_error.stan"))
  started <- proc.time()[["elapsed"]]
  fit <- model$sample(
    data = stan_data,
    seed = seed,
    chains = chains,
    parallel_chains = parallel_chains,
    iter_warmup = warmup,
    iter_sampling = sampling,
    adapt_delta = 0.90,
    max_treedepth = 12,
    refresh = 0,
    output_dir = fit_dir
  )
  elapsed <- proc.time()[["elapsed"]] - started
  diagnostics <- cmdstan_diagnostics(fit)
  ess_per_hour <- diagnostics$ess_bulk_min / (elapsed / 3600)
  list(
    fit = fit,
    record = c(
      list(
        fit_id = fit_id,
        fit_status = "PASS",
        elapsed_seconds = elapsed,
        rows = nrow(slope_frame),
        chains = chains,
        warmup = warmup,
        sampling = sampling,
        output_bytes = sum(file.info(list.files(fit_dir, recursive = TRUE, full.names = TRUE))$size, na.rm = TRUE)
        , peak_rss_kb = peak_rss_kb()
        , minimum_bulk_ess_per_hour = ess_per_hour
      ),
      diagnostics
    )
  )
}

scaled_priors <- function(name = "skeptical") {
  values <- switch(
    name,
    weak = list(coefficient_sd = 0.75, random_sd = 0.75, lkj_eta = 2),
    skeptical = list(coefficient_sd = 0.35, random_sd = 0.40, lkj_eta = 4),
    wide = list(coefficient_sd = 1.50, random_sd = 1.50, lkj_eta = 1),
    stop("unknown prior set: ", name)
  )
  values
}

synthetic_data <- function() {
  set.seed(seed)
  n <- 480L
  child <- factor(sample(sprintf("child_%02d", 1:16), n, replace = TRUE))
  dataset <- factor(sample(sprintf("corpus_%02d", 1:4), n, replace = TRUE))
  age_z <- runif(n, -2, 2)
  word_z <- rnorm(n)
  condition <- factor(rep(c("k0", "k1", "k2", "k3"), length.out = n), levels = c("k0", "k1", "k2", "k3"))
  condition_index <- as.integer(condition)
  child_intercept <- rnorm(nlevels(child), 0, 0.45)
  child_age_slope <- rnorm(nlevels(child), 0, 0.10)
  child_entropy_slope <- rnorm(nlevels(child), 0, 0.08)
  corpus_intercept <- rnorm(nlevels(dataset), 0, 0.35)
  grouping_effect <- child_intercept[as.integer(child)] +
    child_age_slope[as.integer(child)] * age_z +
    corpus_intercept[as.integer(dataset)]
  context_offsets <- c(0, -2, -3, -4)
  age_slopes <- c(-0.20, -0.25, -0.30, -0.35)
  cell_se_bits <- runif(n, 0.05, 0.20)
  cell_mean_bits <- 32 + context_offsets[condition_index] + age_slopes[condition_index] * age_z + 0.4 * word_z + grouping_effect + rt(n, 7) * 0.7 + rnorm(n, 0, cell_se_bits)
  b1 <- data.frame(cell_mean_bits, cell_se_bits, condition, age_z, word_z, child_key = child, dataset)

  sigma <- exp(1.0 - 0.12 * age_z + 0.08 * word_z)
  k3_bits <- 25 - 0.35 * age_z + 0.45 * word_z + grouping_effect + rt(n, 7) * sigma
  b2 <- data.frame(k3_bits, age_z, word_z, child_key = child, dataset)

  entropy_z <- rnorm(n)
  context_words_z <- rnorm(n)
  log_mu <- 0.8 + 0.10 * age_z + 0.15 * entropy_z - 0.12 * age_z * entropy_z + 0.08 * context_words_z +
    0.25 * child_intercept[as.integer(child)] + child_entropy_slope[as.integer(child)] * entropy_z +
    0.20 * corpus_intercept[as.integer(dataset)]
  mu <- exp(log_mu)
  child_words <- rnbinom(n, mu = mu, size = 3)
  b3 <- data.frame(child_words, age_z, entropy_z, context_words_z, child_key = child, dataset)

  rank_mu <- plogis(-0.15 + 0.25 * age_z - 0.20 * entropy_z + 0.12 * age_z * entropy_z)
  rank_probability <- rbeta(n, rank_mu * 18, (1 - rank_mu) * 18)
  rank200 <- rbinom(n, 200, rank_probability)
  b4 <- transform(b3, rank200 = rank200)
  endpoint <- rbinom(n, 1, 0.22)
  upper <- rbinom(n, 1, 0.45)
  interior <- rbeta(n, pmax(rank_mu * 16, 0.1), pmax((1 - rank_mu) * 16, 0.1))
  b4$effort_percentile_in_qwen <- ifelse(endpoint == 1, upper, interior)

  n_child <- 28L
  b5_dataset <- rep(sprintf("corpus_%02d", 1:4), length.out = n_child)
  between <- matrix(c(0.12^2, -0.4 * 0.12 * 0.10, -0.4 * 0.12 * 0.10, 0.10^2), 2)
  latent <- MASS::mvrnorm(n_child, mu = c(-0.25, 0.10), Sigma = between)
  r1_se <- runif(n_child, 0.025, 0.055)
  r2_se <- runif(n_child, 0.020, 0.050)
  estimation_cor <- 0.25
  observed <- matrix(NA_real_, nrow = n_child, ncol = 2)
  covariances <- numeric(n_child)
  for (index in seq_len(n_child)) {
    covariance <- estimation_cor * r1_se[index] * r2_se[index]
    covariances[index] <- covariance
    observed[index, ] <- MASS::mvrnorm(1, mu = latent[index, ], Sigma = matrix(c(r1_se[index]^2, covariance, covariance, r2_se[index]^2), 2))
  }
  b5 <- data.frame(
    child_key = sprintf("child_%02d", seq_len(n_child)),
    dataset = b5_dataset,
    r1_slope = observed[, 1],
    r2_slope = observed[, 2],
    r1_se = r1_se,
    r2_se = r2_se,
    r1_r2_cov = covariances
  )
  list(B1 = b1, B2 = b2, B3 = b3, B4 = b4, B5 = b5)
}

fixed_effect_records <- function(fit, fit_id, dpar = NULL) {
  summary <- fixef(fit)
  distributional <- grepl("^(sigma|zoi|coi)_", rownames(summary))
  if (is.null(dpar)) {
    summary <- summary[!distributional, , drop = FALSE]
  } else {
    summary <- summary[startsWith(rownames(summary), paste0(dpar, "_")), , drop = FALSE]
  }
  data.frame(
    fit_id = fit_id,
    parameter = rownames(summary),
    dpar = if (is.null(dpar)) "mu" else dpar,
    estimate = summary[, "Estimate"],
    error = summary[, "Est.Error"],
    q025 = summary[, "Q2.5"],
    q975 = summary[, "Q97.5"],
    row.names = NULL
  )
}

recovery_checks <- function(parameter_records) {
  estimate <- function(fit_id, parameter) {
    selected <- parameter_records$fit_id == fit_id & parameter_records$parameter == parameter
    value <- parameter_records$estimate[selected]
    if (length(value) != 1L) stop("expected one estimate for ", fit_id, "/", parameter)
    as.numeric(value[[1]])
  }
  rows <- list()
  add <- function(family, check, observed, truth, tolerance) {
    rows[[length(rows) + 1L]] <<- data.frame(
      model_family = family,
      check = check,
      estimate = observed,
      truth = truth,
      absolute_error = abs(observed - truth),
      tolerance = tolerance,
      status = if (abs(observed - truth) <= tolerance) "PASS" else "FAIL"
    )
  }

  add("B1", "k1_context_offset", estimate("B1_synthetic", "conditionk1"), -2.0, 0.50)
  add("B1", "k2_context_offset", estimate("B1_synthetic", "conditionk2"), -3.0, 0.50)
  add("B1", "k3_context_offset", estimate("B1_synthetic", "conditionk3"), -4.0, 0.50)
  base_age <- estimate("B1_synthetic", "age_z")
  add("B1", "k0_age_slope", base_age, -0.20, 0.25)
  add("B1", "k1_age_slope", base_age + estimate("B1_synthetic", "conditionk1:age_z"), -0.25, 0.25)
  add("B1", "k2_age_slope", base_age + estimate("B1_synthetic", "conditionk2:age_z"), -0.30, 0.25)
  add("B1", "k3_age_slope", base_age + estimate("B1_synthetic", "conditionk3:age_z"), -0.35, 0.25)
  add("B2", "mean_age_slope", estimate("B2_synthetic", "age_z"), -0.35, 0.20)
  add("B2", "log_sigma_age_slope", estimate("B2_synthetic", "sigma_age_z"), -0.12, 0.10)
  add("B3", "count_age_slope", estimate("B3_synthetic", "age_z"), 0.10, 0.12)
  add("B3", "count_entropy_slope", estimate("B3_synthetic", "entropy_z"), 0.15, 0.12)
  add("B3", "count_interaction", estimate("B3_synthetic", "age_z:entropy_z"), -0.12, 0.12)
  add("B4", "beta_binomial_age", estimate("B4_beta_binomial_synthetic", "age_z"), 0.25, 0.12)
  add("B4", "beta_binomial_entropy", estimate("B4_beta_binomial_synthetic", "entropy_z"), -0.20, 0.12)
  add("B4", "zoib_endpoint_logit", estimate("B4_zoib_synthetic", "zoi_Intercept"), qlogis(0.22), 0.50)
  add("B4", "zoib_upper_endpoint_logit", estimate("B4_zoib_synthetic", "coi_Intercept"), qlogis(0.45), 0.60)
  add("B5", "population_mean_r1", estimate("B5_synthetic", "population_mean[1]"), -0.25, 0.10)
  add("B5", "population_mean_r2", estimate("B5_synthetic", "population_mean[2]"), 0.10, 0.10)
  add("B5", "between_child_correlation", estimate("B5_synthetic", "between_child_correlation"), -0.40, 0.25)
  rbindlist(rows)
}

run_synthetic_smoke <- function() {
  data <- synthetic_data()
  records <- list()
  parameters <- list()

  b1 <- brms_sample(
    "B1_synthetic",
    bf(
      cell_mean_bits | se(cell_se_bits, sigma = TRUE) ~
        condition * age_z + word_z +
        (1 + age_z | child_key) + (1 | dataset)
    ),
    data$B1,
    student(),
    c(
      prior(normal(30, 5), class = "Intercept"),
      prior(normal(0, 2), class = "b"),
      prior(student_t(3, 0, 2.5), class = "sd"),
      prior(lkj(2), class = "cor"),
      prior(exponential(1), class = "sigma"),
      prior(gamma(2, 0.1), class = "nu")
    )
  )
  records[[length(records) + 1L]] <- b1$record
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b1$fit, "B1_synthetic")

  b2 <- brms_sample(
    "B2_synthetic",
    bf(
      k3_bits ~ age_z + word_z + (1 + age_z | child_key) + (1 | dataset),
      sigma ~ age_z + word_z + (1 | child_key) + (1 | dataset)
    ),
    data$B2,
    student(),
    c(
      prior(normal(25, 10), class = "Intercept"),
      prior(normal(0, 0.75), class = "b"),
      prior(normal(1, 1), class = "Intercept", dpar = "sigma"),
      prior(normal(0, 0.4), class = "b", dpar = "sigma"),
      prior(student_t(3, 0, 2.5), class = "sd"),
      prior(lkj(2), class = "cor"),
      prior(gamma(2, 0.1), class = "nu")
    )
  )
  records[[length(records) + 1L]] <- b2$record
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b2$fit, "B2_synthetic")
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b2$fit, "B2_synthetic", "sigma")

  b3 <- brms_sample(
    "B3_synthetic",
    child_words ~ age_z * entropy_z + context_words_z +
      (1 + age_z + entropy_z | child_key) + (1 | dataset),
    data$B3,
    negbinomial(),
    c(
      prior(normal(0.8, 1), class = "Intercept"),
      prior(normal(0, 0.75), class = "b"),
      prior(student_t(3, 0, 1), class = "sd"),
      prior(lkj(2), class = "cor"),
      prior(gamma(2, 0.5), class = "shape")
    )
  )
  records[[length(records) + 1L]] <- b3$record
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b3$fit, "B3_synthetic")

  b4_beta_binomial <- brms_sample(
    "B4_beta_binomial_synthetic",
    rank200 | trials(200) ~ age_z * entropy_z + context_words_z +
      (1 + age_z + entropy_z | child_key) + (1 | dataset),
    data$B4,
    beta_binomial(),
    c(
      prior(normal(0, 1.5), class = "Intercept"),
      prior(normal(0, 0.75), class = "b"),
      prior(student_t(3, 0, 1), class = "sd"),
      prior(lkj(2), class = "cor"),
      prior(gamma(2, 0.1), class = "phi")
    )
  )
  records[[length(records) + 1L]] <- b4_beta_binomial$record
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b4_beta_binomial$fit, "B4_beta_binomial_synthetic")

  b4_zoib <- brms_sample(
    "B4_zoib_synthetic",
    bf(
      effort_percentile_in_qwen ~ age_z * entropy_z + context_words_z +
        (1 + age_z + entropy_z | child_key) + (1 | dataset),
      zoi ~ age_z + entropy_z + (1 | child_key) + (1 | dataset),
      coi ~ age_z + entropy_z + (1 | child_key) + (1 | dataset)
    ),
    data$B4,
    zero_one_inflated_beta(),
    c(
      prior(normal(0, 1.5), class = "Intercept"),
      prior(normal(0, 0.75), class = "b"),
      prior(normal(-1.3, 1), class = "Intercept", dpar = "zoi"),
      prior(normal(0, 0.75), class = "b", dpar = "zoi"),
      prior(normal(0, 1), class = "Intercept", dpar = "coi"),
      prior(normal(0, 0.75), class = "b", dpar = "coi"),
      prior(student_t(3, 0, 1), class = "sd"),
      prior(lkj(2), class = "cor"),
      prior(gamma(2, 0.1), class = "phi")
    )
  )
  records[[length(records) + 1L]] <- b4_zoib$record
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b4_zoib$fit, "B4_zoib_synthetic")
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b4_zoib$fit, "B4_zoib_synthetic", "zoi")
  parameters[[length(parameters) + 1L]] <- fixed_effect_records(b4_zoib$fit, "B4_zoib_synthetic", "coi")

  b5 <- direct_b5_sample("B5_synthetic", data$B5, scaled_priors("skeptical"))
  records[[length(records) + 1L]] <- b5$record
  b5_summary <- b5$fit$summary(c("population_mean", "child_sd", "between_child_correlation"))
  parameters[[length(parameters) + 1L]] <- data.frame(
    fit_id = "B5_synthetic",
    parameter = b5_summary$variable,
    dpar = "joint",
    estimate = b5_summary$mean,
    error = b5_summary$sd,
    q025 = b5_summary$q5,
    q975 = b5_summary$q95
  )

  fit_records <- rbindlist(lapply(records, as.data.frame), fill = TRUE)
  parameter_records <- rbindlist(parameters, fill = TRUE)
  recovery <- recovery_checks(parameter_records)
  required_fits <- c(
    "B1_synthetic", "B2_synthetic", "B3_synthetic",
    "B4_beta_binomial_synthetic", "B4_zoib_synthetic", "B5_synthetic"
  )
  problems <- character()
  if (!setequal(fit_records$fit_id, required_fits)) problems <- c(problems, "synthetic fit inventory mismatch")
  if (any(fit_records$fit_status != "PASS")) problems <- c(problems, "a synthetic fit failed")
  if (any(!is.finite(parameter_records$estimate))) problems <- c(problems, "non-finite posterior summary")
  if (any(fit_records$divergences > 0, na.rm = TRUE)) problems <- c(problems, "synthetic fit has divergences")
  if (any(fit_records$rhat_max > 1.15, na.rm = TRUE)) problems <- c(problems, "synthetic fit R-hat exceeds 1.15")
  if (any(fit_records$ess_bulk_min < 20, na.rm = TRUE) || any(fit_records$ess_tail_min < 20, na.rm = TRUE)) problems <- c(problems, "synthetic fit ESS below 20")
  treedepth_rate <- fit_records$treedepth_saturated / (fit_records$chains * fit_records$sampling)
  if (any(treedepth_rate > 0.05, na.rm = TRUE)) problems <- c(problems, "synthetic fit treedepth saturation exceeds 5%")
  if (any(recovery$status != "PASS")) problems <- c(problems, "posterior synthetic parameter recovery failed")

  write_csv_atomic(fit_records, file.path(output_dir, "fit_records.csv"))
  write_csv_atomic(parameter_records, file.path(output_dir, "parameter_recovery.csv"))
  write_csv_atomic(recovery, file.path(output_dir, "recovery_checks.csv"))
  write_json_atomic(
    list(
      status = if (length(problems)) "FAIL" else "PASS",
      problems = problems,
      seed = seed,
      brms = as.character(packageVersion("brms")),
      cmdstanr = as.character(packageVersion("cmdstanr")),
      cmdstan = cmdstan_version(),
      local_library = normalizePath(local_library),
      local_brms_path = normalizePath(find.package("brms")),
      fits = required_fits
    ),
    file.path(output_dir, "backend_smoke_audit.json")
  )
  if (length(problems)) stop(paste(problems, collapse = "; "))
}

run_real_pilot <- function() {
  input_dir <- normalizePath(required_argument(arguments, "input-dir"), mustWork = TRUE)
  prior_name <- if (is.null(arguments[["prior-set"]])) "skeptical" else arguments[["prior-set"]]
  prior_values <- scaled_priors(prior_name)
  coefficient_sd <- prior_values$coefficient_sd
  random_sd <- prior_values$random_sd
  lkj_eta <- prior_values$lkj_eta
  coefficient_prior <- set_prior(sprintf("normal(0, %.17g)", coefficient_sd), class = "b")
  smooth_prior <- set_prior(sprintf("normal(0, %.17g)", random_sd), class = "sds")
  random_effect_prior <- set_prior(sprintf("student_t(3, 0, %.17g)", random_sd), class = "sd")
  correlation_prior <- set_prior(sprintf("lkj(%.17g)", lkj_eta), class = "cor")

  b1_data <- fread(file.path(input_dir, "B1.csv"), data.table = FALSE)
  b2_data <- fread(file.path(input_dir, "B2.csv"), data.table = FALSE)
  b3_data <- fread(file.path(input_dir, "B3_B4.csv"), data.table = FALSE)
  b5_data <- fread(file.path(input_dir, "B5_slopes.csv"), data.table = FALSE)
  for (frame_name in c("b1_data", "b2_data", "b3_data")) {
    frame <- get(frame_name)
    frame$child_key <- factor(frame$child_key)
    frame$dataset <- factor(frame$dataset)
    assign(frame_name, frame)
  }
  b1_data$condition <- factor(b1_data$condition, levels = c("k0", "k1", "k2", "k3"))
  b1_data$word_count_top12 <- factor(b1_data$word_count_top12)
  b2_data$word_count_top12 <- factor(b2_data$word_count_top12)
  b1_center <- mean(b1_data$cell_mean_bits)
  b1_scale <- sd(b1_data$cell_mean_bits)
  b1_data$cell_mean_z <- (b1_data$cell_mean_bits - b1_center) / b1_scale
  b1_data$cell_se_z <- b1_data$cell_se_for_model / b1_scale
  b2_center <- mean(b2_data$k3_bits)
  b2_scale <- sd(b2_data$k3_bits)
  b2_data$k3_z <- (b2_data$k3_bits - b2_center) / b2_scale

  records <- list()
  formulas <- list()
  register <- function(fit_id, family, variant, formula_text, data_rows) {
    formulas[[length(formulas) + 1L]] <<- data.frame(
      fit_id = fit_id,
      model_family = family,
      variant = variant,
      age_shape = "low_rank_smooth",
      prior_set = prior_name,
      formula = formula_text,
      rows = data_rows
    )
  }

  b1_formula <- bf(
    cell_mean_z | se(cell_se_z, sigma = TRUE) ~
      0 + condition + s(age_z, by = condition, k = 5) +
      condition:word_count_top12 +
      (0 + condition + condition:age_z | child_key) +
      (0 + condition | dataset)
  )
  register(
    "B1_pilot", "B1", "paired_primary",
    "cell_mean_z | se(cell_se_z,sigma=TRUE) ~ 0+condition+s(age_z,by=condition,k=5)+condition:word_count_top12+(0+condition+condition:age_z|child_key)+(0+condition|dataset)",
    nrow(b1_data)
  )
  b1 <- brms_sample(
    "B1_pilot", b1_formula, b1_data, student(),
    c(
      coefficient_prior,
      smooth_prior,
      random_effect_prior,
      correlation_prior,
      prior(exponential(1), class = "sigma"),
      prior(gamma(2, 0.1), class = "nu")
    )
  )
  records[[length(records) + 1L]] <- b1$record

  b2_formula <- bf(
    k3_z ~ s(age_z, k = 5) + word_count_top12 +
      (1 + age_z | child_key) + (1 | dataset),
    sigma ~ age_z + word_count_top12 + (1 | child_key) + (1 | dataset)
  )
  register(
    "B2_pilot", "B2", "location_scale_primary",
    "bf(k3_z~s(age_z,k=5)+word_count_top12+(1+age_z|child_key)+(1|dataset),sigma~age_z+word_count_top12+(1|child_key)+(1|dataset))",
    nrow(b2_data)
  )
  b2 <- brms_sample(
    "B2_pilot", b2_formula, b2_data, student(),
    c(
      coefficient_prior,
      set_prior(sprintf("normal(0, %.17g)", coefficient_sd), class = "b", dpar = "sigma"),
      prior(normal(0, 1), class = "Intercept"),
      prior(normal(0, 0.5), class = "Intercept", dpar = "sigma"),
      smooth_prior,
      random_effect_prior,
      correlation_prior,
      prior(gamma(2, 0.1), class = "nu")
    )
  )
  records[[length(records) + 1L]] <- b2$record

  route2_formula <- child_words ~
    s(age_z, k = 5) + s(entropy_z, k = 5) +
    t2(age_z, entropy_z, k = c(5, 5)) +
    s(context_words_z, k = 5) +
    (1 + age_z + entropy_z | child_key) + (1 | dataset)
  register(
    "B3_primary_pilot", "B3", "raw_total_association_primary",
    "child_words~s(age_z,k=5)+s(entropy_z,k=5)+t2(age_z,entropy_z,k=c(5,5))+s(context_words_z,k=5)+(1+age_z+entropy_z|child_key)+(1|dataset)",
    nrow(b3_data)
  )
  b3_primary <- brms_sample(
    "B3_primary_pilot", route2_formula, b3_data, negbinomial(),
    c(
      coefficient_prior,
      smooth_prior,
      random_effect_prior,
      correlation_prior,
      prior(gamma(2, 0.5), class = "shape")
    )
  )
  records[[length(records) + 1L]] <- b3_primary$record

  b3_sensitivity_formula <- update(
    route2_formula,
    . ~ . + s(qwen_mean_words_z, k = 5)
  )
  register(
    "B3_qwen_adjusted_pilot", "B3", "qwen_expected_length_adjusted_sensitivity",
    "B3_primary+s(qwen_mean_words_z,k=5)", nrow(b3_data)
  )
  b3_sensitivity <- brms_sample(
    "B3_qwen_adjusted_pilot", b3_sensitivity_formula, b3_data, negbinomial(),
    c(
      coefficient_prior,
      smooth_prior,
      random_effect_prior,
      correlation_prior,
      prior(gamma(2, 0.5), class = "shape")
    )
  )
  records[[length(records) + 1L]] <- b3_sensitivity$record

  b4_formula <- update(route2_formula, rank200 | trials(200) ~ .)
  register(
    "B4_beta_binomial_pilot", "B4", "beta_binomial_primary",
    "rank200|trials(200)~B3_primary_predictors", nrow(b3_data)
  )
  b4_primary <- brms_sample(
    "B4_beta_binomial_pilot", b4_formula, b3_data, beta_binomial(),
    c(
      coefficient_prior,
      smooth_prior,
      random_effect_prior,
      correlation_prior,
      prior(gamma(2, 0.1), class = "phi")
    )
  )
  records[[length(records) + 1L]] <- b4_primary$record

  b4_zoib_formula <- bf(
    effort_percentile_in_qwen ~
      s(age_z, k = 5) + s(entropy_z, k = 5) +
      t2(age_z, entropy_z, k = c(5, 5)) +
      s(context_words_z, k = 5) +
      (1 + age_z + entropy_z | child_key) + (1 | dataset),
    zoi ~ age_z * entropy_z + (1 | child_key) + (1 | dataset),
    coi ~ age_z * entropy_z + (1 | child_key) + (1 | dataset)
  )
  register(
    "B4_zoib_pilot", "B4", "zoib_registered_sensitivity",
    "bf(percentile~B3_primary_predictors,zoi~age_z*entropy_z+(1|child_key)+(1|dataset),coi~age_z*entropy_z+(1|child_key)+(1|dataset))",
    nrow(b3_data)
  )
  b4_zoib <- brms_sample(
    "B4_zoib_pilot", b4_zoib_formula, b3_data, zero_one_inflated_beta(),
    c(
      coefficient_prior,
      set_prior(sprintf("normal(0, %.17g)", coefficient_sd), class = "b", dpar = "zoi"),
      set_prior(sprintf("normal(0, %.17g)", coefficient_sd), class = "b", dpar = "coi"),
      prior(normal(-1.3, 1), class = "Intercept", dpar = "zoi"),
      prior(normal(0, 1), class = "Intercept", dpar = "coi"),
      smooth_prior,
      random_effect_prior,
      correlation_prior,
      prior(gamma(2, 0.1), class = "phi")
    )
  )
  records[[length(records) + 1L]] <- b4_zoib$record

  register(
    "B5_pilot", "B5", "shared_bootstrap_measurement_error_primary",
    "slope_hat[2]~MVN(latent_child_slope[2],known_shared_bootstrap_cov); latent_child_slope~MVN(population+corpus,Sigma_between)",
    nrow(b5_data)
  )
  b5 <- direct_b5_sample("B5_pilot", b5_data, prior_values)
  records[[length(records) + 1L]] <- b5$record

  fit_records <- rbindlist(lapply(records, as.data.frame), fill = TRUE)
  formula_registry <- rbindlist(formulas, fill = TRUE)
  fit_records$b1_center_bits <- b1_center
  fit_records$b1_scale_bits <- b1_scale
  fit_records$b2_center_bits <- b2_center
  fit_records$b2_scale_bits <- b2_scale
  write_csv_atomic(fit_records, file.path(output_dir, "fit_records.csv"))
  write_csv_atomic(formula_registry, file.path(output_dir, "formula_registry.csv"))
  write_json_atomic(
    list(
      status = "PASS",
      fit_count = nrow(fit_records),
      prior_set = prior_name,
      chains = chains,
      warmup = warmup,
      sampling = sampling,
      local_brms_path = normalizePath(find.package("brms"))
    ),
    file.path(output_dir, "pilot_backend_audit.json")
  )
}

if (mode == "synthetic-smoke") {
  run_synthetic_smoke()
} else if (mode == "pilot") {
  run_real_pilot()
} else if (mode == "fit") {
  stop("mode fit is registered but its controller handoff is not yet implemented")
} else {
  stop("unknown --mode: ", mode)
}
