#!/usr/bin/env python3
"""Run ExposureGate on every eg-* project and check each result against its case.json.

  python3 test_runner.py                       all projects, all of their modes
  python3 test_runner.py --only eg-npm-        projects whose id starts with a prefix
  python3 test_runner.py --json results.json   also write machine-readable results
  python3 test_runner.py --materialize eg-uv-high /tmp/repo
                                               build one project's git repo in pull-request
                                               state (main + a change branch), for the
                                               GitHub Action job, then stop

Each project is built as a throwaway git repository: base/ is committed on main, and change/
(plus case.json's "delete" list) is applied as

  pr          a commit on a branch, scanned with --mode pr --target-branch main
  pre-commit  a staged change, scanned with --mode pre-commit
  refs        a commit, scanned with --base <main> --head <change>
  full        a commit, scanned with --mode full

Scans read the frozen data in data/ (checked against data/SHA256SUMS) and never the network or
~/.cache. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "suite", "GIT_AUTHOR_EMAIL": "suite@example.invalid",
    "GIT_COMMITTER_NAME": "suite", "GIT_COMMITTER_EMAIL": "suite@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


def verify_data() -> None:
    for line in (DATA / "SHA256SUMS").read_text().splitlines():
        digest, rel = line.split(maxsplit=1)
        got = hashlib.sha256((DATA / rel).read_bytes()).hexdigest()
        if got != digest:
            sys.exit(f"data/{rel}: sha256 {got} does not match data/SHA256SUMS")


def load_cases(only: str | None) -> list[dict[str, Any]]:
    cases = [json.loads(p.read_text()) for p in sorted(ROOT.glob("eg-*/case.json"))]
    return [c for c in cases if not only or c["id"].startswith(only)]


def git(repo: Path, *args: str) -> str:
    env = {**os.environ, **GIT_ENV}
    out = subprocess.run(["git", "-C", str(repo), *args], check=True, env=env,
                         capture_output=True, text=True)
    return out.stdout.strip()


def copy_tree(src: Path, dst: Path) -> None:
    for p in src.rglob("*"):
        if p.is_file() and p.name != ".keep":
            t = dst / p.relative_to(src)
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, t)


def apply_change(case: dict[str, Any], repo: Path) -> None:
    copy_tree(ROOT / case["id"] / "change", repo)
    for rel in case["delete"]:
        (repo / rel).unlink()


def build(case: dict[str, Any], repo: Path, mode: str) -> list[str]:
    """Create the repository for one mode and return the mode's scan arguments."""
    repo.mkdir(parents=True)
    copy_tree(ROOT / case["id"] / "base", repo)
    if not case["git"]:
        return ["--mode", "pr", "--target-branch", "main"]
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", "base")
    base_sha = git(repo, "rev-parse", "HEAD")
    if mode == "pre-commit":
        apply_change(case, repo)
        git(repo, "add", "-A")
        return ["--mode", "pre-commit"]
    git(repo, "switch", "-q", "-c", "change")
    apply_change(case, repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", "change")
    if mode == "pr":
        return ["--mode", "pr", "--target-branch", "main"]
    if mode == "refs":
        return ["--base", base_sha, "--head", git(repo, "rev-parse", "HEAD")]
    if mode == "full":
        return ["--mode", "full"]
    raise ValueError(f"unknown mode {mode}")


def data_args(case: dict[str, Any], empty: Path) -> list[str]:
    if case["data"] == "frozen":
        return ["--oebc", str(DATA / "oebc.json"), "--osv-dir", str(DATA / "osv")]
    return ["--data-dir", str(empty)]


def check(case: dict[str, Any], code: int, report: dict[str, Any] | None) -> list[str]:
    e = case["expect"]
    errs: list[str] = []
    if code != e["exit_code"]:
        errs.append(f"exit code {code}, expected {e['exit_code']}")
    if e["verdict"] is None:
        if report is not None:
            errs.append(f"expected no report, got verdict {report.get('verdict')}")
        return errs
    if report is None:
        return errs + ["no JSON report on stdout"]
    if report["verdict"] != e["verdict"]:
        errs.append(f"verdict {report['verdict']}, expected {e['verdict']}")

    if "denials" in e:
        got = sorted({d["code"] for d in report["denials"]})
        if got != sorted(set(e["denials"])):
            errs.append(f"denials {got}, expected {sorted(set(e['denials']))}")
    if "denials_enforced" in e:
        bad = [d["code"] for d in report["denials"] if d["enforced"] != e["denials_enforced"]]
        if bad:
            errs.append(f"denials {bad} have enforced != {e['denials_enforced']}")

    findings = report["findings"]
    for exp in e.get("findings", []):
        want = {k: v for k, v in exp.items() if k != "suppressed"}
        hits = [f for f in findings if all(f.get(k) == v for k, v in want.items())]
        if "suppressed" in exp:
            hits = [f for f in hits if (f.get("suppressed_by") is not None) == exp["suppressed"]]
        if not hits:
            errs.append(f"no finding matching {exp}")
    if e.get("exact_findings") and not e.get("findings"):
        if findings:
            errs.append(f"expected no findings, got {len(findings)}")

    for path, status in e.get("lockfiles", {}).items():
        got = {lf["path"]: lf["status"] for lf in report["lockfiles"]}
        if got.get(path) != status:
            errs.append(f"lockfile {path}: status {got.get(path)}, expected {status}")
    if "skipped_min" in e and len(report["skipped"]) < e["skipped_min"]:
        errs.append(f"{len(report['skipped'])} skipped entries, expected >= {e['skipped_min']}")
    if "expired_suppressions" in e and len(report["expired_suppressions"]) != e["expired_suppressions"]:
        errs.append(f"{len(report['expired_suppressions'])} expired suppressions, "
                    f"expected {e['expired_suppressions']}")
    return errs


def run_one(case: dict[str, Any], mode: str, exe: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="eg-suite-") as tmp:
        repo, empty = Path(tmp) / "repo", Path(tmp) / "empty-data"
        empty.mkdir()
        argv = [exe, "scan", *build(case, repo, mode), "--path", str(repo),
                "--format", "json", *data_args(case, empty), *case["args"]]
        env = {**os.environ, **GIT_ENV, "EXPOSUREGATE_DATA_DIR": str(empty)}
        proc = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=repo)
        try:
            report = json.loads(proc.stdout) if proc.stdout.strip() else None
        except json.JSONDecodeError:
            report = None
        errs = check(case, proc.returncode, report)
        keep = ("lockfile", "package", "version", "dependency", "reason", "cve_id",
                "exposure_tier", "base_action", "action")
        return {
            "id": case["id"], "category": case["category"], "mode": mode, "ok": not errs,
            "errors": errs, "exit_code": proc.returncode,
            "verdict": report["verdict"] if report else None,
            "expected": case["expect"]["verdict"],
            "stderr": proc.stderr.strip().splitlines()[-3:] if errs else [],
            "report": None if report is None else {
                "summary": report["summary"],
                "timing_ms": report["timing_ms"],
                "denials": report["denials"],
                "lockfiles": report["lockfiles"],
                "findings": [{k: f.get(k) for k in keep} for f in report["findings"]],
            },
        }


def materialize(case_id: str, dest: Path) -> None:
    case = json.loads((ROOT / case_id / "case.json").read_text())
    if dest.exists():
        sys.exit(f"{dest} already exists")
    build(case, dest, "pr")
    git(dest, "switch", "-q", "change")
    print(json.dumps({"verdict": case["expect"]["verdict"],
                      "exit_code": case["expect"]["exit_code"],
                      "data": case["data"], "args": case["args"]}))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="run projects whose id starts with this prefix")
    ap.add_argument("--json", type=Path, help="write results to this file")
    ap.add_argument("--exposuregate", default=shutil.which("exposuregate") or "exposuregate",
                    help="the exposuregate executable (default: on PATH)")
    ap.add_argument("--materialize", nargs=2, metavar=("ID", "DIR"))
    a = ap.parse_args()
    if os.sep in a.exposuregate:  # scans run with the temp repo as cwd
        a.exposuregate = str(Path(a.exposuregate).resolve())
    verify_data()
    if a.materialize:
        materialize(a.materialize[0], Path(a.materialize[1]))
        return 0

    version = subprocess.run([a.exposuregate, "--version"], capture_output=True, text=True).stdout.strip()
    print(f"{version}; frozen data verified against data/SHA256SUMS\n")
    results = []
    for case in load_cases(a.only):
        for mode in case["modes"]:
            r = run_one(case, mode, a.exposuregate)
            results.append(r)
            mark = "ok  " if r["ok"] else "FAIL"
            print(f"{mark} {case['id']:<34} {mode:<10} {str(r['verdict']):<6} exit {r['exit_code']}")
            for err in r["errors"]:
                print(f"       - {err}")
            for line in r["stderr"]:
                print(f"       stderr: {line}")
    failed = [r for r in results if not r["ok"]]
    projects = len({r["id"] for r in results})
    print(f"\n{len(results) - len(failed)}/{len(results)} scans as expected "
          f"({projects} projects); {len(failed)} failed")
    if a.json:
        a.json.write_text(json.dumps({"tool": version, "results": results}, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
