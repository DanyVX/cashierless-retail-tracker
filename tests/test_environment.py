"""Environment reporting excludes identifiers and is deterministic at the field level."""

import pytest

from crt import environment


def test_snapshot_contains_reproducibility_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(environment, "_command_output", lambda *args: None)
    report = environment.environment_snapshot()
    assert report["python"]
    assert report["ram_bytes"] is None or report["ram_bytes"] > 0
    assert report["disk_free_bytes"] >= 0
    assert report["git_commit"] is None
    assert "internet_reachable" not in report
    assert "hostname" not in report
    assert "username" not in report


def test_network_only_runs_when_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def probe() -> bool:
        calls.append(1)
        return True

    monkeypatch.setattr(environment, "_network_probe", probe)
    report = environment.environment_snapshot(check_network=True)
    assert report["internet_reachable"] is True
    assert len(calls) == 1


def test_command_output_not_executed_if_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(environment.shutil, "which", lambda _: None)
    assert environment._command_output("not-an-executable") is None


def test_missing_package_returns_none() -> None:
    assert environment._version("nonexistent-package-for-crt-tests-xyz") is None
