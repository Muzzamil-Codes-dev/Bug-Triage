from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"

NOT_BUILT_PAGE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Bug Triage</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 40rem; margin: 4rem auto; padding: 0 1rem;">
  <h1>The frontend has not been built yet</h1>
  <p>Start the app with <code>uv run bug-triage-project</code> (it builds the
  frontend automatically), or build it yourself:</p>
  <pre>cd frontend
npm install
npm run build</pre>
  <p>The API is running: see <a href="/docs">/docs</a>.</p>
</body>
</html>"""


def mount_frontend(app: FastAPI, dist: Path = FRONTEND_DIST) -> None:
    """Serve the built React app at "/".

    Must be called after the API routes are registered, because a mount
    at "/" catches every path that no earlier route matched.
    """
    if (dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
        return

    @app.get("/", include_in_schema=False)
    def frontend_not_built():
        return HTMLResponse(NOT_BUILT_PAGE)
