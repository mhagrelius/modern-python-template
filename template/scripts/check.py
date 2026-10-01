"""Run the same read-only quality gates used by CI."""

import argparse
import sys
from collections.abc import Sequence

from _common import entrypoint, project_root, run


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args(argv)
    run(["uv", "sync", "--locked", "--all-groups"])
    run(["uv", "run", "--locked", "--no-sync", "ruff", "check", "."])
    run(["uv", "run", "--locked", "--no-sync", "ruff", "format", "--check", "."])
    run(["uv", "run", "--locked", "--no-sync", "basedpyright"])
    run(
        [
            "uv",
            "run",
            "--locked",
            "--no-sync",
            "pytest",
            "--cov",
            "--cov-report=term-missing",
            "--cov-report=xml",
        ]
    )
    run([sys.executable, str(project_root() / "scripts/test_wheel.py")])
    return 0


if __name__ == "__main__":
    entrypoint(main)
