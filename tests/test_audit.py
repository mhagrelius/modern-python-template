import importlib.util
import subprocess
import sys

import pytest


@pytest.mark.parametrize("audit_status", [0, 1, 2])
def test_check_runs_native_audit_and_preserves_failure(
    render, monkeypatch, audit_status
):
    project = render()
    monkeypatch.syspath_prepend(str(project / "scripts"))
    monkeypatch.delitem(sys.modules, "_common", raising=False)
    spec = importlib.util.spec_from_file_location(
        "generated_check", project / "scripts/check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    commands = []

    def run(arguments):
        commands.append(arguments)
        if "pip-audit" in arguments and audit_status:
            raise subprocess.CalledProcessError(audit_status, arguments)

    monkeypatch.setattr(module, "run", run)
    if audit_status:
        with pytest.raises(subprocess.CalledProcessError) as error:
            module.main(["--audit"])
        assert error.value.returncode == audit_status
    else:
        assert module.main(["--audit"]) == 0
    assert commands[0] == ["uv", "sync", "--locked", "--all-groups"]
    audit = next(command for command in commands if "pip-audit" in command)
    assert "--local" in audit and "--skip-editable" in audit
    assert "--fix" not in audit and "--ignore-vuln" not in audit
