data {
  int<lower=2> N;
  int<lower=1> C;
  array[N] int<lower=1, upper=C> corpus_id;
  array[N] vector[2] slope_hat;
  array[N] cov_matrix[2] estimation_cov;
  real<lower=0> coefficient_sd;
  real<lower=0> random_sd;
  real<lower=1> lkj_eta;
}

transformed data {
  array[N] cholesky_factor_cov[2] estimation_cholesky;
  for (n in 1:N) {
    estimation_cholesky[n] = cholesky_decompose(estimation_cov[n]);
  }
}

parameters {
  vector[2] population_mean;

  vector<lower=0>[2] child_sd;
  cholesky_factor_corr[2] child_correlation_cholesky;
  matrix[2, N] child_z;

  vector<lower=0>[2] corpus_sd;
  cholesky_factor_corr[2] corpus_correlation_cholesky;
  matrix[2, C] corpus_z;
}

transformed parameters {
  matrix[2, N] latent_child_slope;
  matrix[2, 2] child_cholesky =
    diag_pre_multiply(child_sd, child_correlation_cholesky);
  matrix[2, 2] corpus_cholesky =
    diag_pre_multiply(corpus_sd, corpus_correlation_cholesky);
  matrix[2, C] corpus_effect = corpus_cholesky * corpus_z;

  for (n in 1:N) {
    latent_child_slope[, n] = population_mean
                              + corpus_effect[, corpus_id[n]]
                              + child_cholesky * child_z[, n];
  }
}

model {
  population_mean ~ normal(0, coefficient_sd);
  child_sd ~ normal(0, random_sd);
  corpus_sd ~ normal(0, random_sd);
  child_correlation_cholesky ~ lkj_corr_cholesky(lkj_eta);
  corpus_correlation_cholesky ~ lkj_corr_cholesky(lkj_eta);
  to_vector(child_z) ~ std_normal();
  to_vector(corpus_z) ~ std_normal();

  for (n in 1:N) {
    slope_hat[n] ~ multi_normal_cholesky(
      latent_child_slope[, n], estimation_cholesky[n]
    );
  }
}

generated quantities {
  corr_matrix[2] child_correlation =
    multiply_lower_tri_self_transpose(child_correlation_cholesky);
  cov_matrix[2] between_child_covariance =
    quad_form_diag(child_correlation, child_sd);
  real between_child_correlation = child_correlation[1, 2];
  vector[N] log_lik;
  array[N] vector[2] slope_rep;

  for (n in 1:N) {
    log_lik[n] = multi_normal_cholesky_lpdf(
      slope_hat[n] | latent_child_slope[, n], estimation_cholesky[n]
    );
    slope_rep[n] = multi_normal_cholesky_rng(
      latent_child_slope[, n], estimation_cholesky[n]
    );
  }
}
