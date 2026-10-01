import os
import subprocess
import sys

from conftest import git


def command(project, script, *args):
    return subprocess.run(
        [sys.executable, str(project / "scripts" / script), *args],
        cwd=project,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )


def test_bootstrap_without_git_fails_before_install(render):
    project = render()
    result = command(project, "bootstrap.py")
    assert result.returncode != 0
    assert "git init" in result.stderr
    assert not (project / ".venv").exists()
    assert not (project / "uv.lock").exists()


def test_bootstrap_creates_lock_and_hooks_without_commits(render):
    project = render()
    git(project, "init", "-b", "main")
    result = command(project, "bootstrap.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (project / "uv.lock").is_file()
    assert (project / ".git/hooks/pre-commit").is_file()
    assert git(project, "remote") == ""
    assert (
        subprocess.run(
            ["git", "-C", str(project), "rev-parse", "HEAD"], capture_output=True
        ).returncode
        != 0
    )
    pyproject = project / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace("dependencies = []", 'dependencies = ["idna"]')
    )
    stale = command(project, "check.py")
    assert stale.returncode != 0
    assert "lock" in stale.stderr.lower()
