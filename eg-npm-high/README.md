# eg-npm-high

minimist 1.2.5: last release before the fix (1.2.6) for CVE-2021-44906, its only finding (HIGH).

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **WARN**, exit 0
- Lockfiles from: exposuregate planted case npm-high

`base/` is main; `change/` is what the change writes. See `case.json`.
