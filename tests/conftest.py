import subprocess
from collections.abc import Mapping
from pathlib import Path

import copier
import pytest

ROOT = Path(__file__).resolve().parents[1]


def render_project(
    destination: Path, answers: Mapping[str, object] | None = None
) -> Path:
    copier.run_copy(
        str(ROOT),
        str(destination),
        data=dict(answers or {}),
        defaults=True,
        vcs_ref="HEAD",
        unsafe=False,
        quiet=True,
    )
    return destination


def git(project: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(project), *arguments], text=True)


@pytest.fixture
def render(tmp_path: Path):
    def make(answers=None):
        return render_project(tmp_path / "project with spaces", answers)

    return make
