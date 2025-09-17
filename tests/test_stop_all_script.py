import types

import pytest

import stop_all


def test_stop_service_by_pattern_calls_pkill(monkeypatch):
    called = []

    def fake_run(cmd, shell=True):
        called.append(cmd)
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(stop_all, "run_command", fake_run)

    stop_all.stop_service("TestSvc", pattern="some-pattern")

    assert any("pkill -f \"some-pattern\"" in c for c in called)


def test_stop_service_by_port_kills_found_pid(monkeypatch):
    calls = []

    def fake_run(cmd, shell=True):
        calls.append(cmd)
        if cmd.startswith("lsof -ti:"):
            return types.SimpleNamespace(returncode=0, stdout="4321\n", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(stop_all, "run_command", fake_run)

    stop_all.stop_service("TestSvc", port="7777")

    assert any("lsof -ti:7777" in c for c in calls)
    assert any("lsof -ti:7777 | xargs kill -9" in c for c in calls)


def test_stop_service_by_port_no_pid(monkeypatch):
    calls = []

    def fake_run(cmd, shell=True):
        calls.append(cmd)
        if cmd.startswith("lsof -ti:"):
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(stop_all, "run_command", fake_run)

    stop_all.stop_service("TestSvc", port="8888")

    # Should not attempt to kill -9 when no PID
    assert not any("xargs kill -9" in c for c in calls)


def test_stop_redis_found_pid(monkeypatch):
    calls = []

    def fake_run(cmd, shell=True):
        calls.append(cmd)
        if cmd.startswith("lsof -ti:"):
            return types.SimpleNamespace(returncode=0, stdout="5555\n", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(stop_all, "run_command", fake_run)

    stop_all.stop_redis("6379")

    assert any("lsof -ti:6379" in c for c in calls)
    assert any("kill -9 5555" in c for c in calls)


def test_stop_redis_not_running(monkeypatch):
    calls = []

    def fake_run(cmd, shell=True):
        calls.append(cmd)
        if cmd.startswith("lsof -ti:"):
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(stop_all, "run_command", fake_run)

    stop_all.stop_redis("6380")

    assert any("lsof -ti:6380" in c for c in calls)
    assert not any("kill -9" in c for c in calls)


def test_main_invokes_expected_stops(monkeypatch):
    calls = []

    def fake_run(cmd, shell=True):
        calls.append(cmd)
        if cmd.startswith("lsof -ti:"):
            # Return a PID so subsequent kill is attempted
            return types.SimpleNamespace(returncode=0, stdout="9999\n", stderr="")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(stop_all, "run_command", fake_run)

    # Set env ports so we can assert they're used
    monkeypatch.setenv("NOTIFICATION_PORT", "9000")
    monkeypatch.setenv("FASTAPI_PORT", "3031")
    monkeypatch.setenv("RABBITMQ_PORT", "5672")
    monkeypatch.setenv("REDIS_PORT", "6379")

    stop_all.main()

    # Celery Beat pattern pkill
    assert any("pkill -f \"celery -A workers.celery_app beat\"" in c for c in calls)
    # Celery Worker pattern pkill
    assert any("pkill -f \"python.*celery\"" in c for c in calls)
    # Ports are targeted
    assert any("lsof -ti:9000" in c for c in calls)
    assert any("lsof -ti:3031" in c for c in calls)
    assert any("lsof -ti:5672" in c for c in calls)
    assert any("lsof -ti:6379" in c for c in calls)


