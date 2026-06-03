# Agentic History

Timestamped working memory for future coding agents. This file records decisions
that are easy to lose in chat context but important for reproducing or
explaining the project.

## 2026-05-28 PBM Additive LSTM Generation

User goal:

- Generate LSTM child-utterance baselines comparable to the existing random,
  unigram, bigram, and trigram generated baselines.
- Keep the first serious run restricted to Brown, Manchester, and Providence
  before scaling to all strict-naturalistic corpora.
- Preserve the additive age-bin information logic already used for n-grams.
- Compare local caretaker context windows `k=3`, `k=4`, and `k=5`.
- Keep documentation both agent-facing and supervisor-readable.

Design decisions:

- Use a word-level encoder-decoder LSTM, implemented in
  `src/generate_lstm_utterances.py`.
- Use additive age-bin training:
  - `006-023` trains on `006-023`.
  - `024-029` trains on `006-029`.
  - Continue cumulatively through `060-065`.
- Use PBM only for this run: Brown, Manchester, Providence.
- Train independent LSTM models for each context window and target age bin.
- Use same-length decoding as the main output so effort is controlled by word
  count, matching the existing generated baselines.
- Do not mix `k=3`, `k=4`, and `k=5` row-by-row; keep one generated column per
  context window.

Implemented files:

- `src/run_lstm_additive_age_context_pipeline.py`
- `tests/test_lstm_additive_age_context_pipeline.py`
- `docs/lstm-additive-pbm-supervisor-summary.md`

Instrumentation added:

- Per-bin `batch_training_log.csv`
- Per-bin and run-level `training_summary.csv`
- `model_run_manifest.csv`
- `generation_diagnostics.csv`
- `generation_samples.csv`
- PNG/PDF plots under each run's `plots/` folder

Real run command:

```bash
.venv/bin/python src/run_lstm_additive_age_context_pipeline.py \
  --output_dir results/lstm_baselines/pbm_additive_merged_006_023_k3_k4_k5_same_length \
  --contexts 3 4 5 \
  --variants same_length \
  --epochs 3 \
  --embedding_dim 128 \
  --hidden_dim 256 \
  --batch_size 128 \
  --max_vocab_size 30000 \
  --device cuda
```

Run result:

- Completed on the local PC GPU, NVIDIA GeForce RTX 4060 Ti with 16GB VRAM.
- Trained 24 models: 3 context windows times 8 additive age bins.
- Output directory:
  `results/lstm_baselines/pbm_additive_merged_006_023_k3_k4_k5_same_length/`
- Generated columns:
  - `lstm_additive_k3_same_length_utterance`
  - `lstm_additive_k4_same_length_utterance`
  - `lstm_additive_k5_same_length_utterance`

Validation:

- 21 generated child files found.
- 519,803 child rows checked.
- 446,508 non-empty generated rows per LSTM column.
- 0 same-length mismatches for k3, k4, or k5.
- 21 context-with-LSTM files and 21 scoring-with-LSTM files found.
- 446,985 scoring rows with LSTM columns.

Scoring-context reminder:

- Generation context and scoring context are separate design axes.
- The LSTM `k3`, `k4`, and `k5` conditions describe how many previous
  caretaker utterances were given to the LSTM generator.
- Surprisal scoring should still use the row-matched `context_k1`,
  `context_k2`, and `context_k3` columns for every target string.
- This applies to real child utterances, generated child-like baselines, and
  caretaker target utterances. Do not score a generated utterance with a context
  borrowed from another row.

Course-material alignment:

- `NLP-week3-ngrams.pdf`: n-grams are finite-context Markov language models.
- `NLP-week6-rnnlstm.pdf`: recurrent models represent history in hidden state;
  LSTMs add gated context management.
- `week6-lstms-solutions.ipynb`: teacher's PyTorch LSTM workflow uses a
  vocabulary, indexed sequences, custom dataset/collate, training loop, and
  cross-entropy-style loss. This project uses the same neural sequence-modeling
  logic, but with an encoder-decoder generation target instead of sequence
  labeling/classification.
