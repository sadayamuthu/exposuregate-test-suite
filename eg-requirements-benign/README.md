# eg-requirements-benign

requests 2.32.5 -> 2.33.0, the fixed version of CVE-2026-25645 (LOW); 2.33.0 has no advisories.

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **PASS**, exit 0
- Lockfiles from: exposuregate planted case requirements-benign

`base/` is main; `change/` is what the change writes. See `case.json`.
