# eg-npm-direct-kev

vite 6.2.3: last 6.2.x release before the fix (6.2.4) for KEV-listed CVE-2025-31125 (CRITICAL); a devDependency, so the finding carries dev_only.

- Category: grading
- Modes: pr, pre-commit, refs
- Expected: **BLOCK**, exit 1
- Lockfiles from: exposuregate planted case npm-direct-kev

`base/` is main; `change/` is what the change writes. See `case.json`.
