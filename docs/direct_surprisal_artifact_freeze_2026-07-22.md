# Direct-Surprisal Artifact Freeze

Frozen locally on 22 July 2026. This file records the immutable large-data
archives behind the current Mistral and TinyDialogues analyses without adding
those archives to Git.

## Scored Archives

| Scorer run | Run ID | Archive bytes | SHA-256 | Local status |
| --- | --- | ---: | --- | --- |
| Mistral full 79 | `20260713_162955` | 2,220,662,387 | `ff0bf42754fc6ccb8278db7a588cef1083ca18a944032b9ce9e1179341448a81` | archive and extracted 1,896-file scored tree present; compact Mila report and `COMPLETE` marker still need retrieval |
| TinyDialogues PBM | `20260717_201227` | 1,647,277,171 | `c2c0cb3a6f0e55cc97b2824ce3b418ead30ee4f41b3cf9987bec5a45012656ea` | archive and extracted 504-file scored tree present; `LOCAL_RETRIEVAL_AUDIT_PASSED`, `PBM_COMPLETE`, `SMOKE_PASSED`, and context-ready markers present |

The Mistral archive is stored under the ignored sibling-repository path
`compute_surprisal_mila/mila_results/production_runs/naturalistic_79_children_all_available_ages_all_6_conditions_k0_k1_k2_k3_fp16/20260713_162955/`.
The TinyDialogues archive is under
`compute_surprisal_mila/mila_results/tinydialogues_pbm_production/20260717_201227/`.

## Analysis Audit Hashes

| Artifact | SHA-256 |
| --- | --- |
| `results/direct_surprisal_replication/mistral_full79/manifest.json` | `a3d3f5932545a0676934789bd119f34a4fa3a7723a23fe29f929439ea675937e` |
| `results/direct_surprisal_replication/mistral_full79/source_file_audit.csv` | `d77f531d3ed3f8c16f2f572307fdf8d0118dafeef1518ac128c6417191e20867` |
| `results/direct_surprisal_replication/tinydialogues_pbm/manifest.json` | `79e6e4450180c5a7b527fdfa3379d8cc1612f4b6bf30811e59b1a74f9ec09de0` |
| `results/direct_surprisal_replication/tinydialogues_pbm/source_file_audit.csv` | `69faa710a0c2ea0b4e5646ed28b0e464f8fa23e6e570bc79deefb4fb1e0029ae` |
| `results/direct_surprisal_replication/paired_tiny_mistral_pbm/join_audit.json` | `acc9e616945c47e745abf5a15042c4301491a9aab6e4f23a23eda0198fb908c4` |

The Mistral analysis manifest records 79 children, 1,140,695 child rows,
1,470,154 caretaker rows, and 24 blank generated-baseline score cells. The
TinyDialogues manifest records 21 children, 446,508 child rows, 668,903
caretaker rows, and no blank targets. The exact paired intersection contains
446,508 rows; all 477 join mismatches are the documented later Naima coverage
addition in the Mistral source.

## Verification Boundary

The hashes above freeze the compressed scorer archives and compact analysis
audits. They do not convert the 24 Mistral generated-baseline gaps into valid
scores. Those cells remain flagged, and the full-79 LSTM, semantic-response
entropy, listener-utility, and other incomplete predictor families remain
separate future products.
