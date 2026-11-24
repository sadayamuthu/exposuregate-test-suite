# eg-fail-open

Stale data with --fail-open: the denial is reported with enforced: false, and the verdict is WARN, never PASS, even for a benign bump.

- Category: fail-closed
- Modes: pr
- Expected: **WARN**, exit 0
- Denials: data_stale

`base/` is main; `change/` is what the change writes. See `case.json`.
