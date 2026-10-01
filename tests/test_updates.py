import subprocess
import sys

import copier

from tests.conftest import ROOT, git


def commit(project, message):
    git(project, "add", ".")
    git(
        project,
        "-c",
        "user.name=Template Test",
        "-c",
        "user.email=template@example.invalid",
        "commit",
        "-m",
        message,
    )


def test_update_preserves_project_edits_and_exposes_configuration_conflict(tmp_path):
    source = tmp_path / "template"
    git(ROOT, "clone", "--no-hardlinks", str(ROOT), str(source))
    git(source, "tag", "v1000.0.0")
    project = tmp_path / "project"
    copier.run_copy(
        str(source),
        str(project),
        defaults=True,
        vcs_ref="v1000.0.0",
        quiet=True,
        unsafe=False,
    )
    git(project, "init", "--initial-branch=main")
    commit(project, "Generate project")

    package = project / "src/example_package/__init__.py"
    package.write_text("# User-owned addition\n" + package.read_text())
    readme = project / "README.md"
    readme.write_text("# My actual project\n\nUser-owned documentation.\n")
    config = project / "pyproject.toml"
    config.write_text(
        config.read_text().replace('version = "0.1.0"', 'version = "0.1.1"')
    )
    commit(project, "Customize project")

    template_package = source / "template/src/{{ module_name }}/__init__.py"
    template_package.write_text(template_package.read_text() + "\n# Template update\n")
    template_readme = source / "template/README.md.jinja"
    template_readme.write_text("# New template introduction\n")
    template_config = source / "template/pyproject.toml.jinja"
    template_config.write_text(
        template_config.read_text().replace('version = "0.1.0"', 'version = "0.2.0"')
    )
    commit(source, "Update template")
    git(source, "tag", "v1000.1.0")

    copier.run_update(
        str(project),
        defaults=True,
        overwrite=True,
        vcs_ref="v1000.1.0",
        quiet=True,
        unsafe=False,
    )
    assert "# User-owned addition" in package.read_text()
    assert "# Template update" in package.read_text()
    assert readme.read_text() == "# My actual project\n\nUser-owned documentation.\n"
    assert "<<<<<<<" in config.read_text()
    assert 'version = "0.1.1"' in config.read_text()
    assert 'version = "0.2.0"' in config.read_text()
    result = subprocess.run(
        [sys.executable, str(project / "scripts/check_conflicts.py"), str(config)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
