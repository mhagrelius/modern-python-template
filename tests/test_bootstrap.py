import os
import subprocess
import sys

from tests.conftest import git


def command(project, script, *args):
    environment = os.environ.copy()
    environment.pop("VIRTUAL_ENV", None)
    environment["PREK_HOME"] = str(project.parent / "prek-cache")
    return subprocess.run(
        [sys.executable, str(project / "scripts" / script), *args],
        cwd=project,
        text=True,
        capture_output=True,
        env=environment,
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


def test_generated_checks_reject_lint_and_type_errors(render):
    project = render()
    git(project, "init", "-b", "main")
    setup = command(project, "bootstrap.py")
    assert setup.returncode == 0, setup.stderr
    source = project / "src/example_package/__init__.py"
    original = source.read_text()
    source.write_text(original + "\nimport os\n")
    lint = command(project, "check.py")
    assert lint.returncode != 0
    assert "F401" in lint.stdout
    source.write_text(original + '\n\nwrong: int = "not a number"\n')
    typed = command(project, "check.py")
    assert typed.returncode != 0
    assert "reportAssignmentType" in typed.stdout
