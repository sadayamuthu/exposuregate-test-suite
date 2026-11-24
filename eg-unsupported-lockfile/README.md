# eg-unsupported-lockfile

The change adds a yarn.lock, which ExposureGate can't parse. It warns (policy.unsupported_lockfile) instead of passing silently.

- Category: policy
- Modes: pr
- Expected: **WARN**, exit 0

`base/` is main; `change/` is what the change writes. See `case.json`.
