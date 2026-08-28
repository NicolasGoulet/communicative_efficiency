data {
  int<lower=2> N;
  int<lower=2> C;
  int<lower=1> K;
  array[N] int<lower=1, upper=C> corpus_id;
  array[N] vector[K] coefficient_hat;
  array[N] cov_matrix[K] estimation_cov;
  vector<lower=0>[K] population_prior_sd;
  vector<lower=0>[K] child_sd_prior_scale;
  vector<lower=0>[K] corpus_sd_prior_scale;
  real<lower=1> lkj_eta;
}

transformed data {
  array[N] cholesky_factor_cov[K] estimation_cholesky;
  for (n in 1:N) {
    estimation_cholesky[n] = cholesky_decompose(estimation_cov[n]);
  }
}

parameters {
  vector[K] population_mean;

  vector<lower=0>[K] child_sd;
  cholesky_factor_corr[K] child_correlation_cholesky;
  matrix[K, N] child_z;

  vector<lower=0>[K] corpus_sd;
  matrix[K, C] corpus_z;
}

transformed parameters {
  matrix[K, K] child_cholesky =
    diag_pre_multiply(child_sd, child_correlation_cholesky);
  matrix[K, C] corpus_effect = diag_matrix(corpus_sd) * corpus_z;
  matrix[K, N] latent_child_coefficient;

  for (n in 1:N) {
    latent_child_coefficient[, n] = population_mean
                                          + corpus_effect[, corpus_id[n]]
                                          + child_cholesky * child_z[, n];
  }
}

model {
  population_mean ~ normal(0, population_prior_sd);
  child_sd ~ normal(0, child_sd_prior_scale);
  corpus_sd ~ normal(0, corpus_sd_prior_scale);
  child_correlation_cholesky ~ lkj_corr_cholesky(lkj_eta);
  to_vector(child_z) ~ std_normal();
  to_vector(corpus_z) ~ std_normal();

  for (n in 1:N) {
    coefficient_hat[n] ~ multi_normal_cholesky(
      latent_child_coefficient[, n], estimation_cholesky[n]
    );
  }
}

generated quantities {
  corr_matrix[K] child_correlation =
    multiply_lower_tri_self_transpose(child_correlation_cholesky);
  cov_matrix[K] between_child_covariance =
    quad_form_diag(child_correlation, child_sd);
  vector[N] log_lik;
  array[N] vector[K] coefficient_rep;

  for (n in 1:N) {
    log_lik[n] = multi_normal_cholesky_lpdf(
      coefficient_hat[n] | latent_child_coefficient[, n], estimation_cholesky[n]
    );
    coefficient_rep[n] = multi_normal_cholesky_rng(
      latent_child_coefficient[, n], estimation_cholesky[n]
    );
  }
}
