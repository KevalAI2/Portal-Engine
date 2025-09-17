import os
import types
import builtins
import sys

import pytest

import start_all


def test_ensure_package_dirs_creates_inits(tmp_path):
    root_dir = str(tmp_path)
    # Start with empty temp dir; function should create app/, app/workers/ and __init__.py files
    start_all.ensure_package_dirs(root_dir)
    assert (tmp_path / "app").exists()
    assert (tmp_path / "app" / "workers").exists()
    assert (tmp_path / "app" / "__init__.py").exists()
    assert (tmp_path / "app" / "workers" / "__init__.py").exists()


def test_check_celery_app_exists_missing_file(tmp_path, monkeypatch):
    root_dir = str(tmp_path)
    # Ensure workers directory exists but no celery_app.py
    (tmp_path / "app" / "workers").mkdir(parents=True)
    assert start_all.check_celery_app_exists(root_dir) is False


def test_check_celery_app_exists_import_ok(tmp_path, monkeypatch):
    # Create package structure and a minimal celery_app module
    app_dir = tmp_path / "app"
    workers_dir = app_dir / "workers"
    workers_dir.mkdir(parents=True)
    (app_dir / "__init__.py").write_text("")
    (workers_dir / "__init__.py").write_text("")
    (workers_dir / "celery_app.py").write_text("celery_app = object()\n")

    # The function checks existence and then imports
    root_dir = str(tmp_path)
    # Make sure import path can resolve the package
    sys.path.insert(0, root_dir)
    sys.path.insert(0, str(app_dir))
    try:
        assert start_all.check_celery_app_exists(root_dir) is True
    finally:
        # Cleanup sys.path modifications
        sys.path = [p for p in sys.path if p not in (root_dir, str(app_dir))]


def test_main_happy_path_composes_commands(tmp_path, monkeypatch):
    calls = []

    class FakeBgProc:
        def __init__(self, pid):
            self.pid = pid

        def poll(self):
            return None

        def communicate(self):
            return ("", "")

    def fake_run_command(cmd, cwd=None, background=False, env=None):
        calls.append((cmd, cwd, background, env))
        if background:
            # Simulate background Popen-like object with pid and poll()
            return FakeBgProc(pid=1234)
        # Simulate successful synchronous command
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    # Avoid real sleeps
    monkeypatch.setattr(start_all.time, "sleep", lambda *_: None)
    # Pretend binaries and paths exist
    monkeypatch.setattr(start_all.os.path, "exists", lambda p: True)
    # Ensure we do not attempt real import within the function
    monkeypatch.setattr(start_all, "check_celery_app_exists", lambda _rd: True)
    monkeypatch.setattr(start_all, "run_command", fake_run_command)
    # Control getcwd and environment
    fake_environ = os.environ.copy()
    monkeypatch.setattr(start_all.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(start_all.os, "environ", fake_environ)

    start_all.main()

    all_cmds = "\n".join(c[0] for c in calls if isinstance(c[0], str))
    assert "redis-server" in all_cmds
    assert "rabbitmq-server" in all_cmds
    assert "celery -A app.workers.celery_app worker" in all_cmds
    assert "celery -A app.workers.celery_app beat" in all_cmds
    assert "python notification_service.py" in all_cmds
    assert "python app/main.py" in all_cmds


def test_main_exits_when_rabbitmq_missing(tmp_path, monkeypatch):
    # Make celery app check succeed to reach rabbitmq path check
    monkeypatch.setattr(start_all, "check_celery_app_exists", lambda _rd: True)

    # Only return False for rabbitmq_server path, True otherwise
    def fake_exists(path):
        if path.endswith("rabbitmq-server"):
            return False
        return True

    monkeypatch.setattr(start_all.os.path, "exists", fake_exists)
    monkeypatch.setattr(start_all.time, "sleep", lambda *_: None)

    # Control getcwd and environment
    monkeypatch.setattr(start_all.os, "getcwd", lambda: str(tmp_path))

    with pytest.raises(SystemExit) as exc:
        start_all.main()
    assert exc.value.code == 1


