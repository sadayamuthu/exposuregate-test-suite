# eg-requirements-high

pyyaml 5.3.1: highest final release whose only finding is HIGH (CVE-2020-14343).

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **WARN**, exit 0
- Lockfiles from: exposuregate planted case requirements-high

`base/` is main; `change/` is what the change writes. See `case.json`.
