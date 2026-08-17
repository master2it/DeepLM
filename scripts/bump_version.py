"""Bump patch version in VERSION, backend, and frontend."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
BACKEND_FILE = ROOT / "backend" / "app" / "version.py"
FRONTEND_TS = ROOT / "frontend" / "src" / "lib" / "version.ts"
PACKAGE_JSON = ROOT / "frontend" / "package.json"


def bump_patch(version: str) -> str:
    major, minor, patch = (int(p) for p in version.strip().split("."))
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    current = VERSION_FILE.read_text(encoding="utf-8").strip()
    nxt = bump_patch(current)
    VERSION_FILE.write_text(nxt + "\n", encoding="utf-8")
    BACKEND_FILE.write_text(
        '"""App semver. Updated by scripts/bump_version.py on each push to main."""\n\n'
        f'APP_VERSION = "{nxt}"\n',
        encoding="utf-8",
    )
    FRONTEND_TS.write_text(
        "/** App semver. Updated by scripts/bump_version.py on each push to main. */\n"
        f'export const APP_VERSION = "{nxt}";\n',
        encoding="utf-8",
    )
    pkg = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    pkg["version"] = nxt
    PACKAGE_JSON.write_text(
        json.dumps(pkg, indent=2) + "\n", encoding="utf-8"
    )
    print(nxt)


if __name__ == "__main__":
    main()
