import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.frontend import mount_frontend
from api.main import app as api_app
from bug_triage_project.frontend import needs_build


def _app_with_api_route() -> FastAPI:
    app = FastAPI()

    @app.post("/ping")
    def ping():
        return {"ok": True}

    return app


def test_serves_built_frontend_without_hiding_api_routes(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Bug Triage UI</h1>")
    app = _app_with_api_route()

    mount_frontend(app, tmp_path)
    client = TestClient(app)

    assert "Bug Triage UI" in client.get("/").text
    assert client.post("/ping").json() == {"ok": True}


def test_shows_build_instructions_when_frontend_not_built(tmp_path):
    app = _app_with_api_route()

    mount_frontend(app, tmp_path / "missing")
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "npm run build" in response.text


def test_api_docs_still_reachable():
    assert TestClient(api_app).get("/docs").status_code == 200


def _make_frontend(tmp_path, built: bool):
    (tmp_path / "src").mkdir()
    source = tmp_path / "src" / "App.jsx"
    source.write_text("export default 1")
    os.utime(source, (1_000, 1_000))

    if built:
        (tmp_path / "dist").mkdir()
        index = tmp_path / "dist" / "index.html"
        index.write_text("<html></html>")
        os.utime(index, (2_000, 2_000))

    return source


def test_needs_build_when_never_built(tmp_path):
    _make_frontend(tmp_path, built=False)

    assert needs_build(tmp_path) is True


def test_no_build_needed_when_dist_is_newer(tmp_path):
    _make_frontend(tmp_path, built=True)

    assert needs_build(tmp_path) is False


def test_needs_build_when_source_changed_after_build(tmp_path):
    source = _make_frontend(tmp_path, built=True)
    os.utime(source, (3_000, 3_000))

    assert needs_build(tmp_path) is True
