# eg-uv-stale-oebc

Documents OEBC staleness: CVE-2026-48710 was KEV-listed 2026-09-02, after the 2026-06-14 OEBC build, so it grades LOW (pass) instead of CRITICAL (block). The WARN comes from newer CVEs not in that OEBC (not_in_oebc). fastapi 0.115.6 has no advisories; starlette 0.41.3 satisfies its starlette<0.42 pin.

- Category: stale-catalog
- Modes: pr, pre-commit, refs
- Expected: **WARN**, exit 0
- Lockfiles from: exposuregate planted case uv-stale-starlette

`base/` is main; `change/` is what the change writes. See `case.json`.
