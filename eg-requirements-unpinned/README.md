# eg-requirements-unpinned

A requirements line with a range (requests>=2.0) instead of an == pin. It can't be graded, so it warns (policy.unpinned).

- Category: policy
- Modes: pr
- Expected: **WARN**, exit 0

`base/` is main; `change/` is what the change writes. See `case.json`.
