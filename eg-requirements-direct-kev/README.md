# eg-requirements-direct-kev

litellm 1.83.6: highest final release matched by the KEV-listed CVE-2026-42208 and CVE-2026-42271 (CRITICAL in the 2026-06-14 OEBC); it also has HIGH/MEDIUM/LOW, not_in_oebc and no_cve findings.

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **BLOCK**, exit 1
- Lockfiles from: exposuregate planted case requirements-direct-kev

`base/` is main; `change/` is what the change writes. See `case.json`.
