# eg-policy-block-high

A HIGH-tier pin (pyyaml 5.3.1) with policy.HIGH: block. The stricter policy turns the default WARN into a BLOCK.

- Category: policy
- Modes: pr
- Expected: **BLOCK**, exit 1
- Lockfiles from: exposuregate planted case requirements-high

`base/` is main; `change/` is what the change writes. See `case.json`.
