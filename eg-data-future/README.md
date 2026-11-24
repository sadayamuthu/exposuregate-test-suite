# eg-data-future

The scan runs as of 2026-06-30, before the OSV export (2026-11-13) was made. Data from the future is denied.

- Category: fail-closed
- Modes: pr
- Expected: **DENY**, exit 2
- Denials: data_from_future

`base/` is main; `change/` is what the change writes. See `case.json`.
