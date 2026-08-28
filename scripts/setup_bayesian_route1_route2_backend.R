#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
stage <- if (length(args) >= 1) args[[1]] else "all"
if (!stage %in% c("packages", "cmdstan", "all", "audit")) {
  stop("usage: setup_bayesian_route1_route2_backend.R [packages|cmdstan|all|audit]")
}

root <- normalizePath(getwd(), mustWork = TRUE)
library_path <- file.path(root, ".bayes-r-lib")
cmdstan_parent <- file.path(root, ".cmdstan")
dir.create(library_path, recursive = TRUE, showWarnings = FALSE)
dir.create(cmdstan_parent, recursive = TRUE, showWarnings = FALSE)
unlink(Sys.glob(file.path(library_path, "00LOCK*")), recursive = TRUE, force = TRUE)
.libPaths(c(library_path, .Library.site, .Library))

pins <- c(
  brms = "2.23.0",
  cmdstanr = "0.9.0"
)
pin_sources <- c(
  brms = "https://cran.r-project.org/src/contrib/Archive/brms/brms_2.23.0.tar.gz",
  cmdstanr = "https://stan-dev.r-universe.dev/src/contrib/cmdstanr_0.9.0.tar.gz"
)
support_packages <- c("posterior", "loo", "bayesplot", "data.table", "jsonlite")

install_local_packages <- function() {
  repos <- c(
    STAN = "https://stan-dev.r-universe.dev",
    CRAN = "https://cloud.r-project.org"
  )
  options(repos = repos, Ncpus = 1L)
  required <- c(names(pins), support_packages)
  missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing)) {
    install.packages(missing, lib = library_path, dependencies = c("Depends", "Imports", "LinkingTo"))
  }
  installed_versions <- vapply(
    names(pins),
    function(package) if (requireNamespace(package, quietly = TRUE)) as.character(packageVersion(package)) else "MISSING",
    character(1)
  )
  wrong <- names(pins)[installed_versions != pins]
  for (package in wrong) {
    install.packages(pin_sources[[package]], lib = library_path, repos = NULL, type = "source")
  }
}

audit <- function(require_cmdstan = TRUE) {
  versions <- vapply(
    c(names(pins), support_packages),
    function(package) {
      if (requireNamespace(package, quietly = TRUE)) as.character(packageVersion(package)) else "MISSING"
    },
    character(1)
  )
  wrong <- names(pins)[versions[names(pins)] != pins]
  if (length(wrong)) {
    stop("pinned package version mismatch: ", paste(sprintf("%s=%s (expected %s)", wrong, versions[wrong], pins[wrong]), collapse = "; "))
  }
  cmdstan_path <- file.path(cmdstan_parent, "cmdstan-2.39.0")
  if (require_cmdstan && !dir.exists(cmdstan_path)) {
    stop("pinned CmdStan is missing: ", cmdstan_path)
  }
  payload <- list(
    status = "PASS",
    library = library_path,
    packages = as.list(versions),
    cmdstan_path = cmdstan_path,
    cmdstan_present = dir.exists(cmdstan_path),
    global_library_unchanged = TRUE
  )
  cat(jsonlite::toJSON(payload, auto_unbox = TRUE, pretty = TRUE), "\n")
}

if (stage %in% c("packages", "all")) {
  install_local_packages()
  audit(require_cmdstan = FALSE)
}

if (stage %in% c("cmdstan", "all")) {
  if (!requireNamespace("cmdstanr", quietly = TRUE)) {
    stop("cmdstanr must be installed in the local library first")
  }
  cmdstanr::install_cmdstan(
    version = "2.39.0",
    dir = cmdstan_parent,
    cores = max(1L, min(4L, parallel::detectCores(logical = FALSE))),
    overwrite = FALSE,
    quiet = FALSE
  )
  cmdstanr::set_cmdstan_path(file.path(cmdstan_parent, "cmdstan-2.39.0"))
}

if (stage %in% c("cmdstan", "all", "audit")) {
  audit(require_cmdstan = TRUE)
}
