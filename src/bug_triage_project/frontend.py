import shutil
import subprocess
from pathlib import Path

# The application packages (api, graph, Models, prompts) and the React
# frontend live at the project root, two levels above this file.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Files whose changes require the frontend to be rebuilt.
SOURCE_FILES = ("index.html", "package.json", "vite.config.js")
SOURCE_DIRS = ("src", "public")


def _source_files(frontend_dir: Path):
    for name in SOURCE_FILES:
        path = frontend_dir / name
        if path.is_file():
            yield path
    for name in SOURCE_DIRS:
        directory = frontend_dir / name
        if directory.is_dir():
            yield from (p for p in directory.rglob("*") if p.is_file())


def needs_build(frontend_dir: Path = FRONTEND_DIR) -> bool:
    """True if dist/ is missing or older than any frontend source file."""
    index = frontend_dir / "dist" / "index.html"
    if not index.is_file():
        return True

    built_at = index.stat().st_mtime
    return any(
        path.stat().st_mtime > built_at
        for path in _source_files(frontend_dir)
    )


def build(frontend_dir: Path = FRONTEND_DIR) -> None:
    """Install frontend dependencies if needed, then run the Vite build."""
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError(
            "npm was not found. Install Node.js (https://nodejs.org) "
            "to build the frontend."
        )

    if not (frontend_dir / "node_modules").is_dir():
        subprocess.run([npm, "install"], cwd=frontend_dir, check=True)

    subprocess.run([npm, "run", "build"], cwd=frontend_dir, check=True)
