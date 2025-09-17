import json
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


class DummyHTTPResponse:
    def __init__(self, status_code=200, data=None, text="", url="http://example.com", headers=None):
        self.status_code = status_code
        self._data = data
        self.text = text
        self.url = url
        self.headers = headers or {"content-type": "application/json"}

    def json(self):
        if self._data is None:
            raise ValueError("no json")
        return self._data


class DummyAsyncClient:
    def __init__(self, behavior=None, timeout=30.0):
        # behavior: dict of method -> DummyHTTPResponse or Exception
        self.behavior = behavior or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, headers=None):
        resp = self.behavior.get("GET")
        if isinstance(resp, BaseException):
            raise resp
        return resp or DummyHTTPResponse(data={"ok": True}, url=url)

    async def post(self, url, headers=None, content=None):
        resp = self.behavior.get("POST")
        if isinstance(resp, BaseException):
            raise resp
        return resp or DummyHTTPResponse(data={"posted": True, "content": content}, url=url)

    async def put(self, url, headers=None, content=None):
        resp = self.behavior.get("PUT")
        if isinstance(resp, BaseException):
            raise resp
        return resp or DummyHTTPResponse(data={"put": True, "content": content}, url=url)

    async def delete(self, url, headers=None):
        resp = self.behavior.get("DELETE")
        if isinstance(resp, BaseException):
            raise resp
        return resp or DummyHTTPResponse(data={"deleted": True}, url=url)

    async def patch(self, url, headers=None, content=None):
        resp = self.behavior.get("PATCH")
        if isinstance(resp, BaseException):
            raise resp
        return resp or DummyHTTPResponse(data={"patched": True, "content": content}, url=url)


class FakeRedis:
    def __init__(self, data=None):
        # data is a dict-like representing key -> json string
        self._data = data or {}

    def scan_iter(self, match=None):
        for k in list(self._data.keys()):
            if match is None or match.replace("*", "") in k:
                yield k

    def get(self, key):
        return self._data.get(key)

    def ping(self):
        return True


class MemInfo:
    def __init__(self, percent=25.0, available=8 * 1024**3):
        self.percent = percent
        self.available = available


def write_fake_pytest_artifacts(project_root: Path, tests_passed: int = 5, tests_failed: int = 0):
    report_path = project_root / "test-results.json"
    coverage_xml = project_root / "coverage.xml"

    # Minimal pytest JSON report
    report = {
        "summary": {
            "total": tests_passed + tests_failed,
            "passed": tests_passed,
            "failed": tests_failed,
            "skipped": 0,
            "xpassed": 0,
            "xfailed": 0,
            "warnings": 0,
        },
        "tests": [
            {"nodeid": "tests/test_sample.py::test_ok", "outcome": "passed"}
        ],
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")

    # Minimal coverage.xml resembling coverage.py format the UI parser expects
    coverage_xml.write_text(
        """
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="app/api/routers/ui.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
            <line number="3" hits="0"/>
            <line number="4" hits="1"/>
          </lines>
        </class>
        <class filename="app/main.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
        """
        .strip(),
        encoding="utf-8",
    )


def test_ui_basic_pages_render():
    client = TestClient(app)
    r = client.get("/ui/")
    assert r.status_code == 200
    r = client.get("/ui/test")
    assert r.status_code == 200
    r = client.get("/ui/portal")
    assert r.status_code == 200
    r = client.get("/ui/tests")
    assert r.status_code == 200


def test_ui_pages_template_error(monkeypatch):
    # Force TemplateResponse to raise for all pages to hit exception paths
    import app.api.routers.ui as ui_mod

    class FakeTemplates:
        def TemplateResponse(self, *args, **kwargs):
            raise Exception("template fail")

    monkeypatch.setattr(ui_mod, "templates", FakeTemplates())
    client = TestClient(app)
    # These endpoints should propagate HTTPException 500 handled by global handler into JSON 500
    for path in ["/ui/", "/ui/test", "/ui/portal", "/ui/tests"]:
        resp = client.get(path)
        assert resp.status_code == 500


def test_proxy_success_json_and_text(monkeypatch):
    import httpx

    dummy_json = DummyHTTPResponse(status_code=200, data={"hello": "world"}, url="http://x")
    dummy_text = DummyHTTPResponse(status_code=200, data=None, text="plain", url="http://x")

    def make_client(*args, **kwargs):
        return DummyAsyncClient(behavior={"GET": dummy_json, "POST": dummy_text})

    monkeypatch.setattr(httpx, "AsyncClient", make_client)

    client = TestClient(app)
    r = client.post("/ui/proxy", json={"method": "GET", "url": "http://x"})
    assert r.status_code == 200 and r.json()["success"] is True
    assert r.json()["data"] == {"hello": "world"}

    r = client.post("/ui/proxy", json={"method": "POST", "url": "http://x", "body": "data"})
    assert r.status_code == 200 and r.json()["success"] is True
    assert r.json()["data"] == "plain"


def test_proxy_errors(monkeypatch):
    import httpx

    timeout_exc = httpx.TimeoutException("timeout")
    conn_exc = httpx.ConnectError("connect")

    def make_client_timeout(*args, **kwargs):
        return DummyAsyncClient(behavior={"GET": timeout_exc})

    def make_client_connect(*args, **kwargs):
        return DummyAsyncClient(behavior={"GET": conn_exc})

    monkeypatch.setattr(httpx, "AsyncClient", make_client_timeout)
    client = TestClient(app)
    r = client.post("/ui/proxy", json={"method": "GET", "url": "http://x"})
    assert r.json()["status_code"] == 408

    monkeypatch.setattr(httpx, "AsyncClient", make_client_connect)
    r = client.post("/ui/proxy", json={"method": "GET", "url": "http://x"})
    assert r.json()["status_code"] == 503

    r = client.post("/ui/proxy", json={"method": "TRACE", "url": "http://x"})
    assert r.status_code == 200
    assert r.json()["success"] is False


def test_proxy_put_delete_patch(monkeypatch):
    import httpx

    dummy_put = DummyHTTPResponse(status_code=200, data={"put": True}, url="http://x")
    dummy_delete = DummyHTTPResponse(status_code=200, data={"deleted": True}, url="http://x")
    dummy_patch = DummyHTTPResponse(status_code=200, data={"patched": True}, url="http://x")

    def make_client(*args, **kwargs):
        return DummyAsyncClient(behavior={"PUT": dummy_put, "DELETE": dummy_delete, "PATCH": dummy_patch})

    monkeypatch.setattr(httpx, "AsyncClient", make_client)
    client = TestClient(app)

    r = client.post("/ui/proxy", json={"method": "PUT", "url": "http://x", "body": "data"})
    assert r.status_code == 200 and r.json()["success"] is True

    r = client.post("/ui/proxy", json={"method": "DELETE", "url": "http://x"})
    assert r.status_code == 200 and r.json()["success"] is True

    r = client.post("/ui/proxy", json={"method": "PATCH", "url": "http://x", "body": "data"})
    assert r.status_code == 200 and r.json()["success"] is True


def _install_fake_redis(monkeypatch, dataset):
    import app.api.routers.ui as ui_mod

    class Module:
        Redis = lambda self, **kwargs: FakeRedis(dataset)

    monkeypatch.setitem(ui_mod.sys.modules, "redis", Module())


def _install_fake_psutil(monkeypatch):
    import app.api.routers.ui as ui_mod

    class Module:
        @staticmethod
        def virtual_memory():
            return MemInfo()

        @staticmethod
        def cpu_percent(interval=0.1):
            return 12.5

    monkeypatch.setitem(ui_mod.sys.modules, "psutil", Module())


def test_debug_search_queries(monkeypatch):
    dataset = {
        "recommendations:1": json.dumps({"prompt": "beach trips", "user_id": "u1"}),
        "recommendations:2": json.dumps({"prompt": "mountain hikes", "user_id": "u2"}),
    }
    _install_fake_redis(monkeypatch, dataset)

    client = TestClient(app)
    r = client.get("/ui/debug/search-queries")
    assert r.status_code == 200 and r.json()["success"] is True
    assert r.json()["data"]["total_queries"] == 2

    r = client.get("/ui/debug/search-queries", params={"user_id": "u1"})
    assert r.status_code == 200 and r.json()["data"]["total_queries"] >= 1


def test_debug_search_queries_error(monkeypatch):
    import app.api.routers.ui as ui_mod

    class BadRedis:
        def __init__(self, *a, **k):
            pass
        def scan_iter(self, match=None):
            raise Exception("redis scan error")

    class Module:
        Redis = lambda self, **kwargs: BadRedis()

    monkeypatch.setitem(ui_mod.sys.modules, "redis", Module())
    client = TestClient(app)
    r = client.get("/ui/debug/search-queries")
    assert r.status_code == 200 and r.json()["success"] is False


def test_debug_ml_parameters(monkeypatch):
    import app.api.routers.ui as ui_mod

    # Fake services
    class FakeLLMService:
        ACTION_WEIGHTS = {"click": 1.0}
        BASE_SCORE = 0.5
        SCALE = 1.0
        timeout = 2

    class FakeResultsService:
        pass

    monkeypatch.setitem(ui_mod.sys.modules, "app.services.llm_service", types.SimpleNamespace(LLMService=FakeLLMService))
    monkeypatch.setitem(ui_mod.sys.modules, "app.services.results_service", types.SimpleNamespace(ResultsService=FakeResultsService))

    dataset = {
        "recommendations:1": json.dumps(
            {
                "recommendations": {
                    "hotels": [{"ranking_score": 0.6}, {"ranking_score": 0.9}],
                    "tours": [{"ranking_score": 0.7}],
                }
            }
        )
    }
    _install_fake_redis(monkeypatch, dataset)

    client = TestClient(app)
    r = client.get("/ui/debug/ml-parameters")
    data = r.json()
    assert r.status_code == 200 and data["success"] is True
    assert "parameters" in data["data"]


def test_debug_ml_parameters_error(monkeypatch):
    import app.api.routers.ui as ui_mod

    class Module:
        Redis = lambda self, **kwargs: (_ for _ in ()).throw(Exception("redis error"))

    monkeypatch.setitem(ui_mod.sys.modules, "redis", Module())
    client = TestClient(app)
    r = client.get("/ui/debug/ml-parameters")
    assert r.status_code == 200 and r.json()["success"] is False


def test_endpoints_listing():
    client = TestClient(app)
    r = client.get("/ui/endpoints")
    assert r.status_code == 200 and r.json()["success"] is True
    assert "endpoints" in r.json()


def test_debug_prefetch_and_pipeline_and_engine(monkeypatch):
    dataset = {
        "recommendations:1": json.dumps({"success": True, "processing_time": 1.2, "metadata": {"total_recommendations": 5}}),
        "recommendations:2": json.dumps({"success": False, "processing_time": 0.8}),
        "cache_hit:1": "1",
        "cache_miss:1": "1",
    }
    _install_fake_redis(monkeypatch, dataset)
    _install_fake_psutil(monkeypatch)

    client = TestClient(app)
    r = client.get("/ui/debug/prefetch-stats")
    assert r.status_code == 200 and r.json()["success"] is True

    r = client.get("/ui/debug/pipeline-details")
    assert r.status_code == 200 and r.json()["success"] is True

    r = client.get("/ui/debug/engine-details")
    assert r.status_code == 200 and r.json()["success"] is True


def test_debug_prefetch_pipeline_engine_errors(monkeypatch):
    import app.api.routers.ui as ui_mod

    class Module:
        Redis = lambda self, **kwargs: (_ for _ in ()).throw(Exception("redis down"))

    monkeypatch.setitem(ui_mod.sys.modules, "redis", Module())
    client = TestClient(app)
    for path in ["/ui/debug/prefetch-stats", "/ui/debug/pipeline-details", "/ui/debug/engine-details"]:
        r = client.get(path)
        assert r.status_code == 200 and r.json()["success"] is False


def test_debug_performance_metrics(monkeypatch):
    dataset = {
        "recommendations:1": json.dumps({"processing_time": 2.0, "generated_at": 9999999999}),
        "recommendations:2": json.dumps({"processing_time": 1.0, "generated_at": 9999999999}),
    }
    _install_fake_redis(monkeypatch, dataset)
    _install_fake_psutil(monkeypatch)

    client = TestClient(app)
    r = client.get("/ui/debug/performance-metrics")
    assert r.status_code == 200 and r.json()["success"] is True


def test_debug_performance_metrics_error(monkeypatch):
    import app.api.routers.ui as ui_mod

    class Module:
        Redis = lambda self, **kwargs: (_ for _ in ()).throw(Exception("redis err"))

    monkeypatch.setitem(ui_mod.sys.modules, "redis", Module())
    client = TestClient(app)
    r = client.get("/ui/debug/performance-metrics")
    assert r.status_code == 200 and r.json()["success"] is False


def test_tests_list_and_view(tmp_path, monkeypatch):
    # Ensure tests directory exists and contains a file
    tests_dir = Path("tests")
    sample = tests_dir / "test_sample_view.py"
    sample.write_text("def test_sample():\n    assert True\n", encoding="utf-8")

    client = TestClient(app)
    r = client.get("/ui/tests/list")
    assert r.status_code == 200 and r.json()["success"] is True
    assert any(f["name"] == "test_sample_view.py" for f in r.json()["files"])

    r = client.get("/ui/tests/view", params={"path": str(sample)})
    assert r.status_code == 200 and r.json()["success"] is True

    r = client.get("/ui/tests/view", params={"path": "../secrets.txt"})
    assert r.status_code in (400, 200)  # API returns 400 as HTTPException
    if r.status_code == 200:
        # when caught, response uses JSONResponse with success False
        assert r.json().get("success") in (False,)

    # Not found case
    r = client.get("/ui/tests/view", params={"path": "tests/does_not_exist.py"})
    assert r.status_code in (404, 200)
    if r.status_code == 200:
        assert r.json().get("success") is False


def test_run_tests_endpoint_creates_summary(monkeypatch):
    import app.api.routers.ui as ui_mod
    import subprocess as real_subprocess

    # Use the same root calculation as the endpoint (parents[3] from ui.py file)
    project_root = Path(ui_mod.__file__).resolve().parents[3]

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        # Simulate pytest execution by writing artifacts
        write_fake_pytest_artifacts(project_root, tests_passed=3, tests_failed=0)
        proc = types.SimpleNamespace(returncode=0, stdout="OK", stderr="")
        return proc

    monkeypatch.setattr(ui_mod.subprocess, "run", fake_run)

    client = TestClient(app)
    r = client.post("/ui/tests/run", json={"file": "ALL"})
    assert r.status_code == 200 and r.json()["success"] is True
    body = r.json()
    assert body["totals"]["passed"] >= 1
    assert "coverage" in body


def test_run_tests_endpoint_single_file_branch(monkeypatch):
    import app.api.routers.ui as ui_mod

    project_root = Path(ui_mod.__file__).resolve().parents[3]
    report_path = project_root / "test-results.json"
    coverage_xml = project_root / "coverage.xml"

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        # Write artifacts with single-file coverage for test_ui_router.py
        summary = {
            "summary": {"total": 2, "passed": 2, "failed": 0, "skipped": 0, "xpassed": 0, "xfailed": 0, "warnings": 0},
            "tests": [
                {"nodeid": "tests/test_ui_router.py::test_a", "outcome": "passed"},
                {"nodeid": "tests/test_ui_router.py::test_b", "outcome": "passed"},
            ],
        }
        report_path.write_text(json.dumps(summary), encoding="utf-8")
        # selected becomes "test_ui_router.py" for file param starting with tests/
        coverage_xml.write_text(
            """
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="tests/test_ui_router.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
            <line number="3" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
            """.strip(),
            encoding="utf-8",
        )
        return types.SimpleNamespace(returncode=0, stdout="OK", stderr="")

    monkeypatch.setattr(ui_mod.subprocess, "run", fake_run)
    client = TestClient(app)
    r = client.post("/ui/tests/run", json={"file": "tests/test_ui_router.py"})
    assert r.status_code == 200
    data = r.json()
    assert data["is_single_file"] is True
    assert data["coverage"]["overall_percent"] > 0


def test_run_tests_endpoint_missing_artifacts(monkeypatch):
    import app.api.routers.ui as ui_mod

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        # Do not write any files
        return types.SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(ui_mod.subprocess, "run", fake_run)
    client = TestClient(app)
    r = client.post("/ui/tests/run", json={"file": "ALL"})
    assert r.status_code == 200 and r.json()["success"] is True


def test_run_tests_endpoint_bad_xml(monkeypatch):
    import app.api.routers.ui as ui_mod
    project_root = Path(ui_mod.__file__).resolve().parents[3]

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        # write only bad coverage.xml
        (project_root / "test-results.json").write_text(json.dumps({"summary": {"total": 0}}), encoding="utf-8")
        (project_root / "coverage.xml").write_text("<not-xml>", encoding="utf-8")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ui_mod.subprocess, "run", fake_run)
    client = TestClient(app)
    r = client.post("/ui/tests/run", json={"file": "ALL"})
    assert r.status_code == 200 and r.json()["success"] is True


def test_performance_metrics_no_data(monkeypatch):
    _install_fake_redis(monkeypatch, {})
    _install_fake_psutil(monkeypatch)
    client = TestClient(app)
    r = client.get("/ui/debug/performance-metrics")
    assert r.status_code == 200 and r.json()["success"] is True


def test_run_tests_endpoint_rich_tables(monkeypatch):
    import app.api.routers.ui as ui_mod
    project_root = Path(ui_mod.__file__).resolve().parents[3]
    report_path = project_root / "test-results.json"
    coverage_xml = project_root / "coverage.xml"

    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        tests_entries = []
        # a.py: 10/10 passed
        tests_entries += [{"nodeid": "tests/a.py::t%02d" % i, "outcome": "passed"} for i in range(10)]
        # b.py: 8/10 passed
        tests_entries += [{"nodeid": "tests/b.py::t%02d" % i, "outcome": "passed"} for i in range(8)]
        tests_entries += [{"nodeid": "tests/b.py::t%02d" % i, "outcome": "failed"} for i in range(8, 10)]
        # c.py: 5/10 passed
        tests_entries += [{"nodeid": "tests/c.py::t%02d" % i, "outcome": "passed"} for i in range(5)]
        tests_entries += [{"nodeid": "tests/c.py::t%02d" % i, "outcome": "failed"} for i in range(5, 10)]
        # d.py: 2/10 passed
        tests_entries += [{"nodeid": "tests/d.py::t%02d" % i, "outcome": "passed"} for i in range(2)]
        tests_entries += [{"nodeid": "tests/d.py::t%02d" % i, "outcome": "failed"} for i in range(2, 10)]

        summary = {
            "summary": {"total": len(tests_entries), "passed": 25, "failed": len(tests_entries) - 25, "skipped": 0, "xpassed": 0, "xfailed": 0, "warnings": 0},
            "tests": tests_entries,
        }
        report_path.write_text(json.dumps(summary), encoding="utf-8")

        # Coverage classes with different percents to hit all badge branches
        coverage_xml.write_text(
            """
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="app/mod_high.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
            <line number="3" hits="1"/>
            <line number="4" hits="1"/>
            <line number="5" hits="1"/>
            <line number="6" hits="1"/>
            <line number="7" hits="1"/>
            <line number="8" hits="1"/>
            <line number="9" hits="1"/>
            <line number="10" hits="0"/>
          </lines>
        </class>
        <class filename="app/mod_good.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
            <line number="3" hits="1"/>
            <line number="4" hits="1"/>
            <line number="5" hits="0"/>
          </lines>
        </class>
        <class filename="app/mod_fair.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
            <line number="3" hits="0"/>
            <line number="4" hits="0"/>
          </lines>
        </class>
        <class filename="app/mod_poor.py">
          <lines>
            <line number="1" hits="0"/>
            <line number="2" hits="0"/>
            <line number="3" hits="0"/>
            <line number="4" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
            """.strip(),
            encoding="utf-8",
        )
        return types.SimpleNamespace(returncode=0, stdout="OK", stderr="")

    monkeypatch.setattr(ui_mod.subprocess, "run", fake_run)
    client = TestClient(app)
    r = client.post("/ui/tests/run", json={"file": "ALL"})
    assert r.status_code == 200 and r.json()["success"] is True


