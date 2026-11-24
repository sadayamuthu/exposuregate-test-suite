# eg-data-missing

A lockfile changes but there is no data directory index. The gate denies instead of passing.

- Category: fail-closed
- Modes: pr, pre-commit, refs
- Expected: **DENY**, exit 2
- Denials: data_missing

`base/` is main; `change/` is what the change writes. See `case.json`.
