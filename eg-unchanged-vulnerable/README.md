# eg-unchanged-vulnerable

main already pins a KEV version (litellm 1.83.6); the change only bumps requests to a fixed version. The gate grades what a change adds, so it passes.

- Category: repo-shape
- Modes: pr, pre-commit, refs
- Expected: **PASS**, exit 0

`base/` is main; `change/` is what the change writes. See `case.json`.
