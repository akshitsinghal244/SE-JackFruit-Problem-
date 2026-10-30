import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


@pytest.fixture(scope="session")
def synthetic_csv(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp("data") / "synthetic.csv"
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "make_synthetic_data.py"),
         "--out", str(path), "--stores", "2", "--items", "3"],
        check=True, cwd=ROOT, capture_output=True,
    )
    return str(path)


def train(module: str, csv: str, out: str, *extra: str) -> None:
    subprocess.run([sys.executable, "-m", module, "--data", csv, "--out", out, *extra],
                   check=True, cwd=ROOT, capture_output=True)
