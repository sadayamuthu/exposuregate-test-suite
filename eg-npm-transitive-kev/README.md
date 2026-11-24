# eg-npm-transitive-kev

jquery 3.4.1 nested under jquery-ui 1.13.2 (no advisories): last release before the fix (3.5.0) for KEV-listed CVE-2020-11023 (CRITICAL).

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **BLOCK**, exit 1
- Lockfiles from: exposuregate planted case npm-transitive-kev

`base/` is main; `change/` is what the change writes. See `case.json`.
