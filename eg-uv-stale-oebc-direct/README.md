# eg-uv-stale-oebc-direct

Documents OEBC staleness: CVE-2026-111497 was KEV-listed 2026-10-27, after the 2026-06-14 OEBC build, so it is not_in_oebc (warn) instead of CRITICAL (block).

- Category: stale-catalog
- Modes: pr, pre-commit, refs
- Expected: **WARN**, exit 0
- Lockfiles from: exposuregate planted case uv-stale-brotli

`base/` is main; `change/` is what the change writes. See `case.json`.
