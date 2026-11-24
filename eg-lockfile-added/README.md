# eg-lockfile-added

The change adds the project's first lockfile, which pins a KEV version. Every pin in a new lockfile counts as added.

- Category: repo-shape
- Modes: pr, pre-commit, refs
- Expected: **BLOCK**, exit 1

`base/` is main; `change/` is what the change writes. See `case.json`.
