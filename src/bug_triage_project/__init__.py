import argparse
import os
import subprocess
import threading
import webbrowser

import uvicorn

from bug_triage_project import frontend


def _ensure_frontend_built() -> None:
    if not frontend.needs_build():
        return

    print("Building the frontend...", flush=True)
    try:
        frontend.build()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Could not build the frontend: {error}", flush=True)
        print("The API will still run; see /docs.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Bug Triage web app (API + React frontend).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="don't open the app in a web browser",
    )
    args = parser.parse_args()

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    _ensure_frontend_built()

    if not args.no_browser:
        browse_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
        url = f"http://{browse_host}:{port}"
        threading.Timer(1.5, webbrowser.open, args=[url]).start()

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        app_dir=str(frontend.PROJECT_ROOT),
    )
