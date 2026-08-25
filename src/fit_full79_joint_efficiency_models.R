#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(mgcv)
  library(jsonlite)
})

parse_args <- function(values) {
  result <- list()
  i <- 1
  while (i <= length(values)) {
    key <- sub("^--", "", values[[i]])
    if (i == length(values)) stop(paste("missing value for", values[[i]]))
    result[[key]] <- values[[i + 1]]
    i <- i + 2
  }
  result
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
if (is.null(args$input) || is.null(args$output)) {
  stop("usage: fit_full79_joint_efficiency_models.R --input rows.csv.gz --output DIR [--threads 4]")
}
input_path <- normalizePath(args$input, mustWork = TRUE)
output_dir <- normalizePath(args$output, mustWork = FALSE)
threads <- if (is.null(args$threads)) 4L else as.integer(args$threads)
analysis_scope <- if (is.null(args$scope)) "all79" else args$scope
model_set <- if (is.null(args$`model-set`)) "all" else args$`model-set`
valid_scopes <- c("all79", "pbm_discovery", "non_pbm_confirmation")
if (!analysis_scope %in% valid_scopes) stop(paste("invalid scope", analysis_scope))
if (!model_set %in% c("all", "core")) stop(paste("invalid model set", model_set))
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(output_dir, "rds"), recursive = TRUE, showWarnings = FALSE)

sha256_file <- function(path) {
  output <- system2("sha256sum", path, stdout = TRUE)
  strsplit(output[[1]], "[[:space:]]+")[[1]][[1]]
}

file_record <- function(path) {
  path <- normalizePath(path, mustWork = TRUE)
  list(path = path, sha256 = sha256_file(path), bytes = unname(file.info(path)$size))
}

write_csv_atomic <- function(frame, path, gzip = FALSE) {
  temporary <- paste0(path, ".tmp.", Sys.getpid())
  if (gzip) {
    connection <- gzfile(temporary, open = "wt", compression = 6)
    write.csv(frame, connection, row.names = FALSE, na = "")
    close(connection)
  } else {
    write.csv(frame, temporary, row.names = FALSE, na = "")
  }
  invisible(file.rename(temporary, path))
}

message("[R models] reading ", input_path)
connection <- gzfile(input_path, open = "rt")
data <- read.csv(connection, stringsAsFactors = FALSE, check.names = FALSE)
close(connection)

pbm_corpora <- c("Brown", "Manchester", "Providence")
if (analysis_scope == "pbm_discovery") {
  data <- data[data$dataset %in% pbm_corpora, , drop = FALSE]
} else if (analysis_scope == "non_pbm_confirmation") {
  data <- data[!data$dataset %in% pbm_corpora, , drop = FALSE]
}
if (!nrow(data)) stop(paste("scope has no rows:", analysis_scope))

required <- c(
  "utterance_id", "dataset", "child_key", "age_months", "child_words",
  "child_k3_sum_bits", "response_entropy_bits", "context_word_count",
  "qwen_mean_word_count", "effort_percentile_open", "exact_length_support",
  "child_minus_exact_length_qwen_median_k3", "raw_nondominated"
)
missing <- setdiff(required, names(data))
if (length(missing)) stop(paste("missing model columns:", paste(missing, collapse = ", ")))

data$child_key <- factor(data$child_key)
data$dataset <- factor(data$dataset)
data$age_z <- as.numeric(scale(data$age_months))
data$entropy_z <- as.numeric(scale(data$response_entropy_bits))
data$effort_percentile_open <- pmin(pmax(data$effort_percentile_open, 1e-5), 1 - 1e-5)
data$exact_length_k3_percentile_open <- pmin(
  pmax(data$exact_length_k3_percentile_open, 1e-5), 1 - 1e-5
)

random_terms <- paste(
  "s(child_key, bs='re')",
  "s(child_key, age_z, bs='re')",
  "s(child_key, entropy_z, bs='re')",
  "s(dataset, bs='re')",
  sep = " + "
)

length_base <- paste(
  "s(age_months, k=8, bs='cr')",
  "s(response_entropy_bits, k=8, bs='cr')",
  "ti(age_months, response_entropy_bits, k=c(6,6), bs=c('cr','cr'))",
  "s(context_word_count, k=8, bs='cr')",
  random_terms,
  sep = " + "
)

information_base <- paste(
  "s(age_months, k=8, bs='cr')",
  "s(child_words, k=12, bs='cr')",
  "ti(age_months, child_words, k=c(6,8), bs=c('cr','cr'))",
  "s(response_entropy_bits, k=8, bs='cr')",
  "s(context_word_count, k=8, bs='cr')",
  random_terms,
  sep = " + "
)

specs <- list(
  list(
    id = "m1_length_primary",
    label = "Raw child effort: nonlinear negative-binomial GAMM",
    outcome = "child_words",
    family_name = "negative_binomial",
    family = nb(link = "log"),
    formula = paste("child_words ~", length_base),
    subset = quote(is.finite(child_words) & child_words > 0),
    grid = "age_entropy"
  ),
  list(
    id = "m2_length_qwen_reference",
    label = "Effort sensitivity with generated expected length",
    outcome = "child_words",
    family_name = "negative_binomial",
    family = nb(link = "log"),
    formula = paste("child_words ~", length_base, "+ s(qwen_mean_word_count, k=8, bs='cr')"),
    subset = quote(is.finite(child_words) & child_words > 0 & is.finite(qwen_mean_word_count)),
    grid = "age_entropy_reference"
  ),
  list(
    id = "m3_information_k3_total",
    label = "Contextual total surprisal at adaptive effort",
    outcome = "child_k3_sum_bits",
    family_name = "scaled_t",
    family = scat(link = "identity"),
    formula = paste("child_k3_sum_bits ~", information_base),
    subset = quote(is.finite(child_k3_sum_bits)),
    grid = "age_length"
  ),
  list(
    id = "m3b_information_k3_per_token",
    label = "Contextual surprisal per model token sensitivity",
    outcome = "child_k3_bits_per_token",
    family_name = "scaled_t",
    family = scat(link = "identity"),
    formula = paste("child_k3_bits_per_token ~", information_base),
    subset = quote(is.finite(child_k3_bits_per_token)),
    grid = "age_length"
  ),
  list(
    id = "m3c_information_k0_total",
    label = "Unconditional total surprisal sensitivity",
    outcome = "child_k0_sum_bits",
    family_name = "scaled_t",
    family = scat(link = "identity"),
    formula = paste("child_k0_sum_bits ~", information_base),
    subset = quote(is.finite(child_k0_sum_bits)),
    grid = "age_length"
  ),
  list(
    id = "m3d_context_support",
    label = "Context-support sensitivity",
    outcome = "child_context_support_bits",
    family_name = "scaled_t",
    family = scat(link = "identity"),
    formula = paste("child_context_support_bits ~", information_base),
    subset = quote(is.finite(child_context_support_bits)),
    grid = "age_length"
  ),
  list(
    id = "m4_effort_percentile",
    label = "Effort calibration inside the Qwen length distribution",
    outcome = "effort_percentile_open",
    family_name = "beta",
    family = betar(link = "logit"),
    formula = paste("effort_percentile_open ~", length_base),
    subset = quote(is.finite(effort_percentile_open)),
    grid = "age_entropy"
  ),
  list(
    id = "m5_exact_length_k3_gap",
    label = "Exact-length child-minus-Qwen contextual surprisal gap",
    outcome = "child_minus_exact_length_qwen_median_k3",
    family_name = "scaled_t",
    family = scat(link = "identity"),
    formula = paste(
      "child_minus_exact_length_qwen_median_k3 ~", length_base,
      "+ s(child_words, k=12, bs='cr')"
    ),
    subset = quote(exact_length_support >= 5 & is.finite(child_minus_exact_length_qwen_median_k3)),
    grid = "age_entropy"
  ),
  list(
    id = "m6_raw_nondominated",
    label = "Secondary raw Qwen nondominance diagnostic",
    outcome = "raw_nondominated",
    family_name = "binomial",
    family = binomial(link = "logit"),
    formula = paste("raw_nondominated ~", length_base, "+ s(child_words, k=12, bs='cr')"),
    subset = quote(raw_nondominated %in% c(0, 1)),
    grid = "age_entropy"
  )
)

if (model_set == "core") {
  core_ids <- c("m1_length_primary", "m3_information_k3_total", "m4_effort_percentile")
  specs <- specs[vapply(specs, function(spec) spec$id %in% core_ids, logical(1))]
}

reference <- list(
  age_min = max(6, floor(quantile(data$age_months, 0.005, na.rm = TRUE))),
  age_max = min(65, ceiling(quantile(data$age_months, 0.995, na.rm = TRUE))),
  age_median = median(data$age_months, na.rm = TRUE),
  entropy = quantile(data$response_entropy_bits, c(0.05, 0.10, 0.50, 0.90, 0.95), na.rm = TRUE),
  context_words = median(data$context_word_count, na.rm = TRUE),
  qwen_words = quantile(data$qwen_mean_word_count, c(0.10, 0.50, 0.90), na.rm = TRUE),
  child_words = median(data$child_words, na.rm = TRUE),
  child_key = levels(data$child_key)[[1]],
  dataset = levels(data$dataset)[[1]]
)

newdata_base <- function(frame) {
  if (!"context_word_count" %in% names(frame)) frame$context_word_count <- reference$context_words
  if (!"qwen_mean_word_count" %in% names(frame)) frame$qwen_mean_word_count <- reference$qwen_words[[2]]
  if (!"child_words" %in% names(frame)) frame$child_words <- reference$child_words
  frame$child_key <- factor(reference$child_key, levels = levels(data$child_key))
  frame$dataset <- factor(reference$dataset, levels = levels(data$dataset))
  frame$age_z <- (frame$age_months - mean(data$age_months, na.rm = TRUE)) / sd(data$age_months, na.rm = TRUE)
  frame$entropy_z <- (frame$response_entropy_bits - mean(data$response_entropy_bits, na.rm = TRUE)) /
    sd(data$response_entropy_bits, na.rm = TRUE)
  frame
}

prediction_grid <- function(model, grid_type, model_id) {
  ages <- seq(reference$age_min, reference$age_max, length.out = 45)
  entropy_values <- seq(reference$entropy[[1]], reference$entropy[[5]], length.out = 35)
  if (grid_type == "age_entropy") {
    grid <- expand.grid(age_months = ages, response_entropy_bits = entropy_values)
    grid$grid_type <- "age_entropy_surface"
    grid$reference_level <- "not_applicable"
  } else if (grid_type == "age_entropy_reference") {
    grid <- expand.grid(
      age_months = ages,
      response_entropy_bits = entropy_values,
      qwen_mean_word_count = unname(reference$qwen_words)
    )
    grid$grid_type <- "age_entropy_qwen_reference_surface"
    grid$reference_level <- rep(c("low", "median", "high"), each = length(ages) * length(entropy_values))
  } else if (grid_type == "age_length") {
    grid <- expand.grid(age_months = ages, child_words = 1:12)
    grid$response_entropy_bits <- reference$entropy[[3]]
    grid$grid_type <- "age_length_surface"
    grid$reference_level <- "median_entropy"
  } else {
    stop(paste("unknown grid type", grid_type))
  }
  grid <- newdata_base(grid)
  random_labels <- vapply(model$smooth, function(value) value$label, character(1))
  exclusions <- random_labels[grepl("child_key|dataset", random_labels)]
  predicted <- predict(model, newdata = grid, type = "link", se.fit = TRUE, exclude = exclusions)
  grid$estimate <- model$family$linkinv(predicted$fit)
  grid$ci_low <- model$family$linkinv(predicted$fit - 1.96 * predicted$se.fit)
  grid$ci_high <- model$family$linkinv(predicted$fit + 1.96 * predicted$se.fit)
  grid$model_id <- model_id
  grid
}

model_contrasts <- function(model, grid_type, model_id) {
  random_labels <- vapply(model$smooth, function(value) value$label, character(1))
  exclusions <- random_labels[grepl("child_key|dataset", random_labels)]
  rows <- list()
  add_pair <- function(from, to, comparison, moderator, moderator_value) {
    pair <- newdata_base(rbind(from, to))
    matrix <- predict(model, newdata = pair, type = "lpmatrix", exclude = exclusions)
    difference <- matrix[2, ] - matrix[1, ]
    link_difference <- as.numeric(difference %*% coef(model))
    link_se <- sqrt(max(0, as.numeric(difference %*% model$Vp %*% difference)))
    link_low <- link_difference - 1.96 * link_se
    link_high <- link_difference + 1.96 * link_se
    endpoint_link <- as.numeric(matrix %*% coef(model))
    endpoint_response <- model$family$linkinv(endpoint_link)
    link_name <- model$family$link
    rows[[length(rows) + 1]] <<- data.frame(
      model_id = model_id,
      comparison = comparison,
      moderator = moderator,
      moderator_value = moderator_value,
      from_age = pair$age_months[[1]], to_age = pair$age_months[[2]],
      from_entropy = pair$response_entropy_bits[[1]], to_entropy = pair$response_entropy_bits[[2]],
      from_child_words = pair$child_words[[1]], to_child_words = pair$child_words[[2]],
      from_response = endpoint_response[[1]], to_response = endpoint_response[[2]],
      response_difference = endpoint_response[[2]] - endpoint_response[[1]],
      link = link_name,
      link_difference = link_difference, link_se = link_se,
      link_ci_low = link_low, link_ci_high = link_high,
      ratio_or_odds_ratio = if (link_name %in% c("log", "logit")) exp(link_difference) else NA_real_,
      ratio_or_odds_ci_low = if (link_name %in% c("log", "logit")) exp(link_low) else NA_real_,
      ratio_or_odds_ci_high = if (link_name %in% c("log", "logit")) exp(link_high) else NA_real_,
      p_value = 2 * pnorm(abs(link_difference / link_se), lower.tail = FALSE)
    )
  }
  entropy_levels <- c(low = reference$entropy[[2]], median = reference$entropy[[3]], high = reference$entropy[[4]])
  ages <- unique(pmin(reference$age_max, pmax(reference$age_min, c(18, 30, 42, 54, 60))))
  if (grid_type %in% c("age_entropy", "age_entropy_reference")) {
    for (label in names(entropy_levels)) {
      entropy <- entropy_levels[[label]]
      add_pair(
        data.frame(age_months = reference$age_min, response_entropy_bits = entropy),
        data.frame(age_months = reference$age_max, response_entropy_bits = entropy),
        "age_min_to_max", "response_entropy", label
      )
    }
    for (age in ages) {
      add_pair(
        data.frame(age_months = age, response_entropy_bits = entropy_levels[["low"]]),
        data.frame(age_months = age, response_entropy_bits = entropy_levels[["high"]]),
        "entropy_p10_to_p90", "age_months", age
      )
    }
  } else if (grid_type == "age_length") {
    for (words in c(1, 2, 4, 8, 12)) {
      add_pair(
        data.frame(age_months = reference$age_min, response_entropy_bits = entropy_levels[["median"]], child_words = words),
        data.frame(age_months = reference$age_max, response_entropy_bits = entropy_levels[["median"]], child_words = words),
        "age_min_to_max", "child_words", words
      )
    }
    for (age in ages) {
      add_pair(
        data.frame(age_months = age, response_entropy_bits = entropy_levels[["median"]], child_words = 2),
        data.frame(age_months = age, response_entropy_bits = entropy_levels[["median"]], child_words = 6),
        "length_2_to_6", "age_months", age
      )
    }
  }
  bind_rows_fill(rows)
}

registry_rows <- list()
smooth_rows <- list()
parametric_rows <- list()
k_rows <- list()
prediction_rows <- list()
residual_rows <- list()
contrast_rows <- list()
selected_models <- list()
successful_ids <- character()

bind_rows_fill <- function(frames) {
  if (!length(frames)) return(data.frame())
  columns <- unique(unlist(lapply(frames, names), use.names = FALSE))
  aligned <- lapply(frames, function(frame) {
    missing <- setdiff(columns, names(frame))
    for (column in missing) frame[[column]] <- NA
    frame[, columns, drop = FALSE]
  })
  do.call(rbind, aligned)
}

for (spec in specs) {
  message("[R models] fitting ", spec$id)
  subset_rows <- with(data, eval(spec$subset))
  model_data <- data[which(subset_rows), , drop = FALSE]
  status <- "PASS"
  error_text <- ""
  fitted <- tryCatch(
    bam(
      as.formula(spec$formula),
      data = model_data,
      family = spec$family,
      method = "fREML",
      discrete = TRUE,
      nthreads = threads,
      select = TRUE,
      gc.level = 1,
      drop.unused.levels = FALSE
    ),
    error = function(error) {
      status <<- "FAIL"
      error_text <<- conditionMessage(error)
      NULL
    }
  )
  if (is.null(fitted)) {
    registry_rows[[length(registry_rows) + 1]] <- data.frame(
      model_id = spec$id, model_label = spec$label, outcome = spec$outcome,
      family = spec$family_name, formula = spec$formula, status = status,
      n_rows = nrow(model_data), deviance_explained = NA_real_, adjusted_r2 = NA_real_,
      aic = NA_real_, total_edf = NA_real_, converged = FALSE, error = error_text
    )
    next
  }
  successful_ids <- c(successful_ids, spec$id)
  if (spec$id %in% c("m1_length_primary", "m3_information_k3_total")) {
    selected_models[[spec$id]] <- fitted
  }
  summary_fit <- summary(fitted)
  rds_path <- file.path(output_dir, "rds", paste0(spec$id, ".rds"))
  saveRDS(fitted, rds_path, compress = "gzip")
  registry_rows[[length(registry_rows) + 1]] <- data.frame(
    model_id = spec$id, model_label = spec$label, outcome = spec$outcome,
    family = spec$family_name, formula = spec$formula, status = status,
    n_rows = nrow(model_data), deviance_explained = summary_fit$dev.expl,
    adjusted_r2 = ifelse(is.null(summary_fit$r.sq), NA_real_, summary_fit$r.sq),
    aic = AIC(fitted), total_edf = sum(fitted$edf),
    converged = isTRUE(fitted$converged), error = error_text
  )
  if (!is.null(summary_fit$s.table)) {
    table <- as.data.frame(summary_fit$s.table)
    table$term <- rownames(table)
    names(table) <- make.names(names(table))
    table$model_id <- spec$id
    smooth_rows[[length(smooth_rows) + 1]] <- table
  }
  if (!is.null(summary_fit$p.table)) {
    table <- as.data.frame(summary_fit$p.table)
    table$term <- rownames(table)
    names(table) <- make.names(names(table))
    table$model_id <- spec$id
    parametric_rows[[length(parametric_rows) + 1]] <- table
  }
  k_check <- tryCatch(k.check(fitted, subsample = 5000, n.rep = 200), error = function(error) NULL)
  if (!is.null(k_check)) {
    table <- as.data.frame(k_check)
    table$term <- rownames(table)
    names(table) <- make.names(names(table))
    table$model_id <- spec$id
    k_rows[[length(k_rows) + 1]] <- table
  }
  prediction_rows[[length(prediction_rows) + 1]] <- prediction_grid(fitted, spec$grid, spec$id)
  contrast_rows[[length(contrast_rows) + 1]] <- model_contrasts(fitted, spec$grid, spec$id)
  sample_n <- min(15000L, nrow(model_data))
  indices <- unique(round(seq(1, nrow(model_data), length.out = sample_n)))
  residual_rows[[length(residual_rows) + 1]] <- data.frame(
    model_id = spec$id,
    observed = model_data[[spec$outcome]][indices],
    fitted = fitted$fitted.values[indices],
    deviance_residual = residuals(fitted, type = "deviance")[indices],
    age_months = model_data$age_months[indices],
    child_key = as.character(model_data$child_key[indices])
  )
  rm(model_data, fitted)
  gc(verbose = FALSE)
}

registry <- bind_rows_fill(registry_rows)
smooth_terms <- bind_rows_fill(smooth_rows)
parametric_terms <- bind_rows_fill(parametric_rows)
k_diagnostics <- bind_rows_fill(k_rows)
predictions <- bind_rows_fill(prediction_rows)
residuals_sample <- bind_rows_fill(residual_rows)
contrasts <- bind_rows_fill(contrast_rows)

child_effects <- list()
child_map <- aggregate(dataset ~ child_key, data = data, FUN = function(value) as.character(value[[1]]))
entropy_low <- reference$entropy[[2]]
entropy_high <- reference$entropy[[4]]
for (model_id in intersect(c("m1_length_primary", "m3_information_k3_total"), names(selected_models))) {
  model <- selected_models[[model_id]]
  outcome <- registry$outcome[match(model_id, registry$model_id)]
  for (index in seq_len(nrow(child_map))) {
    child <- as.character(child_map$child_key[[index]])
    dataset_value <- as.character(child_map$dataset[[index]])
    age_frame <- data.frame(
      age_months = c(18, 60),
      response_entropy_bits = reference$entropy[[3]],
      context_word_count = reference$context_words,
      qwen_mean_word_count = reference$qwen_words[[2]],
      child_words = reference$child_words,
      child_key = factor(child, levels = levels(data$child_key)),
      dataset = factor(dataset_value, levels = levels(data$dataset))
    )
    age_frame$age_z <- (age_frame$age_months - mean(data$age_months)) / sd(data$age_months)
    age_frame$entropy_z <- (age_frame$response_entropy_bits - mean(data$response_entropy_bits)) /
      sd(data$response_entropy_bits)
    entropy_frame <- age_frame[c(1, 1), ]
    entropy_frame$age_months <- reference$age_median
    entropy_frame$age_z <- (reference$age_median - mean(data$age_months)) / sd(data$age_months)
    entropy_frame$response_entropy_bits <- c(entropy_low, entropy_high)
    entropy_frame$entropy_z <- (entropy_frame$response_entropy_bits - mean(data$response_entropy_bits)) /
      sd(data$response_entropy_bits)
    age_prediction <- predict(model, newdata = age_frame, type = "response", exclude = "s(dataset)")
    entropy_prediction <- predict(model, newdata = entropy_frame, type = "response", exclude = "s(dataset)")
    child_effects[[length(child_effects) + 1]] <- data.frame(
      model_id = model_id,
      outcome = outcome,
      child_key = child,
      dataset = dataset_value,
      predicted_age18 = age_prediction[[1]],
      predicted_age60 = age_prediction[[2]],
      age_change_per_month = (age_prediction[[2]] - age_prediction[[1]]) / 42,
      predicted_entropy_low = entropy_prediction[[1]],
      predicted_entropy_high = entropy_prediction[[2]],
      entropy_change_per_bit = (entropy_prediction[[2]] - entropy_prediction[[1]]) /
        (entropy_high - entropy_low)
    )
  }
}
child_effects <- if (length(child_effects)) do.call(rbind, child_effects) else data.frame()

for (name in c("registry", "smooth_terms", "parametric_terms", "k_diagnostics",
               "predictions", "residuals_sample", "contrasts", "child_effects")) {
  frame <- get(name)
  if (nrow(frame)) frame$analysis_scope <- analysis_scope
  assign(name, frame)
}

registry_path <- file.path(output_dir, "model_registry.csv")
smooth_path <- file.path(output_dir, "smooth_terms.csv")
parametric_path <- file.path(output_dir, "parametric_terms.csv")
k_path <- file.path(output_dir, "smooth_k_diagnostics.csv")
predictions_path <- file.path(output_dir, "prediction_grids.csv.gz")
residuals_path <- file.path(output_dir, "residual_diagnostics_sample.csv.gz")
child_effects_path <- file.path(output_dir, "child_effects.csv")
contrasts_path <- file.path(output_dir, "model_contrasts.csv")
reference_path <- file.path(output_dir, "prediction_reference.json")

write_csv_atomic(registry, registry_path)
write_csv_atomic(smooth_terms, smooth_path)
write_csv_atomic(parametric_terms, parametric_path)
write_csv_atomic(k_diagnostics, k_path)
write_csv_atomic(predictions, predictions_path, gzip = TRUE)
write_csv_atomic(residuals_sample, residuals_path, gzip = TRUE)
write_csv_atomic(child_effects, child_effects_path)
write_csv_atomic(contrasts, contrasts_path)
write_json(reference, reference_path, pretty = TRUE, auto_unbox = TRUE)

output_paths <- c(
  model_registry = registry_path,
  smooth_terms = smooth_path,
  parametric_terms = parametric_path,
  smooth_k_diagnostics = k_path,
  prediction_grids = predictions_path,
  residual_diagnostics = residuals_path,
  child_effects = child_effects_path,
  model_contrasts = contrasts_path,
  prediction_reference = reference_path
)
for (model_id in successful_ids) {
  output_paths[[paste0("rds_", model_id)]] <- file.path(output_dir, "rds", paste0(model_id, ".rds"))
}

manifest <- list(
  status = if (all(registry$status == "PASS")) "PASS" else "FAIL",
  engine = "mgcv::bam",
  mgcv_version = as.character(packageVersion("mgcv")),
  analysis_scope = analysis_scope,
  sample_role = switch(
    analysis_scope,
    all79 = "pooled_descriptive",
    pbm_discovery = "discovery",
    non_pbm_confirmation = "confirmation"
  ),
  model_set = model_set,
  completed_at = format(Sys.time(), tz = "UTC", usetz = TRUE),
  input = file_record(input_path),
  registered_models = nrow(registry),
  passed_models = sum(registry$status == "PASS"),
  outputs = lapply(output_paths, file_record)
)
manifest_path <- file.path(output_dir, "r_model_manifest.json")
write_json(manifest, manifest_path, pretty = TRUE, auto_unbox = TRUE)

if (!all(registry$status == "PASS")) {
  stop(paste("model failures:", paste(registry$model_id[registry$status != "PASS"], collapse = ", ")))
}
message("[R models] all registered models passed")
