# eg-npm-lockfile-v1

A package-lock.json with lockfileVersion 1, which ExposureGate does not read. It is denied rather than passed.

- Category: fail-closed
- Modes: pr
- Expected: **DENY**, exit 2
- Denials: lockfile_unsupported
- Lockfiles from: exposuregate fixture tests/fixtures/lockfiles/npm/v1/package-lock.json

`base/` is main; `change/` is what the change writes. See `case.json`.
