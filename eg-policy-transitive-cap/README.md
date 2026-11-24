# eg-policy-transitive-cap

A transitive KEV pin (pillow 10.0.0 via matplotlib) with policy.transitive_max_action: warn. The cap turns the BLOCK into a WARN.

- Category: policy
- Modes: pr
- Expected: **WARN**, exit 0
- Lockfiles from: exposuregate planted case uv-transitive-kev

`base/` is main; `change/` is what the change writes. See `case.json`.
