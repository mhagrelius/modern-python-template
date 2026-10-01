# Validation

Observed locally on macOS arm64 on 2026-10-01.

- 30 maintainer tests passed, including real library/CLI rendering, bootstrap in a
  path containing spaces, stale-lock/lint/type failures, isolated installed-wheel
  tests, missing `py.typed`, audit failure propagation, tag validation, and updates.
- Generated CLI projects passed their full checks, including installed-wheel tests,
  on Python 3.12.14 and 3.13.15. Maintainer integration tests used Python 3.14.8.
- A real pip-audit run on the synchronized locked development environment reported
  no known vulnerabilities. This is a point-in-time advisory check.
- All generated workflow variants and the maintainer workflow passed actionlint
  1.7.12. Referenced action tags were resolved to full commit SHAs via GitHub's API.
- Copier update tests use two local Git tags: user source additions and README text
  survive; incompatible version edits produce visible conflict markers.

The generated GitHub workflows cover Linux across the selected Python range and
macOS/Windows on 3.14. Local macOS checks do not establish those remote results.
PyPI publishing is configured only when requested and requires a Trusted Publisher;
no package has been uploaded to PyPI during template validation.

## Deliberate simplifications

Copier handles rendering and updates. Native pip-audit checks the synchronized
locked environment; there is no custom advisory parser. `uv version` validates
release tags. GitHub transfers build artifacts between release jobs; there is no
custom release manifest or release script. Existing pytest tests provide acceptance
coverage instead of a second acceptance framework.

Contributor scripts are limited to bootstrap, the shared check command, installed
wheel validation, a small conflict-marker hook, and shared subprocess helpers.

## Execution decisions

- A new output repository on a feature branch provided isolation without another
  worktree. If that assumption were wrong, the output would need relocating.
- Sandbox-local uv caches and managed Python downloads were used. This consumes
  scratch disk space; it does not change the generated project configuration.
- Already-run verification was recorded after commits instead of repeating an
  unchanged suite. No commit hooks were installed in the template repository.
- The user's request for less support code superseded the plan's custom audit,
  release-manifest, and duplicate acceptance scripts. Native tool diagnostics and
  exit codes are retained; custom diagnostics are intentionally absent.

## Sources

Tool versions were checked against PyPI and the installed uv release during
implementation. Configuration follows [uv](https://docs.astral.sh/uv/),
[Copier](https://copier.readthedocs.io/),
[pytest](https://docs.pytest.org/en/stable/reference/customize.html), and
[GitHub Dependabot](https://docs.github.com/en/code-security/dependabot/).
