"""Shared helpers for contributor commands; no third-party imports."""

import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(arguments: Sequence[str], *, cwd: Path | None = None) -> None:
    print("+ " + " ".join(arguments), flush=True)
    _ = subprocess.run(arguments, cwd=cwd or project_root(), check=True)


def entrypoint(action: Callable[[], int]) -> None:
    try:
        code = action()
    except subprocess.CalledProcessError as error:
        print(
            f"Command failed (exit {error.returncode}); see diagnostics above.",
            file=sys.stderr,
        )
        code = error.returncode
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        code = 1
    raise SystemExit(code)
