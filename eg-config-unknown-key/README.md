# eg-config-unknown-key

A misspelled config key (polcy). Every key changes behaviour, so an unknown one is an error (exit 2, no report), not ignored.

- Category: usage-error
- Modes: pr
- Expected: **no report**, exit 2

`base/` is main; `change/` is what the change writes. See `case.json`.
