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


