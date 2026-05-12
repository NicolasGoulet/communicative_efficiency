# Coding Guidelines

Repo-specific coding conventions.

## General Style

- Prefer simple, explicit Python.
- Keep changes small and reviewable.
- Follow existing local patterns before introducing new abstractions.
- Use clear names for data columns and file paths.

TODO: Add any preferred formatting/linting tools.

## Paths And Files

- Do not hardcode machine-specific absolute paths.
- Prefer `pathlib.Path`.
- Keep raw data read-only.
- Write generated outputs under documented output folders.

TODO: Define canonical output roots.

## Data Safety

- Do not overwrite raw CHILDES / CHAT files.
- Do not silently drop rows.
- Preserve provenance columns when transforming data.
- Document any schema changes.

## Comments And Docstrings

- Comment non-obvious data policies.
- Avoid comments that merely repeat the code.
- Use docstrings for public helpers that encode project assumptions.

## Tests

Current test style:

- simple `unittest` files under `tests/`
- tiny toy examples
- easy-to-edit expected values

Current command:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

TODO: Add fixture policy if fixtures become larger.
