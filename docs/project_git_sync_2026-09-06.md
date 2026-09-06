# Portelance project Git synchronization — 2026-09-06

The six current project repositories and the legacy `surprisal_computing`
repository were checked against live GitHub branches and tags. Cached
`origin/main` references initially made two stale checkouts appear synchronized;
live HTTPS queries and fetches established the actual state.

## Repository coverage

| Repository | Initial local main | Live main / action |
|---|---|---|
| `communicative_efficiency` | `f109766487c58decd8f373f6384536d2614e7248` | Already matched GitHub; this documentation update preserves the audit and two previously unpublished recovery documents. |
| `compute_surprisal_mila` | `9d82ffa298c3293cd4468f9605190975cc7af5ca` | Fast-forwarded 139 commits to `6c9f716aaacccac65b3aadd9c94f6cb4dd8abf29`; push confirmed everything up to date. |
| `surprisal_computing` (legacy) | `62e8a732e53e783f0982e61f768c967dc64897f1` | Fast-forwarded six commits to `f0dc641e38680ee25b162bec004ab2ae8772a410`, then committed and pushed `e51004e7d7098f9f267e243349e60467ceee7646` to ignore local LibreOffice locks. |
| `developmental_word_information` | No checkout under the current native project root | GitHub main `12bd91b66d7fdb5155a8e380eabc807aa8017cf1`; saved branch tips are published. |
| `generate_baselines_mila` | No checkout under the current native project root | GitHub main `a455000568f70506d4501d62f32c7c3a24e6fd53`; saved branch tips are published. |
| `bayes_efficiency_mila` | No checkout under the current native project root | GitHub main `d37703d59b76d047971a6fcf130e58c6f8c88aee`; saved branch tip is published. |
| `child_complexity_predictors` | No checkout under the current native project root | GitHub main `33497c2189d28543a0f2280a5fff227d37c87dcb`; saved branch tip is published. |

The current native project root is `/home/alkan/Portelance/`. Every local branch
tip listed by the pre/post-integration bundles in
`/home/alkan/Documents/EvaPortelance_git_safety_2026-09-02/` was found at an
identical SHA on at least one live GitHub branch. Recovery/integration branch
names can differ while preserving the exact commit. This comparison inspected
bundle ref headers; it does not replace the original full bundle/hash audits.

## Preservation and changes

- The analysis repository's June 16 autostash
  `15c1eb1abf74670c4883553ee253a4d01552e141` contains 12 text files and one
  obsolete Python bytecode file. Ten text files match current main exactly;
  the other two (`TODO.md` and `docs/notes.md`) have their exact stashed blobs
  in main's history. The stash was neither applied nor dropped.
- Two external recovery notes are now preserved byte-for-byte under
  [`portability_history/`](portability_history/README.md), with SHA-256 values
  and an explicit historical-status notice. The third external note already
  exists in the maintained portability record's Git history.
- All three native checkouts now use their existing GitHub repository URLs
  over HTTPS and the existing `gh auth git-credential` helper, configured
  locally per repository. SSH failed because no usable key was available in
  this session; the existing GitHub CLI login was verified successfully.
- The legacy `.gitignore` adds only `.~lock.*`. The existing spreadsheet lock
  remains on disk. No new data or output files were staged for publication.
- Both fast-forwards were checked for local changes, ancestry, added-path
  collisions, and storage footprint. Scoring added about 17.8 MB of tracked
  files; legacy added about 2.20 GB, largely historically tracked data/output
  files already on GitHub. The operation retained at least 50 GiB free.
  Legacy's prior tracked data remain recoverable at its initial commit.

## Verification and limits

Verification used live `git ls-remote --heads --tags`, explicit HTTPS fetches,
`git rev-list --left-right --count HEAD...origin/main`, `git status`, bundle
ref comparisons, exact historical-blob checks, `git check-ignore`, and document
SHA-256 comparisons. New changes are documentation and one ignore rule; no
scientific source changes or new model results were introduced. No unit suite,
model fitting, scoring, Mila job, or data-archive re-audit was run.

The two archived notes retain their original bytes, including two intentional
Markdown hard-break lines in the long guide. Whitespace checking for that file
allows end-of-line spaces; current documentation uses the ordinary check.

The T7 was not mounted at either known location (`/media/alkan/T7/` or
`/mnt/d/`). Its current working-tree changes and data integrity therefore could
not be inspected. Four current repositories were verified through live GitHub
refs and saved recovery bundles, not through their absent T7 working trees.
The historical data stash in the compute recovery bundle remains preserved
there under the existing recovery policy.

Ignored datasets, scores, checkpoints, environments, caches, figures, and the
generated evidence ZIP remain outside Git under the repository's
[storage policy](project_portability_and_git_recovery_2026-09-02.md).
`Portelance/backup/` contains historical tables and figures, not another Git
checkout. Git synchronization is not a backup of these generated products.
