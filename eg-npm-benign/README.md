# eg-npm-benign

lodash 4.18.0 -> 4.18.1, the fixed version of CVE-2026-2950 (LOW); 4.18.1 has no advisories.

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **PASS**, exit 0
- Lockfiles from: exposuregate planted case npm-benign

`base/` is main; `change/` is what the change writes. See `case.json`.
