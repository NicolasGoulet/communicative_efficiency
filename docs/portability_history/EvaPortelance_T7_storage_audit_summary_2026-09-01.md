# EvaPortelance T7 storage audit — 2026-09-01

Read-only audit only. No files were edited, moved, renamed, or deleted. The scan was stopped before unplugging the T7.

## Main finding

`/media/alkan/T7/EvaPortelance/Projet_1` occupies approximately **336.93 GiB (361.77 GB)**.

Largest top-level branches:

- `compute_surprisal_mila`: **205.65 GiB**
- `communicative_efficiency`: **88.96 GiB**
- `surprisal_computing`: **16.49 GiB**
- `compute_surprisal_mila_qwen_word_surprisal`: **10.91 GiB**
- `BACK_UP_SURPRISAL_COMPUTING`: **6.04 GiB**
- `old_results`: **2.52 GiB**

## Best cleanup candidates to review

- Reproducible environments/builds: `compute_surprisal_mila/.venv` (**10.61 GiB**), `communicative_efficiency/.bayes-r-lib` (**2.84 GiB**), and `communicative_efficiency/.cmdstan` (**3.75 GiB**). Potential total: **17.20 GiB**.
- Git worktrees: `compute_surprisal_mila/.worktrees` is **22.31 GiB**. Check for uncommitted or untracked work before removing worktrees properly through Git.
- Historical backup: `BACK_UP_SURPRISAL_COMPUTING` is **6.04 GiB**. Verify it is fully superseded before deletion.
- Generated outputs: `compute_surprisal_mila/results` is **20.66 GiB** and `figs` is **7.83 GiB**. Review which runs and figures are reproducible or obsolete.
- Main result archive: `compute_surprisal_mila/mila_results` is **141.18 GiB**. Its largest subtree is `crossmodel_word_surprisal` at **90.47 GiB**. Other large sets include `production_runs` (**14.27 GiB**), `tinydialogues_pbm_production` (**12.50 GiB**), and `qwen_response_mistral_full_scoring` (**8.92 GiB**).
- Possible overlapping cleaned results: `raw_surprisal_cleaned` and `raw_surprisal_cleaned_patched_006_023` are about **4.70 GiB each**, plus an **0.81 GiB** tar archive. Compare contents and provenance before choosing a canonical copy.
- Older result/figure trees elsewhere add several more GiB, including `old_results` (**2.52 GiB**) and `old_figs` (**1.02 GiB**).

## Cautions

- The large model-result directories may be unique research data. Do not delete them based on size alone; first confirm they exist elsewhere or can be regenerated.
- Git `.git` data was not classified as disposable.
- A small `mila_token.txt` file exists at the project root. Its contents were not opened. Treat it as a secret and consider rotating it if it is still active.
- The detailed scan of `communicative_efficiency` was interrupted, so its `results`, `figs`, `.venv`, and `.worktrees` still need a deeper read-only breakdown.

Likely reclaimable space is already **at least 45.55 GiB** from reproducible environments, the large worktree area, and the historical backup, subject to the checks above. Considerably more may be recoverable from generated and superseded results after provenance/backup verification.
