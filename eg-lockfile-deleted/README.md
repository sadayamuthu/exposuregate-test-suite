# eg-lockfile-deleted

The change deletes a lockfile that pins a KEV version. Removing a dependency adds nothing, so it passes.

- Category: repo-shape
- Modes: pr, pre-commit, refs
- Expected: **PASS**, exit 0

`base/` is main; `change/` is what the change writes. See `case.json`.
