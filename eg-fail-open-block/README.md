# eg-fail-open-block

Stale data with --fail-open and a KEV pin: findings are still graded, so the KEV pin still blocks.

- Category: fail-closed
- Modes: pr
- Expected: **BLOCK**, exit 1
- Denials: data_stale

`base/` is main; `change/` is what the change writes. See `case.json`.
