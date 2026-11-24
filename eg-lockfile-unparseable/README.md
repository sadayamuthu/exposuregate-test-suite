# eg-lockfile-unparseable

The change leaves package-lock.json as truncated JSON. A lockfile that won't parse is denied, not skipped.

- Category: fail-closed
- Modes: pr
- Expected: **DENY**, exit 2
- Denials: lockfile_parse

`base/` is main; `change/` is what the change writes. See `case.json`.
