# Modern Python template

A small Copier template for typed Python libraries and CLIs: uv and uv_build,
Ruff, strict basedpyright, pytest with branch coverage, prek, and pip-audit.
Uses a `src/` layout and tests the installed wheel outside the checkout.

## Create a project

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uvx --from copier==9.18.2 copier copy --vcs-ref=v0.1.0 gh:mhagrelius/modern-python-template my-project
cd my-project
git init --initial-branch=main
uv run --no-project --python 3.14 scripts/bootstrap.py
uv run --locked python scripts/check.py --audit
git add .
git commit -m "Initialize project"
```

Answer the prompts for the distribution/import names, library or CLI, minimum
Python (3.12–3.14), license, and optional GitHub/PyPI setup. Defaults are a library,
Python 3.14, no selected project license, and publishing disabled. Rendering has
no install scripts; bootstrap generates your project's `uv.lock` and installs
hooks. Commit that lockfile. uv 0.12.21 is the reviewed toolchain version.

## Update an existing project

Commit your project changes, then from its root:

```bash
uvx --from copier==9.18.2 copier update
```

Review the diff, resolve any conflicts, and rerun the checks. Your initial README
is preserved; Copier merges other files with your edits. Generated CONTRIBUTING.md
covers dependencies, interpreter support, checks, and optional Trusted Publishing.

## Work on the template

```bash
uv sync --locked
uv run --locked pytest
```

Tests render real projects, bootstrap them, validate installed wheels, and exercise
Copier updates. See [VALIDATION.md](VALIDATION.md) for observed checks and limitations.
MIT licensed. Generated projects independently choose their own license.
