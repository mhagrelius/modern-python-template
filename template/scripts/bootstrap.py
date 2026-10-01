"""Explicitly prepare a checkout; rendering never runs this command."""

import subprocess
from pathlib import Path

from _common import entrypoint, project_root, run


def main() -> int:
    root = project_root()
    checkout = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if checkout.returncode or root != Path(checkout.stdout.strip()).resolve():
        raise RuntimeError(
            "Initialize this project with git init --initial-branch=main before bootstrap."
        )
    # uv enforces tool.uv.required-version before it resolves or installs packages.
    run(["uv", "--version"])
    run(["uv", "sync", "--all-groups"])
    run(["uv", "run", "--locked", "--no-sync", "prek", "install"])
    print("Setup complete. Commit uv.lock with your source files.")
    return 0


if __name__ == "__main__":
    entrypoint(main)
