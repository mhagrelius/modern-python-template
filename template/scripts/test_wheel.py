"""Build from an sdist, then run tests against an isolated installed wheel."""

import argparse
import os
import shutil
import sys
import tarfile
import tomllib
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from _common import entrypoint, project_root, run


def build_distributions(output_directory: Path) -> tuple[Path, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    # Fresh staging prevents old dist/ contents from entering a release.
    with TemporaryDirectory(prefix="build-", dir=output_directory) as temporary:
        stage = Path(temporary)
        run(["uv", "build", "--no-sources", "--out-dir", str(stage)])
        sdists = list(stage.glob("*.tar.gz"))
        wheels = list(stage.glob("*.whl"))
        if len(sdists) != 1 or len(wheels) != 1:
            raise RuntimeError("Expected exactly one newly built sdist and wheel.")
        metadata = tomllib.loads((project_root() / "pyproject.toml").read_text())
        module = metadata["tool"]["uv"]["build-backend"]["module-name"]
        with tarfile.open(sdists[0]) as archive:
            if not any(
                name.endswith(f"/src/{module}/py.typed") for name in archive.getnames()
            ):
                raise RuntimeError("Source distribution is missing py.typed.")
        outputs = tuple(output_directory / item.name for item in (sdists[0], wheels[0]))
        for item, target in zip((sdists[0], wheels[0]), outputs, strict=True):
            _ = shutil.copyfile(item, target)
        return outputs


def test_wheel(wheel: Path) -> None:
    root = project_root()
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    module = metadata["tool"]["uv"]["build-backend"]["module-name"]
    with ZipFile(wheel) as archive:
        names = set(archive.namelist())
        for required in (f"{module}/__init__.py", f"{module}/py.typed"):
            if required not in names:
                raise RuntimeError(f"Wheel is missing {required}.")
    with TemporaryDirectory(prefix="installed-wheel-") as temporary:
        stage = Path(temporary)
        environment = stage / "environment"
        python = environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        requirements = stage / "requirements.txt"
        run(
            [
                "uv",
                "export",
                "--locked",
                "--all-groups",
                "--no-emit-project",
                "--no-hashes",
                "--format",
                "requirements-txt",
                "--output-file",
                str(requirements),
            ]
        )
        run(["uv", "venv", "--python", sys.executable, str(environment)])
        run(["uv", "pip", "sync", "--python", str(python), str(requirements)])
        run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--no-deps",
                str(wheel.resolve()),
            ]
        )
        _ = shutil.copytree(
            root / "tests",
            stage / "tests",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        _ = shutil.copyfile(root / "pyproject.toml", stage / "pyproject.toml")
        provenance = (
            "import importlib,pathlib,site,sys; "
            "module=importlib.import_module(sys.argv[1]); "
            "location=pathlib.Path(module.__file__).resolve(); "
            "assert any(location.is_relative_to(pathlib.Path(p).resolve()) for p in site.getsitepackages()), location; "
            "assert not location.is_relative_to(pathlib.Path(sys.argv[2]).resolve()), location; "
            "print('Installed import verified:',location)"
        )
        run([str(python), "-I", "-c", provenance, module, str(root)], cwd=stage)
        run([str(python), "-I", "-m", "pytest", "--import-mode=importlib"], cwd=stage)
        for command in metadata["project"].get("scripts", {}):
            executable = python.parent / (
                command + ".exe" if os.name == "nt" else command
            )
            run([str(executable), "--help"], cwd=stage)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--wheel", type=Path, help="Test an already built wheel.")
    args = parser.parse_args(argv)
    run(["uv", "lock", "--check"])
    wheel = args.wheel
    if wheel is None:
        _, wheel = build_distributions(project_root() / "dist")
    test_wheel(wheel)
    return 0


if __name__ == "__main__":
    entrypoint(main)
