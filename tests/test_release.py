import os
import subprocess

import pytest
import yaml


def workflow(project, name):
    return yaml.safe_load((project / ".github/workflows" / name).read_text())


@pytest.mark.parametrize("floor", ["3.12", "3.13", "3.14"])
def test_check_matrix_covers_supported_interpreters_and_platforms(render, floor):
    project = render({"python_min": floor})
    checks = workflow(project, "checks.yml")
    matrix = checks["jobs"]["check"]["strategy"]["matrix"]["include"]
    expected = [
        ("ubuntu-latest", f"3.{minor}") for minor in range(int(floor.split(".")[1]), 15)
    ]
    expected += [("macos-latest", "3.14"), ("windows-latest", "3.14")]
    assert [(entry["os"], entry["python"]) for entry in matrix] == expected
    assert checks["permissions"] == {"contents": "read"}
    steps = checks["jobs"]["check"]["steps"]
    assert any("--audit" in step.get("run", "") for step in steps)
    assert all(
        len(step["uses"].split("@")[1]) == 40 for step in steps if "uses" in step
    )


@pytest.mark.parametrize("tag", ["v0.1.0", "v9.9.9", "v$(touch INJECTED)"])
def test_release_validates_tag_and_publishes_only_transferred_artifacts(
    render, tmp_path, tag
):
    project = render(
        {"publish_to_pypi": True, "license": "MIT", "github_owner": "example"}
    )
    release = workflow(project, "release.yml")
    jobs = release["jobs"]
    validate = jobs["validate"]
    tag_step = next(
        step for step in validate["steps"] if step.get("name") == "Validate release tag"
    )
    env = {**os.environ, "RELEASE_TAG": tag}
    env.pop("VIRTUAL_ENV", None)
    result = subprocess.run(
        ["bash", "-c", tag_step["run"]],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) == (tag == "v0.1.0"), result.stderr
    assert not (project / "INJECTED").exists()
    assert release["permissions"] == {"contents": "read"}
    publish = jobs["publish"]
    assert publish["needs"] == "validate"
    assert publish["environment"]["name"] == "pypi"
    assert publish["permissions"]["id-token"] == "write"
    commands = "\n".join(step.get("run", "") for step in publish["steps"])
    assert "uv publish --trusted-publishing always" in commands
    assert "uv build" not in commands
    upload = next(
        step for step in validate["steps"] if "upload-artifact@" in step.get("uses", "")
    )
    download = next(
        step
        for step in publish["steps"]
        if "download-artifact@" in step.get("uses", "")
    )
    assert upload["with"]["name"] == download["with"]["name"]
    assert "*.whl" in upload["with"]["path"] and "*.tar.gz" in upload["with"]["path"]
