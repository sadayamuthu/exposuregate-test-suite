# eg-monorepo

Two services change in one pull request: a HIGH pin in a uv.lock and a KEV pin in a package-lock.json. Both are graded; the verdict is the worst.

- Category: repo-shape
- Modes: pr, pre-commit, refs
- Expected: **BLOCK**, exit 1

`base/` is main; `change/` is what the change writes. See `case.json`.
