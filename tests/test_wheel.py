from zipfile import ZIP_DEFLATED, ZipFile

from tests.conftest import git
from tests.test_bootstrap import command


def test_built_wheel_is_tested_outside_checkout(render):
    project = render({"project_kind": "cli", "module_name": "custom_import"})
    git(project, "init", "-b", "main")
    setup = command(project, "bootstrap.py")
    assert setup.returncode == 0, setup.stderr
    dist = project / "dist"
    dist.mkdir()
    (dist / "stale-99-py3-none-any.whl").write_text("not a wheel")
    result = command(project, "test_wheel.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Installed import verified:" in result.stdout
    assert "4 passed" in result.stdout
    wheel = next(dist.glob("example_package-0.1.0-*.whl"))
    with ZipFile(wheel) as archive:
        items = {
            name: archive.read(name)
            for name in archive.namelist()
            if name != "custom_import/py.typed"
        }
    damaged = dist / "damaged.whl"
    with ZipFile(damaged, "w", ZIP_DEFLATED) as archive:
        for name, data in items.items():
            archive.writestr(name, data)
    invalid = command(project, "test_wheel.py", "--wheel", str(damaged))
    assert invalid.returncode != 0
    assert "py.typed" in invalid.stderr
