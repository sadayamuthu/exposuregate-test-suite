# eg-requirements-transitive-kev

starlette (via fastapi) has no CRITICAL CVE in the frozen OEBC: its only KEV CVE, CVE-2026-48710, was KEV-listed 2026-09-02, after the 2026-06-14 OEBC build, which grades it LOW (see the stale-starlette case). pillow via matplotlib is used instead: pillow 10.0.0 is the last release before the fix (10.0.1) for KEV-listed CVE-2023-4863 (libwebp, CRITICAL); matplotlib 3.8.0 has no advisories.

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **BLOCK**, exit 1
- Lockfiles from: exposuregate planted case requirements-transitive-kev

`base/` is main; `change/` is what the change writes. See `case.json`.
