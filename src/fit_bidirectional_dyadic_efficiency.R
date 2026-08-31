#!/usr/bin/env Rscript

# Focused GAMM backend for the registered bidirectional F1-F3 inventory.

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

.libPaths(c(file.path(root, ".bayes-r-lib"), .Library.site, .Library))
suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
  library(MASS)
  library(mgcv)
})

contract <- fromJSON(contract_path, simplifyVector = FALSE)
if (!identical(contract$status, "frozen_pre_fit")) stop("contract is not frozen")
if (length(contract$estimands) != 3L) stop("F1-F3 inventory mismatch")

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

most_common <- function(values) {
  counts <- sort(table(values), decreasing = TRUE)
  names(counts)[[1L]]
}

prepare_data <- function(frame) {
  factor_columns <- c(
    "dataset", "child_key", "child_session_key", "sample_group",
    "a0_question_type", "c_question_type", "c_word_top12"
  )
  for (column in factor_columns) frame[[column]] <- factor(frame[[column]])
  integer_columns <- c(
    "exact_imitation_candidate", "child_backchannel_candidate",
    "session_reading_candidate", "session_routine_candidate"
  )
  for (column in integer_columns) frame[[column]] <- as.integer(frame[[column]])
  frame
}

scope_filter <- function(frame, scope) {
  result <- if (scope == "all79_descriptive") {
    copy(frame)
  } else {
    frame[as.character(sample_group) == scope]
  }
  droplevels(result)
}

model_specs <- function(smoke = FALSE, parent = FALSE) {
  if (parent) {
    inventory <- data.table(
      family_id = c("F1", "F2", "F3"),
      scope = "all79_descriptive",
      variant = "k3",
      parent_filter = c("a0", "a0", "a1")
    )
    inventory[, model_id := paste(family_id, "k3", "parent_sensitivity", sep = "__")]
    return(inventory)
  }
  primary <- CJ(
    family_id = c("F1", "F2", "F3"),
    scope = c("pbm_discovery", "non_pbm_confirmation", "all79_descriptive"),
    variant = "k3",
    sorted = FALSE
  )
  decomposition <- CJ(
    family_id = c("F1", "F2", "F3"),
    scope = "all79_descriptive",
    variant = c("k0", "support"),
    sorted = FALSE
  )
  inventory <- rbindlist(list(primary, decomposition))
  inventory[, model_id := paste(family_id, variant, scope, sep = "__")]
  inventory[, parent_filter := ""]
  if (smoke) inventory <- inventory[model_id %in% c(
    "F1__k3__pbm_discovery", "F3__k3__pbm_discovery"
  )]
  inventory
}

configure_model_frame <- function(frame, family_id, variant) {
  prefix <- if (family_id %in% c("F1", "F2")) "a0" else "c"
  within_names <- list(
    k3 = paste0(prefix, "_k3_within_z"),
    k0 = paste0(prefix, "_k0_within_z"),
    support = paste0(prefix, "_support_within_z")
  )
  child_mean_names <- list(
    k3 = paste0(prefix, "_k3_child_mean"),
    k0 = paste0(prefix, "_k0_child_mean"),
    support = paste0(prefix, "_support_child_mean")
  )
  frame[, predictor_within_z := get(within_names[[variant]])]
  frame[, predictor_child_mean := get(child_mean_names[[variant]])]
  frame[, a0_control_within_z := get(paste0("a0_", variant, "_within_z"))]
  if (family_id == "F1") {
    outcome <- list(k3 = "c_k3_bits", k0 = "c_k0_bits", support = "c_context_support_bits")[[variant]]
    frame[, score_outcome := get(outcome)]
  }
  frame
}

family_for <- function(family_id) {
  if (family_id == "F1") scat(link = "identity") else nb(link = "log")
}

registered_formula <- function(family_id) {
  as.formula(contract$frequentist_formulas[[family_id]])
}

random_terms <- c("s(dataset)", "s(child_key)", "s(child_session_key)")

reference_newdata <- function(frame, ages) {
  data.frame(
    age_z = (ages - 42) / 6,
    predictor_within_z = 0,
    predictor_child_mean = median(frame$predictor_child_mean, na.rm = TRUE),
    a0_control_within_z = 0,
    c_word_top12 = factor("2", levels = levels(frame$c_word_top12)),
    log1p_a0_words = median(frame$log1p_a0_words),
    log1p_c_words = median(frame$log1p_c_words),
    a0_question_type = factor(most_common(frame$a0_question_type), levels = levels(frame$a0_question_type)),
    c_question_type = factor(most_common(frame$c_question_type), levels = levels(frame$c_question_type)),
    exact_imitation_candidate = 0L,
    child_backchannel_candidate = 0L,
    session_reading_candidate = 0L,
    session_routine_candidate = 0L,
    dataset = factor(levels(frame$dataset)[[1L]], levels = levels(frame$dataset)),
    child_key = factor(levels(frame$child_key)[[1L]], levels = levels(frame$child_key)),
    child_session_key = factor(levels(frame$child_session_key)[[1L]], levels = levels(frame$child_session_key))
  )
}

coupling_curve <- function(fit, frame, ages, model_id, family_id, variant, scope) {
  base <- reference_newdata(frame, ages)
  delta <- 0.01
  plus <- copy(base)
  minus <- copy(base)
  plus$predictor_within_z <- delta / 2
  minus$predictor_within_z <- -delta / 2
  x_plus <- predict(fit, newdata = plus, type = "lpmatrix", exclude = random_terms)
  x_minus <- predict(fit, newdata = minus, type = "lpmatrix", exclude = random_terms)
  derivative <- (x_plus - x_minus) / delta
  active <- which(colSums(abs(derivative)) > 1e-12)
  derivative <- derivative[, active, drop = FALSE]
  covariance <- fit$Vp[active, active, drop = FALSE]
  estimate <- drop(derivative %*% coef(fit)[active])
  standard_error <- sqrt(pmax(0, rowSums((derivative %*% covariance) * derivative)))
  set.seed(as.integer(contract$validation$whole_child_bootstrap_seed))
  draws <- mvrnorm(2000, coef(fit)[active], covariance)
  curve_draws <- derivative %*% t(draws)
  standardized <- sweep(curve_draws, 1, estimate, "-")
  standardized <- sweep(standardized, 1, standard_error, "/")
  critical <- unname(quantile(apply(abs(standardized), 2, max), 0.95, na.rm = TRUE))
  lower <- estimate - critical * standard_error
  upper <- estimate + critical * standard_error
  if (family_id != "F1") {
    display_estimate <- exp(estimate)
    display_lower <- exp(lower)
    display_upper <- exp(upper)
    unit <- "incidence_rate_ratio_per_within_sd"
  } else {
    display_estimate <- estimate
    display_lower <- lower
    display_upper <- upper
    unit <- "outcome_bits_per_within_sd"
  }
  data.table(
    model_id = model_id, family_id = family_id, variant = variant, scope = scope,
    age_months = ages, link_slope = estimate, link_se = standard_error,
    simultaneous_critical = critical, simultaneous_lower_link = lower,
    simultaneous_upper_link = upper, estimate = display_estimate,
    simultaneous_lower = display_lower, simultaneous_upper = display_upper,
    unit = unit,
    simultaneous_excludes_null = if (family_id == "F1") lower > 0 | upper < 0 else display_lower > 1 | display_upper < 1
  )
}

fit_one <- function(frame, specification, smoke = FALSE) {
  family_id <- specification$family_id
  scope <- specification$scope
  variant <- specification$variant
  model_id <- specification$model_id
  model_frame <- scope_filter(frame, scope)
  parent_filter <- specification$parent_filter
  if (!is.null(parent_filter) && !is.na(parent_filter) && parent_filter == "a0") {
    model_frame <- model_frame[a0_parent_valid == TRUE]
  } else if (!is.null(parent_filter) && !is.na(parent_filter) && parent_filter == "a1") {
    model_frame <- model_frame[a1_parent_valid == TRUE]
  }
  model_frame <- configure_model_frame(model_frame, family_id, variant)
  if (smoke && nrow(model_frame) > 30000L) {
    indices <- unique(round(seq(1, nrow(model_frame), length.out = 30000L)))
    model_frame <- droplevels(model_frame[indices])
  }
  started <- proc.time()[["elapsed"]]
  fit <- bam(
    registered_formula(family_id), data = model_frame,
    family = family_for(family_id), method = "fREML", discrete = TRUE,
    nthreads = 4L, gc.level = 1L
  )
  elapsed <- proc.time()[["elapsed"]] - started
  if (!isTRUE(fit$converged)) stop("model did not converge: ", model_id)
  summary_fit <- summary(fit)
  ages <- as.numeric(unlist(contract$registered_age_grids_months[[scope]]))
  curve <- coupling_curve(fit, model_frame, ages, model_id, family_id, variant, scope)
  smooth <- as.data.table(summary_fit$s.table, keep.rownames = "term")
  smooth[, `:=`(model_id = model_id, family_id = family_id, variant = variant, scope = scope)]
  setcolorder(smooth, c("model_id", "family_id", "variant", "scope", "term"))
  inventory <- data.table(
    model_id = model_id, family_id = family_id, variant = variant, scope = scope,
    rows = nrow(model_frame), children = uniqueN(model_frame$child_key),
    sessions = uniqueN(model_frame$child_session_key), elapsed_seconds = elapsed,
    converged = isTRUE(fit$converged), rank = fit$rank,
    coefficients = length(coef(fit)), deviance_explained = summary_fit$dev.expl,
    scale = summary_fit$scale, negative_binomial_theta = if (family_id == "F1") NA_real_ else fit$family$getTheta(TRUE),
    registered_formula = paste(deparse(registered_formula(family_id)), collapse = " ")
  )
  list(inventory = inventory, curve = curve, smooth = smooth)
}

frame <- fread(cmd = paste("gzip -dc", shQuote(input_path)))
parent <- identical(mode, "parent")
if (parent) {
  parent_sidecar <- required_argument(arguments, "parent-sidecar")
  roles <- fread(parent_sidecar, select = c("response_pair_id", "a0_parent_valid", "a1_parent_valid"))
  frame <- merge(frame, roles, by = "response_pair_id", all.x = TRUE, sort = FALSE)
  if (anyNA(frame$a0_parent_valid) || anyNA(frame$a1_parent_valid)) stop("parent sidecar join is incomplete")
}
frame <- prepare_data(frame)
expected_rows <- as.integer(contract$expected$strict_rows)
if (nrow(frame) != expected_rows) stop("model input row mismatch")
smoke <- identical(mode, "smoke")
if (!smoke && !identical(mode, "full") && !parent) stop("unknown mode: ", mode)
specifications <- model_specs(smoke, parent)
results <- vector("list", nrow(specifications))
for (index in seq_len(nrow(specifications))) {
  message("fitting ", specifications$model_id[[index]])
  results[[index]] <- fit_one(frame, specifications[index], smoke = smoke)
}
inventory <- rbindlist(lapply(results, `[[`, "inventory"), fill = TRUE)
curves <- rbindlist(lapply(results, `[[`, "curve"), fill = TRUE)
smooths <- rbindlist(lapply(results, `[[`, "smooth"), fill = TRUE)
write_csv_atomic(inventory, file.path(output_dir, "model_inventory.csv"))
write_csv_atomic(curves, file.path(output_dir, "coupling_curves.csv"))
write_csv_atomic(smooths, file.path(output_dir, "smooth_term_tests.csv"))
expected_models <- if (smoke) 2L else if (parent) 3L else 15L
problems <- character()
if (nrow(inventory) != expected_models) problems <- c(problems, "model inventory mismatch")
if (any(!inventory$converged)) problems <- c(problems, "nonconverged model")
if (any(!is.finite(curves$link_slope)) || any(!is.finite(curves$link_se))) problems <- c(problems, "non-finite coupling curve")
write_json_atomic(
  list(
    status = if (length(problems)) "FAIL" else "PASS",
    mode = mode,
    models = nrow(inventory),
    total_elapsed_seconds = sum(inventory$elapsed_seconds),
    maximum_model_elapsed_seconds = max(inventory$elapsed_seconds),
    maximum_coefficients = max(inventory$coefficients),
    curve_rows = nrow(curves),
    problems = problems
  ),
  file.path(output_dir, "fit_audit.json")
)
if (length(problems)) stop(paste(problems, collapse = "; "))
