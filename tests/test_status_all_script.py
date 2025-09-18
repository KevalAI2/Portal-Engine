import socket
import types

import pytest

import status_all


def test_is_port_in_use_true(monkeypatch):
    class FakeSocket:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def connect_ex(self, addr):
            return 0

    monkeypatch.setattr(status_all.socket, "socket", lambda *a, **k: FakeSocket())
    assert status_all.is_port_in_use(1234) is True


def test_is_port_in_use_false(monkeypatch):
    class FakeSocket:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def connect_ex(self, addr):
            return 1

    monkeypatch.setattr(status_all.socket, "socket", lambda *a, **k: FakeSocket())
    assert status_all.is_port_in_use(1234) is False


def test_get_pid_for_port_found(monkeypatch):
    def fake_check_output(args):
        assert args[:2] == ["lsof", "-ti"]
        return b"1111\n2222\n"

    monkeypatch.setattr(status_all.subprocess, "check_output", fake_check_output)
    assert status_all.get_pid_for_port(3031) == "1111"


def test_get_pid_for_port_not_found(monkeypatch):
    def fake_check_output(args):
        raise status_all.subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(status_all.subprocess, "check_output", fake_check_output)
    assert status_all.get_pid_for_port(3031) is None


def test_get_all_pids_multiple(monkeypatch):
    def fake_run(cmd, shell=True, capture_output=True, text=True):
        return types.SimpleNamespace(returncode=0, stdout="111\n222\n")

    monkeypatch.setattr(status_all.subprocess, "run", fake_run)
    assert status_all.get_all_pids("pattern") == ["111", "222"]


def test_get_all_pids_empty(monkeypatch):
    def fake_run(cmd, shell=True, capture_output=True, text=True):
        return types.SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(status_all.subprocess, "run", fake_run)
    assert status_all.get_all_pids("pattern") == []


def test_check_celery_workers_active(monkeypatch):
    stdout = (
        "ACTIVE:2\n"
        "REGISTERED:10\n"
        "SCHEDULED:0\n"
        "HOSTNAME:worker1\n"
        "HOSTNAME:worker2\n"
    )

    def fake_run(args, capture_output=True, text=True, timeout=10, env=None):
        return types.SimpleNamespace(returncode=0, stdout=stdout)

    monkeypatch.setattr(status_all.subprocess, "run", fake_run)
    result = status_all.check_celery_workers()
    assert result.strip() == stdout.strip()


def test_check_celery_workers_subprocess_error(monkeypatch):
    def fake_run(args, capture_output=True, text=True, timeout=10, env=None):
        return types.SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(status_all.subprocess, "run", fake_run)
    assert status_all.check_celery_workers() == "ERROR:Subprocess failed"


def test_check_celery_workers_exception(monkeypatch):
    def fake_run(args, capture_output=True, text=True, timeout=10, env=None):
        raise RuntimeError("bad import")

    monkeypatch.setattr(status_all.subprocess, "run", fake_run)
    out = status_all.check_celery_workers()
    assert out.startswith("ERROR:")



def test_main_all_services_running(monkeypatch, capsys):
    # Simulate ports in use
    monkeypatch.setattr(status_all, "is_port_in_use", lambda p: True)
    # PID lookups
    monkeypatch.setattr(status_all, "get_pid_for_port", lambda p: "1234")
    # Celery worker/beat PIDs
    def fake_get_all_pids(pattern):
        if "worker" in pattern:
            return ["2001", "2002"]
        if "beat" in pattern:
            return ["3001"]
        if "notification_service.py" in pattern:
            return ["4001"]
        if "main.py" in pattern:
            return ["5001"]
        return []
    monkeypatch.setattr(status_all, "get_all_pids", fake_get_all_pids)

    # Redis ping and RabbitMQ status succeed
    def fake_run(cmd, shell=True, capture_output=True, text=True, timeout=10):
        class R:
            returncode = 0
            stdout = "PONG" if "redis-cli" in cmd else "ok"
            stderr = ""
        return R()
    monkeypatch.setattr(status_all.subprocess, "run", fake_run)

    # RabbitMQ ctl path exists
    monkeypatch.setattr(status_all.os.path, "exists", lambda p: True)

    # Celery inspector output
    monkeypatch.setattr(status_all, "check_celery_workers", lambda: (
        "ACTIVE:1\nREGISTERED:10\nSCHEDULED:0\nHOSTNAME:worker1\n"
    ))

    status_all.main()
    captured = capsys.readouterr().out
    assert "Redis (port" in captured and "✅ RUNNING" in captured
    assert "RabbitMQ (port" in captured and "✅ RabbitMQ responding properly" in captured
    assert "Celery Worker:" in captured and "ACTIVE:1".replace("ACTIVE:", "   ✅ 1 active workers")
    assert "Celery Beat:" in captured and "✅ RUNNING" in captured
    assert "Notification Service" in captured and "✅ RUNNING" in captured
    assert "FastAPI Service" in captured and "✅ RUNNING" in captured
    assert "=== Status Check Complete ===" in captured


def test_main_services_stopped(monkeypatch, capsys):
    # No ports in use
    monkeypatch.setattr(status_all, "is_port_in_use", lambda p: False)
    # No processes
    monkeypatch.setattr(status_all, "get_all_pids", lambda pattern: [])
    # lsof lookups won't be called but safe to stub
    monkeypatch.setattr(status_all, "get_pid_for_port", lambda p: None)
    # RabbitMQ ctl path check
    monkeypatch.setattr(status_all.os.path, "exists", lambda p: False)
    # run() shouldn't be used but stub anyway
    def fake_run(cmd, shell=True, capture_output=True, text=True, timeout=10):
        class R:
            returncode = 1
            stdout = ""
            stderr = ""
        return R()
    monkeypatch.setattr(status_all.subprocess, "run", fake_run)

    status_all.main()
    captured = capsys.readouterr().out
    assert captured.count("❌ STOPPED") >= 5  # multiple services should be stopped


def test_main_celery_inspector_unavailable(monkeypatch, capsys):
    # Worker present but inspector not available
    monkeypatch.setattr(status_all, "is_port_in_use", lambda p: False)
    monkeypatch.setattr(status_all, "get_all_pids", lambda pattern: ["2222"] if "worker" in pattern else [])
    monkeypatch.setattr(status_all, "check_celery_workers", lambda: "NO_INSPECTOR")
    status_all.main()
    captured = capsys.readouterr().out
    assert "Workers running but inspector not available" in captured


def test_main_redis_open_but_no_pong(monkeypatch, capsys):
    # Redis port open, other ports closed
    def fake_is_port(port):
        return port == 6379
    monkeypatch.setattr(status_all, "is_port_in_use", fake_is_port)
    monkeypatch.setattr(status_all, "get_pid_for_port", lambda p: "1111")

    def fake_run(cmd, shell=True, capture_output=True, text=True, timeout=10):
        # Simulate redis ping not returning PONG
        if "redis-cli ping" in cmd:
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        return types.SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(status_all.subprocess, "run", fake_run)
    # RabbitMQ ctl not found
    monkeypatch.setattr(status_all.os.path, "exists", lambda p: False)
    # No celery processes
    monkeypatch.setattr(status_all, "get_all_pids", lambda pattern: [])

    status_all.main()
    out = capsys.readouterr().out
    assert "Redis (port" in out and "port open but not responding" in out


def test_main_rabbitmq_open_ctl_missing(monkeypatch, capsys):
    # Only RabbitMQ port open
    def fake_is_port(port):
        return port == 5672
    monkeypatch.setattr(status_all, "is_port_in_use", fake_is_port)
    monkeypatch.setattr(status_all, "get_pid_for_port", lambda p: "2222")
    # rabbitmqctl missing
    monkeypatch.setattr(status_all.os.path, "exists", lambda p: False)
    # subprocess run default
    monkeypatch.setattr(status_all.subprocess, "run", lambda *a, **k: types.SimpleNamespace(returncode=0, stdout="", stderr=""))
    # No celery or other services
    monkeypatch.setattr(status_all, "get_all_pids", lambda pattern: [])

    status_all.main()
    out = capsys.readouterr().out
    assert "RabbitMQ (port 5672):" in out and "control tool not found" in out
