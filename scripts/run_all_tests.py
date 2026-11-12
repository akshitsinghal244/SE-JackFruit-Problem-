#!/usr/bin/env python3
"""Run every automated RDCP test suite and print a pass/fail summary.

    python scripts/run_all_tests.py            # gateway + services + client
    python scripts/run_all_tests.py --fast     # skip the slow service-model trainings

The script is the single entry point referenced by docs/testing/test-report.md.
Exit code 0 = every suite passed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(name: str, cmd: list[str], cwd: str, env: dict | None = None) -> dict:
    t0 = time.time()
    e = dict(os.environ)
    e.update(env or {})
    e.setdefault("PYTHONIOENCODING", "utf-8")
    p = subprocess.run(cmd, cwd=os.path.join(REPO, cwd), env=e, capture_output=True, check=False)
    out = ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "replace").strip()
    return {"name": name, "cmd": " ".join(cmd), "cwd": cwd, "code": p.returncode,
            "seconds": round(time.time() - t0, 1), "tail": "\n".join(out.splitlines()[-12:])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="skip the slow DL/QML training runs")
    ap.add_argument("--json", metavar="PATH", help="also write the results as JSON")
    a = ap.parse_args()

    npm = shutil.which("npm")
    suites = [
        run("gateway (auth, orchestrator, resilience, security, perf)", [PY, "-m", "pytest", "-q"], "gateway"),
        run("services (shared, ML/DL/QML, HTTP contract)", [PY, "-m", "pytest", "-q"], "services"),
    ]
    if npm:
        suites.append(run("client (Vitest: UI + api layer)", [npm, "exec", "--", "vitest", "run"], "client"))
    else:
        suites.append({"name": "client (Vitest)", "code": 127, "seconds": 0.0, "tail": "npm not found on PATH"})

    for s in suites:
        head = f"[{'PASS' if s['code'] == 0 else 'FAIL'}] {s['name']} ({s['seconds']}s)"
        print(head)
        if s["code"] != 0:
            print("\n".join(f"    {line}" for line in s.get("tail", "").splitlines()))

    print("\n" + "-" * 72)
    failed = [s["name"] for s in suites if s["code"] != 0]
    print(f"{len(suites) - len(failed)}/{len(suites)} suites passed"
          + (f" - FAILED: {', '.join(failed)}" if failed else ""))

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(suites, f, indent=2)
        print(f"details written to {a.json}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
