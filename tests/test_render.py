import subprocess
import tomllib

import pytest
import yaml


def test_default_is_typed_private_library(render):
    project = render()
    metadata = tomllib.loads((project / "pyproject.toml").read_text())
    assert metadata["project"]["version"] == "0.1.0"
    assert metadata["project"]["requires-python"] == ">=3.14"
    assert metadata["build-system"]["build-backend"] == "uv_build"
    assert (project / "src/example_package/py.typed").is_file()
    assert not (project / "src/example_package/cli.py").exists()
    assert not (project / "LICENSE").exists()
    assert not (project / ".github/workflows/release.yml").exists()
    assert not (project / "uv.lock").exists()
    assert not (project / ".git").exists()


def test_metadata_round_trips_without_executing_text(render):
    description = 'Quoted "hello"\nUnicode café 🐍 and $(touch INJECTED) `whoami`'
    project = render({"distribution_name": "useful-tool", "description": description})
    build = subprocess.run(["uv", "build"], cwd=project, capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    metadata = tomllib.loads((project / "pyproject.toml").read_text())
    assert metadata["project"]["description"] == " ".join(description.split())
    assert (project / "src/useful_tool/__init__.py").is_file()
    assert not (project / "INJECTED").exists()
    answers = yaml.safe_load((project / ".copier-answers.yml").read_text())
    assert answers["description"] == description


@pytest.mark.parametrize(
    "module_name", ["class", "../bad", "bad-name", "1bad", "os", "sys"]
)
def test_invalid_or_shadowing_module_names_are_rejected(render, module_name):
    with pytest.raises(ValueError):
        render({"module_name": module_name})


@pytest.mark.parametrize("floor", ["3.12", "3.13", "3.14"])
def test_python_minimum_controls_syntax_and_ci_matrix(render, floor):
    project = render({"python_min": floor})
    metadata = tomllib.loads((project / "pyproject.toml").read_text())
    assert metadata["tool"]["basedpyright"]["pythonVersion"] == floor
    assert metadata["tool"]["ruff"]["target-version"] == "py" + floor.replace(".", "")


def test_public_cli_requires_license_and_repository(render):
    with pytest.raises(ValueError):
        render({"publish_to_pypi": True})


def test_public_cli_has_entrypoint_and_release(render):
    project = render(
        {
            "project_kind": "cli",
            "publish_to_pypi": True,
            "license": "MIT",
            "github_owner": "example",
            "github_repository": "example-package",
        }
    )
    metadata = tomllib.loads((project / "pyproject.toml").read_text())
    assert (
        metadata["project"]["scripts"]["example-package"] == "example_package.cli:main"
    )
    assert (project / "LICENSE").is_file()
    assert (project / ".github/workflows/release.yml").is_file()


@pytest.mark.parametrize(
    "answers",
    [
        {"python_min": "3.10"},
        {"github_owner": "bad/name"},
        {"distribution_name": "../bad"},
    ],
)
def test_invalid_answers_are_rejected(render, answers):
    with pytest.raises(ValueError):
        render(answers)


def test_bsd_notice_uses_selected_author(render):
    project = render({"license": "BSD-3-Clause", "author_name": "Test Author"})
    notice = (project / "LICENSE").read_text()
    assert "Copyright (c) 2026 Test Author" in notice
    assert "<owner>" not in notice
