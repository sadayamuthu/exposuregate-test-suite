# eg-data-stale

Frozen data with the default 7-day limit: OEBC (built 2026-06-14) is 152 days old on 2026-11-13, so the scan is denied.

- Category: fail-closed
- Modes: pr
- Expected: **DENY**, exit 2
- Denials: data_stale

`base/` is main; `change/` is what the change writes. See `case.json`.
