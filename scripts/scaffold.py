#!/usr/bin/env python3
"""Generate the eg-* test projects and copy the frozen data.

Usage: python3 scripts/scaffold.py /path/to/exposuregate   (a checkout at tag v0.1.0)

Every lockfile comes from ExposureGate's planted-exposure set
(tests/fixtures/planted/cases/*) or its lockfile parser fixtures (tests/fixtures/lockfiles/*),
so the suite and the tool's own tests grade the same versions against the same frozen data.
Each project gets:

  base/        files committed on main
  change/      files the change writes over base (a new branch, a staged change, or a commit)
  case.json    how to run the scan and what it must return
  README.md    generated from case.json

Re-running overwrites every eg-* directory and data/. Expected results are written here, by
hand, from ExposureGate's documented behaviour; test_runner.py checks them, and a mismatch is
a finding about the tool or the case, never something to "fix" by copying the tool's output.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOCKFILE = {
    "requirements": "requirements.txt",
    "poetry": "poetry.lock",
    "uv": "uv.lock",
    "npm": "package-lock.json",
}
GRADING = ["direct-kev", "transitive-kev", "high", "low", "benign"]
GRADED_MODES = ["pr", "pre-commit", "refs"]
STALE = {
    "requirements-stale-starlette": "eg-requirements-stale-oebc",
    "poetry-stale-starlette": "eg-poetry-stale-oebc",
    "uv-stale-starlette": "eg-uv-stale-oebc",
    "uv-stale-brotli": "eg-uv-stale-oebc-direct",
}

APP_PY = 'def main() -> None:\n    print("hello")\n'
APP_PY_CHANGED = 'def main() -> None:\n    print("hello, world")\n'


class Scaffold:
    def __init__(self, eg: Path) -> None:
        self.eg = eg
        self.planted = eg / "tests" / "fixtures" / "planted"
        self.spec = json.loads((self.planted / "cases.json").read_text())
        self.cases = {c["id"]: c for c in self.spec["cases"]}
        self.made: list[dict] = []

    # -- inputs ---------------------------------------------------------------------------
    def lock(self, case_id: str, side: str) -> str:
        c = self.cases[case_id]
        return (self.planted / c[side]).read_text()

    def manifest(self, case_id: str) -> str | None:
        m = self.cases[case_id].get("manifest")
        return (self.planted / m).read_text() if m else None

    def findings(self, case_id: str) -> list[dict]:
        keep = ("package", "version", "cve_id", "reason", "dependency", "action")
        return [{k: f[k] for k in keep if k in f} for f in self.cases[case_id]["expected_findings"]]

    # -- output ---------------------------------------------------------------------------
    def project(
        self,
        name: str,
        *,
        category: str,
        summary: str,
        base: dict[str, str],
        change: dict[str, str],
        expect: dict,
        modes: list[str] | None = None,
        delete: list[str] | None = None,
        data: str = "frozen",
        args: list[str] | None = None,
        git: bool = True,
        source: str | None = None,
    ) -> None:
        d = ROOT / name
        if d.exists():
            shutil.rmtree(d)
        for side, files in (("base", base), ("change", change)):
            (d / side).mkdir(parents=True)
            (d / side / ".keep").write_text("")
            for rel, text in files.items():
                p = d / side / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
        case = {
            "id": name,
            "category": category,
            "summary": summary,
            "source": source,
            "git": git,
            "modes": modes or ["pr"],
            "delete": delete or [],
            "data": data,
            "args": args if args is not None else list(self.spec["scan_args"]),
            "expect": expect,
        }
        (d / "case.json").write_text(json.dumps(case, indent=2) + "\n")
        (d / "README.md").write_text(readme(case))
        self.made.append(case)

    # -- projects -------------------------------------------------------------------------
    def grading(self) -> None:
        for eco, fname in LOCKFILE.items():
            for kind in GRADING:
                cid = f"{eco}-{kind}"
                c = self.cases[cid]
                base = {fname: self.lock(cid, "old"), "app.py": APP_PY}
                change = {fname: self.lock(cid, "new")}
                if (m := self.manifest(cid)) is not None:
                    base["pyproject.toml"] = m
                    change["pyproject.toml"] = m
                self.project(
                    f"eg-{eco}-{kind}",
                    category="grading",
                    summary=c["why"],
                    base=base,
                    change=change,
                    modes=GRADED_MODES,
                    source=f"exposuregate planted case {cid}",
                    expect={
                        "verdict": c["expected_verdict"],
                        "exit_code": c["expected_exit_code"],
                        "denials": [],
                        "findings": self.findings(cid),
                        "exact_findings": c.get("exact_findings", False),
                    },
                )
        for cid, name in STALE.items():
            c = self.cases[cid]
            fname = LOCKFILE[c["lockfile_type"]]
            base = {fname: self.lock(cid, "old"), "app.py": APP_PY}
            change = {fname: self.lock(cid, "new")}
            if (m := self.manifest(cid)) is not None:
                base["pyproject.toml"] = m
                change["pyproject.toml"] = m
            self.project(
                name,
                category="stale-catalog",
                summary=c["why"],
                base=base,
                change=change,
                modes=GRADED_MODES,
                source=f"exposuregate planted case {cid}",
                expect={
                    "verdict": c["expected_verdict"],
                    "exit_code": c["expected_exit_code"],
                    "denials": [],
                    "findings": self.findings(cid),
                    "exact_findings": False,
                },
            )

    def policy(self) -> None:
        req_high_old = self.lock("requirements-high", "old")
        req_high_new = self.lock("requirements-high", "new")
        req_kev_old = self.lock("requirements-direct-kev", "old")
        req_kev_new = self.lock("requirements-direct-kev", "new")
        pyyaml = {"package": "pyyaml", "version": "5.3.1", "cve_id": "CVE-2020-14343"}

        self.project(
            "eg-policy-transitive-cap",
            category="policy",
            summary="A transitive KEV pin (pillow 10.0.0 via matplotlib) with "
            "policy.transitive_max_action: warn. The cap turns the BLOCK into a WARN.",
            base={
                "uv.lock": self.lock("uv-transitive-kev", "old"),
                ".exposuregate.yml": "policy:\n  transitive_max_action: warn\n",
            },
            change={"uv.lock": self.lock("uv-transitive-kev", "new")},
            source="exposuregate planted case uv-transitive-kev",
            expect={
                "verdict": "WARN",
                "exit_code": 0,
                "denials": [],
                "findings": [
                    {"package": "pillow", "version": "10.0.0", "cve_id": "CVE-2023-4863",
                     "dependency": "transitive", "base_action": "block", "action": "warn"}
                ],
            },
        )
        self.project(
            "eg-policy-block-high",
            category="policy",
            summary="A HIGH-tier pin (pyyaml 5.3.1) with policy.HIGH: block. "
            "The stricter policy turns the default WARN into a BLOCK.",
            base={"requirements.txt": req_high_old, ".exposuregate.yml": "policy:\n  HIGH: block\n"},
            change={"requirements.txt": req_high_new},
            source="exposuregate planted case requirements-high",
            expect={
                "verdict": "BLOCK",
                "exit_code": 1,
                "denials": [],
                "findings": [{**pyyaml, "reason": "graded", "action": "block"}],
            },
        )
        self.project(
            "eg-suppression-active",
            category="policy",
            summary="The HIGH finding for pyyaml 5.3.1 is suppressed with a reason and an "
            "expiry in the future. The finding is still reported, with action pass.",
            base={
                "requirements.txt": req_high_old,
                ".exposuregate.yml": (
                    "suppressions:\n"
                    "  - id: CVE-2020-14343\n"
                    "    package: pyyaml\n"
                    "    reason: \"test suite: only safe_load is called\"\n"
                    "    expires: 2099-12-31\n"
                ),
            },
            change={"requirements.txt": req_high_new},
            source="exposuregate planted case requirements-high",
            expect={
                "verdict": "PASS",
                "exit_code": 0,
                "denials": [],
                "findings": [{**pyyaml, "base_action": "warn", "action": "pass",
                              "suppressed": True}],
                "expired_suppressions": 0,
            },
        )
        self.project(
            "eg-suppression-expired",
            category="policy",
            summary="The same suppression, expired on 2026-01-01 (the scan runs as of "
            "2026-11-13). It no longer applies, and the expiry is itself reported.",
            base={
                "requirements.txt": req_high_old,
                ".exposuregate.yml": (
                    "suppressions:\n"
                    "  - id: CVE-2020-14343\n"
                    "    package: pyyaml\n"
                    "    reason: \"test suite: only safe_load is called\"\n"
                    "    expires: 2026-01-01\n"
                ),
            },
            change={"requirements.txt": req_high_new},
            source="exposuregate planted case requirements-high",
            expect={
                "verdict": "WARN",
                "exit_code": 0,
                "denials": [],
                "findings": [{**pyyaml, "action": "warn", "suppressed": False},
                             {"reason": "suppression_expired", "action": "warn"}],
                "expired_suppressions": 1,
            },
        )
        self.project(
            "eg-requirements-unpinned",
            category="policy",
            summary="A requirements line with a range (requests>=2.0) instead of an == pin. "
            "It can't be graded, so it warns (policy.unpinned).",
            base={"requirements.txt": "click==8.1.7\n"},
            change={"requirements.txt": "click==8.1.7\nrequests>=2.0\n"},
            expect={
                "verdict": "WARN",
                "exit_code": 0,
                "denials": [],
                "findings": [{"package": "requests", "reason": "unpinned", "action": "warn"}],
            },
        )
        self.project(
            "eg-unsupported-lockfile",
            category="policy",
            summary="The change adds a yarn.lock, which ExposureGate can't parse. It warns "
            "(policy.unsupported_lockfile) instead of passing silently.",
            base={"app.py": APP_PY},
            change={"yarn.lock": "# yarn lockfile v1\n\n\nleft-pad@^1.3.0:\n  version \"1.3.0\"\n"},
            expect={
                "verdict": "WARN",
                "exit_code": 0,
                "denials": [],
                "findings": [{"reason": "unsupported_lockfile", "action": "warn"}],
                "lockfiles": {"yarn.lock": "unsupported"},
            },
        )
        self.project(
            "eg-exclusions",
            category="policy",
            summary="A KEV pin in examples/demo/requirements.txt, excluded with "
            "exclusions.paths: [examples/*]. The file is listed as excluded and nothing is graded.",
            base={
                "examples/demo/requirements.txt": req_kev_old,
                ".exposuregate.yml": "exclusions:\n  paths: [\"examples/*\"]\n",
            },
            change={"examples/demo/requirements.txt": req_kev_new},
            expect={
                "verdict": "PASS",
                "exit_code": 0,
                "denials": [],
                "findings": [],
                "exact_findings": True,
                "lockfiles": {"examples/demo/requirements.txt": "excluded"},
            },
        )

    def repo_shapes(self) -> None:
        req_kev_old = self.lock("requirements-direct-kev", "old")
        req_kev_new = self.lock("requirements-direct-kev", "new")
        litellm = {"package": "litellm", "version": "1.83.6", "cve_id": "CVE-2026-42208",
                   "action": "block"}

        self.project(
            "eg-monorepo",
            category="repo-shape",
            summary="Two services change in one pull request: a HIGH pin in a uv.lock and a "
            "KEV pin in a package-lock.json. Both are graded; the verdict is the worst.",
            base={
                "services/api/uv.lock": self.lock("uv-high", "old"),
                "services/web/package-lock.json": self.lock("npm-direct-kev", "old"),
            },
            change={
                "services/api/uv.lock": self.lock("uv-high", "new"),
                "services/web/package-lock.json": self.lock("npm-direct-kev", "new"),
            },
            modes=GRADED_MODES,
            expect={
                "verdict": "BLOCK",
                "exit_code": 1,
                "denials": [],
                "findings": [
                    {"package": "pyyaml", "version": "5.3.1", "cve_id": "CVE-2020-14343",
                     "action": "warn", "lockfile": "services/api/uv.lock"},
                    {"package": "vite", "version": "6.2.3", "cve_id": "CVE-2025-31125",
                     "action": "block", "lockfile": "services/web/package-lock.json"},
                ],
                "lockfiles": {"services/api/uv.lock": "graded",
                              "services/web/package-lock.json": "graded"},
            },
        )
        self.project(
            "eg-lockfile-added",
            category="repo-shape",
            summary="The change adds the project's first lockfile, which pins a KEV version. "
            "Every pin in a new lockfile counts as added.",
            base={"app.py": APP_PY},
            change={"requirements.txt": req_kev_new},
            modes=GRADED_MODES,
            expect={"verdict": "BLOCK", "exit_code": 1, "denials": [], "findings": [litellm]},
        )
        self.project(
            "eg-lockfile-deleted",
            category="repo-shape",
            summary="The change deletes a lockfile that pins a KEV version. Removing a "
            "dependency adds nothing, so it passes.",
            base={"requirements.txt": req_kev_new, "app.py": APP_PY},
            change={},
            delete=["requirements.txt"],
            modes=GRADED_MODES,
            expect={"verdict": "PASS", "exit_code": 0, "denials": [], "findings": [],
                    "exact_findings": True},
        )
        self.project(
            "eg-no-lockfile-change",
            category="repo-shape",
            summary="The change edits only app.py, and there is no data at all. A change "
            "that touches no lockfile needs no data and passes quickly.",
            base={"requirements.txt": req_kev_new, "app.py": APP_PY},
            change={"app.py": APP_PY_CHANGED},
            data="empty",
            args=[],
            modes=GRADED_MODES,
            expect={"verdict": "PASS", "exit_code": 0, "denials": [], "findings": [],
                    "exact_findings": True},
        )
        unchanged_base = "litellm==1.83.6\nrequests==2.32.5\n"
        unchanged_new = "litellm==1.83.6\nrequests==2.33.0\n"
        self.project(
            "eg-unchanged-vulnerable",
            category="repo-shape",
            summary="main already pins a KEV version (litellm 1.83.6); the change only bumps "
            "requests to a fixed version. The gate grades what a change adds, so it passes.",
            base={"requirements.txt": unchanged_base},
            change={"requirements.txt": unchanged_new},
            modes=GRADED_MODES,
            expect={"verdict": "PASS", "exit_code": 0, "denials": [], "findings": [],
                    "exact_findings": True},
        )
        self.project(
            "eg-mode-full",
            category="repo-shape",
            summary="The same repository scanned with --mode full, which grades every pin. "
            "The KEV pin that the pull request scan leaves alone now blocks.",
            base={"requirements.txt": unchanged_base},
            change={"requirements.txt": unchanged_new},
            modes=["full"],
            expect={"verdict": "BLOCK", "exit_code": 1, "denials": [], "findings": [litellm]},
        )
        ws = self.eg / "tests" / "fixtures" / "lockfiles" / "uv" / "workspace" / "uv.lock"
        self.project(
            "eg-uv-workspace",
            category="repo-shape",
            summary="A uv workspace lockfile: its editable and virtual members are listed under "
            "skipped, not graded.",
            base={"app.py": APP_PY},
            change={"uv.lock": ws.read_text()},
            source="exposuregate fixture tests/fixtures/lockfiles/uv/workspace/uv.lock",
            expect={"verdict": "PASS", "exit_code": 0, "denials": [], "skipped_min": 1},
        )

    def fail_closed(self) -> None:
        req_kev_old = self.lock("requirements-direct-kev", "old")
        req_kev_new = self.lock("requirements-direct-kev", "new")
        ben_old = self.lock("requirements-benign", "old")
        ben_new = self.lock("requirements-benign", "new")
        no_age = ["--as-of", "2026-11-13"]

        self.project(
            "eg-data-missing",
            category="fail-closed",
            summary="A lockfile changes but there is no data directory index. "
            "The gate denies instead of passing.",
            base={"requirements.txt": req_kev_old},
            change={"requirements.txt": req_kev_new},
            data="empty",
            args=[],
            modes=GRADED_MODES,
            expect={"verdict": "DENY", "exit_code": 2, "denials": ["data_missing"]},
        )
        self.project(
            "eg-data-stale",
            category="fail-closed",
            summary="Frozen data with the default 7-day limit: OEBC (built 2026-06-14) is 152 "
            "days old on 2026-11-13, so the scan is denied.",
            base={"requirements.txt": ben_old},
            change={"requirements.txt": ben_new},
            args=no_age,
            expect={"verdict": "DENY", "exit_code": 2, "denials": ["data_stale"]},
        )
        self.project(
            "eg-data-future",
            category="fail-closed",
            summary="The scan runs as of 2026-06-30, before the OSV export (2026-11-13) was "
            "made. Data from the future is denied.",
            base={"requirements.txt": ben_old},
            change={"requirements.txt": ben_new},
            args=["--as-of", "2026-06-30", "--max-age-days", "200"],
            expect={"verdict": "DENY", "exit_code": 2, "denials": ["data_from_future"]},
        )
        self.project(
            "eg-lockfile-unparseable",
            category="fail-closed",
            summary="The change leaves package-lock.json as truncated JSON. A lockfile that "
            "won't parse is denied, not skipped.",
            base={"package-lock.json": self.lock("npm-benign", "old")},
            change={"package-lock.json": '{\n  "name": "planted-app",\n  "lockfileVersion": 3,\n  "packages": {\n'},
            expect={"verdict": "DENY", "exit_code": 2, "denials": ["lockfile_parse"]},
        )
        v1 = self.eg / "tests" / "fixtures" / "lockfiles" / "npm" / "v1" / "package-lock.json"
        self.project(
            "eg-npm-lockfile-v1",
            category="fail-closed",
            summary="A package-lock.json with lockfileVersion 1, which ExposureGate does not "
            "read. It is denied rather than passed.",
            base={"app.py": APP_PY},
            change={"package-lock.json": v1.read_text()},
            source="exposuregate fixture tests/fixtures/lockfiles/npm/v1/package-lock.json",
            expect={"verdict": "DENY", "exit_code": 2, "denials": ["lockfile_unsupported"]},
        )
        self.project(
            "eg-fail-open",
            category="fail-closed",
            summary="Stale data with --fail-open: the denial is reported with enforced: false, "
            "and the verdict is WARN, never PASS, even for a benign bump.",
            base={"requirements.txt": ben_old},
            change={"requirements.txt": ben_new},
            args=[*no_age, "--fail-open"],
            expect={"verdict": "WARN", "exit_code": 0, "denials": ["data_stale"],
                    "denials_enforced": False},
        )
        self.project(
            "eg-fail-open-block",
            category="fail-closed",
            summary="Stale data with --fail-open and a KEV pin: findings are still graded, "
            "so the KEV pin still blocks.",
            base={"requirements.txt": req_kev_old},
            change={"requirements.txt": req_kev_new},
            args=[*no_age, "--fail-open"],
            expect={"verdict": "BLOCK", "exit_code": 1, "denials": ["data_stale"],
                    "denials_enforced": False,
                    "findings": [{"package": "litellm", "version": "1.83.6",
                                  "cve_id": "CVE-2026-42208", "action": "block"}]},
        )

    def usage(self) -> None:
        self.project(
            "eg-config-unknown-key",
            category="usage-error",
            summary="A misspelled config key (polcy). Every key changes behaviour, so an "
            "unknown one is an error (exit 2, no report), not ignored.",
            base={"requirements.txt": "click==8.1.7\n", ".exposuregate.yml": "polcy:\n  HIGH: block\n"},
            change={"requirements.txt": "click==8.1.7\nrequests==2.33.0\n"},
            expect={"verdict": None, "exit_code": 2},
        )
        self.project(
            "eg-not-a-git-repo",
            category="usage-error",
            summary="A pull-request scan in a directory that is not a git repository "
            "(exit 2, no report).",
            base={"requirements.txt": "click==8.1.7\n"},
            change={},
            git=False,
            expect={"verdict": None, "exit_code": 2},
        )

    def data(self) -> None:
        src = self.planted / "data"
        dst = ROOT / "data"
        if dst.exists():
            shutil.rmtree(dst)
        (dst / "osv").mkdir(parents=True)
        files = ["oebc.json", "osv/PyPI.zip", "osv/npm.zip", "provenance.json"]
        for rel in files:
            shutil.copyfile(src / rel, dst / rel)
        sums = "".join(
            f"{hashlib.sha256((dst / rel).read_bytes()).hexdigest()}  {rel}\n" for rel in files
        )
        (dst / "SHA256SUMS").write_text(sums)
        (dst / "scan_args.json").write_text(json.dumps(self.spec["scan_args"]) + "\n")


def readme(case: dict) -> str:
    e = case["expect"]
    verdict = e["verdict"] or "no report"
    lines = [
        f"# {case['id']}",
        "",
        case["summary"],
        "",
        f"- Category: {case['category']}",
        f"- Modes: {', '.join(case['modes'])}",
        f"- Expected: **{verdict}**, exit {e['exit_code']}",
    ]
    if e.get("denials"):
        lines.append(f"- Denials: {', '.join(e['denials'])}")
    if case["source"]:
        lines.append(f"- Lockfiles from: {case['source']}")
    lines += ["", "`base/` is main; `change/` is what the change writes. See `case.json`.", ""]
    return "\n".join(lines)


def update_readme(cases: list[dict]) -> None:
    rows = ["| Project | Category | Modes | Expected |", "|---|---|---|---|"]
    for c in cases:
        e = c["expect"]
        exp = f"{e['verdict'] or 'no report'}, exit {e['exit_code']}"
        if e.get("denials"):
            exp += f" ({', '.join(e['denials'])})"
        rows.append(f"| [`{c['id']}`]({c['id']}/) | {c['category']} | {', '.join(c['modes'])} | {exp} |")
    path = ROOT / "README.md"
    text = path.read_text()
    start, end = "<!-- projects:start -->", "<!-- projects:end -->"
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    path.write_text(f"{head}{start}\n" + "\n".join(rows) + f"\n{end}{tail}")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    s = Scaffold(Path(sys.argv[1]).resolve())
    s.grading()
    s.policy()
    s.repo_shapes()
    s.fail_closed()
    s.usage()
    s.data()
    index = [{"id": c["id"], "category": c["category"], "modes": c["modes"],
              "verdict": c["expect"]["verdict"], "exit_code": c["expect"]["exit_code"]}
             for c in s.made]
    (ROOT / "cases.json").write_text(json.dumps(index, indent=2) + "\n")
    update_readme(s.made)
    print(f"wrote {len(s.made)} projects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
