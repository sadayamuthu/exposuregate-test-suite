# eg-no-lockfile-change

The change edits only app.py, and there is no data at all. A change that touches no lockfile needs no data and passes quickly.

- Category: repo-shape
- Modes: pr, pre-commit, refs
- Expected: **PASS**, exit 0

`base/` is main; `change/` is what the change writes. See `case.json`.
