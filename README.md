# ExposureGate Test Suite

Test projects for [ExposureGate](https://github.com/sadayamuthu/exposuregate), the pre-commit
and pull-request gate that blocks dependency versions with known, exploited vulnerabilities
(OSV advisories graded with the [OEBC](https://github.com/sadayamuthu/oebc) exposure tier). It is
the counterpart of the [ControlGate test suite](https://github.com/sadayamuthu/controlgate-test-suite).

Each `eg-*` project is a small repository in two states: `base/` (what is on `main`) and
`change/` (what a commit or pull request writes over it). `test_runner.py` builds each one as a
real git repository, runs ExposureGate the way a developer or CI would, and checks the verdict,
exit code, findings, denials and lockfile statuses against the project's `case.json`.

The suite pins **ExposureGate 0.1.0** and a **frozen data snapshot** (`data/`: OEBC built
2026-06-14, OSV PyPI and npm exports of 2026-11-13), so the results never drift with upstream
data. Scans run `--as-of 2026-11-13 --max-age-days 200` unless a project says otherwise.

## Quick start

```bash
make test                      # install exposuregate==0.1.0 in .venv, run every project and mode
make test-eg-npm-direct-kev    # one project
make test-json                 # also write results.json
```

Or with ExposureGate already on `PATH`: `python3 test_runner.py [--only eg-uv-]`.
The runner needs only Python 3.10+ and git.

## What it covers

| Area | Projects | What is checked |
|---|---|---|
| Grading, per lockfile type | `eg-{requirements,poetry,uv,npm}-{direct-kev,transitive-kev,high,low,benign}` | KEV pin → BLOCK, HIGH → WARN, LOW → PASS, transitive KEV → BLOCK (tagged `transitive`), fixed-version bump → PASS |
| Stale catalog | `eg-*-stale-oebc*` | CVEs KEV-listed after the OEBC build grade low or `not_in_oebc` (WARN), not CRITICAL |
| Policy and config | `eg-policy-*`, `eg-suppression-*`, `eg-requirements-unpinned`, `eg-unsupported-lockfile`, `eg-exclusions` | transitive cap, stricter tiers, active and expired suppressions, unpinned lines, unsupported lockfiles, excluded paths |
| Repository shapes | `eg-monorepo`, `eg-lockfile-added`, `eg-lockfile-deleted`, `eg-no-lockfile-change`, `eg-unchanged-vulnerable`, `eg-mode-full`, `eg-uv-workspace` | several lockfiles, new and deleted lockfiles, no lockfile change (no data needed), only what a change adds is graded, `--mode full`, workspace members skipped |
| Fail closed | `eg-data-*`, `eg-lockfile-unparseable`, `eg-npm-lockfile-v1`, `eg-fail-open*` | missing, stale and future data, a lockfile that won't parse or isn't supported → DENY (exit 2); `--fail-open` reports denials unenforced and never returns PASS |
| Usage errors | `eg-config-unknown-key`, `eg-not-a-git-repo` | exit 2 and no report |

Scan modes: grading, stale-catalog and most repository-shape projects run in three modes, which
must agree: `pr` (`--mode pr --target-branch main` on a change branch), `pre-commit` (a staged
change) and `refs` (`--base <main> --head <change>`). The others run in `pr` mode, and
`eg-mode-full` runs in `full` mode.

The CI workflow (`.github/workflows/suite.yml`) runs the whole suite with the CLI, and runs the
[ExposureGate GitHub Action](https://github.com/sadayamuthu/exposuregate/blob/main/action.yml)
(`sadayamuthu/exposuregate@v0.1.0`) on six projects, checking its `verdict` and `exit-code` outputs.

## Projects

<!-- projects:start -->
| Project | Category | Modes | Expected |
|---|---|---|---|
| [`eg-requirements-direct-kev`](eg-requirements-direct-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-requirements-transitive-kev`](eg-requirements-transitive-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-requirements-high`](eg-requirements-high/) | grading | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-requirements-low`](eg-requirements-low/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-requirements-benign`](eg-requirements-benign/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-poetry-direct-kev`](eg-poetry-direct-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-poetry-transitive-kev`](eg-poetry-transitive-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-poetry-high`](eg-poetry-high/) | grading | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-poetry-low`](eg-poetry-low/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-poetry-benign`](eg-poetry-benign/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-uv-direct-kev`](eg-uv-direct-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-uv-transitive-kev`](eg-uv-transitive-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-uv-high`](eg-uv-high/) | grading | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-uv-low`](eg-uv-low/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-uv-benign`](eg-uv-benign/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-npm-direct-kev`](eg-npm-direct-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-npm-transitive-kev`](eg-npm-transitive-kev/) | grading | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-npm-high`](eg-npm-high/) | grading | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-npm-low`](eg-npm-low/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-npm-benign`](eg-npm-benign/) | grading | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-requirements-stale-oebc`](eg-requirements-stale-oebc/) | stale-catalog | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-poetry-stale-oebc`](eg-poetry-stale-oebc/) | stale-catalog | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-uv-stale-oebc`](eg-uv-stale-oebc/) | stale-catalog | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-uv-stale-oebc-direct`](eg-uv-stale-oebc-direct/) | stale-catalog | pr, pre-commit, refs | WARN, exit 0 |
| [`eg-policy-transitive-cap`](eg-policy-transitive-cap/) | policy | pr | WARN, exit 0 |
| [`eg-policy-block-high`](eg-policy-block-high/) | policy | pr | BLOCK, exit 1 |
| [`eg-suppression-active`](eg-suppression-active/) | policy | pr | PASS, exit 0 |
| [`eg-suppression-expired`](eg-suppression-expired/) | policy | pr | WARN, exit 0 |
| [`eg-requirements-unpinned`](eg-requirements-unpinned/) | policy | pr | WARN, exit 0 |
| [`eg-unsupported-lockfile`](eg-unsupported-lockfile/) | policy | pr | WARN, exit 0 |
| [`eg-exclusions`](eg-exclusions/) | policy | pr | PASS, exit 0 |
| [`eg-monorepo`](eg-monorepo/) | repo-shape | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-lockfile-added`](eg-lockfile-added/) | repo-shape | pr, pre-commit, refs | BLOCK, exit 1 |
| [`eg-lockfile-deleted`](eg-lockfile-deleted/) | repo-shape | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-no-lockfile-change`](eg-no-lockfile-change/) | repo-shape | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-unchanged-vulnerable`](eg-unchanged-vulnerable/) | repo-shape | pr, pre-commit, refs | PASS, exit 0 |
| [`eg-mode-full`](eg-mode-full/) | repo-shape | full | BLOCK, exit 1 |
| [`eg-uv-workspace`](eg-uv-workspace/) | repo-shape | pr | PASS, exit 0 |
| [`eg-data-missing`](eg-data-missing/) | fail-closed | pr, pre-commit, refs | DENY, exit 2 (data_missing) |
| [`eg-data-stale`](eg-data-stale/) | fail-closed | pr | DENY, exit 2 (data_stale) |
| [`eg-data-future`](eg-data-future/) | fail-closed | pr | DENY, exit 2 (data_from_future) |
| [`eg-lockfile-unparseable`](eg-lockfile-unparseable/) | fail-closed | pr | DENY, exit 2 (lockfile_parse) |
| [`eg-npm-lockfile-v1`](eg-npm-lockfile-v1/) | fail-closed | pr | DENY, exit 2 (lockfile_unsupported) |
| [`eg-fail-open`](eg-fail-open/) | fail-closed | pr | WARN, exit 0 (data_stale) |
| [`eg-fail-open-block`](eg-fail-open-block/) | fail-closed | pr | BLOCK, exit 1 (data_stale) |
| [`eg-config-unknown-key`](eg-config-unknown-key/) | usage-error | pr | no report, exit 2 |
| [`eg-not-a-git-repo`](eg-not-a-git-repo/) | usage-error | pr | no report, exit 2 |
<!-- projects:end -->

## Where the lockfiles come from

The grading and stale-catalog projects use the lockfiles of ExposureGate's own planted-exposure
set (`tests/fixtures/planted/` at tag v0.1.0), and `data/` is a byte-for-byte copy of that set's
frozen data, checked against `data/SHA256SUMS` on every run. The other projects reuse the same
lockfiles or ExposureGate's parser fixtures. `scripts/scaffold.py` regenerates every project and
`data/` from an ExposureGate checkout:

```bash
make scaffold EG_SRC=../exposuregate    # checkout at v0.1.0
```

Expected results for the 24 grading and stale-catalog projects are taken from the planted set's
`cases.json` (verdict, exit code and the findings it names), which ExposureGate's own unit tests
also check. The other 23 projects' expectations are written in `scripts/scaffold.py` from
ExposureGate's documented behaviour. Findings are checked as a subset (the findings a case names
must be present) unless the case sets `exact_findings`. A failing case is a finding about the
tool or the case.

Each grading case's reason (why that version, which CVE) is in its `case.json` `summary` and
`README.md`. The planted versions are real releases with real advisories: don't install them.

## Not covered

- The pre-commit framework hook (`.pre-commit-hooks.yaml`): it runs `exposuregate scan --mode
  pre-commit` with no data arguments, so it needs `update-data` and network access. The runner
  covers the same `--mode pre-commit` scan with frozen data.
- `update-data`, `data-info` and `rebuild-oebc`, which download or rebuild data.
- Ecosystems other than PyPI and npm, which ExposureGate 0.1.0 does not grade.

## License

MIT. See [LICENSE](LICENSE).
