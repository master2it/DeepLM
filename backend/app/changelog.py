"""Parse CHANGELOG.md into JSON for the UI."""

from __future__ import annotations

import re
from pathlib import Path

from app.version import APP_VERSION

_RELEASE_RE = re.compile(
    r"^## \[(?P<version>[^\]]+)\](?:\s+[—-]\s+(?P<meta>.+))?\s*$"
)
_ITEM_RE = re.compile(r"^### (?P<title>.+?)\s*$")
_FIELD_RE = re.compile(r"^-\s+\*\*(?P<key>[^*]+):\*\*\s*(?P<value>.*)$")


def _changelog_path() -> Path:
    here = Path(__file__).resolve()
    for candidate in (
        here.parents[2] / "CHANGELOG.md",
        here.parents[1] / "CHANGELOG.md",
        Path("/app/CHANGELOG.md"),
    ):
        if candidate.is_file():
            return candidate
    return here.parents[2] / "CHANGELOG.md"


def load_changelog() -> dict:
    path = _changelog_path()
    if not path.is_file():
        return {"current": APP_VERSION, "releases": []}

    text = path.read_text(encoding="utf-8")
    releases: list[dict] = []
    current: dict | None = None
    item: dict | None = None
    past_howto = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## [") and not line.startswith("###"):
            past_howto = True
            if item and current is not None:
                current["changes"].append(item)
                item = None
            if current is not None:
                releases.append(current)
            match = _RELEASE_RE.match(line)
            version = match.group("version") if match else line
            meta = (match.group("meta") or "").strip() if match else ""
            date = ""
            kind = ""
            if meta:
                parts = [p.strip() for p in re.split(r"\s+[—-]\s+", meta)]
                if parts:
                    date = parts[0]
                if len(parts) > 1:
                    kind = parts[1]
            current = {
                "version": version,
                "date": date,
                "kind": kind,
                "notes": "",
                "changes": [],
            }
            continue

        if not past_howto:
            continue
        if current is None:
            continue
        if line.startswith("### Template") or line.startswith("```"):
            continue
        if line.strip() == "---":
            continue

        item_match = _ITEM_RE.match(line)
        if item_match:
            if item:
                current["changes"].append(item)
            item = {
                "title": item_match.group("title").strip(),
                "type": "",
                "summary": "",
                "why": "",
                "files": "",
            }
            continue

        field = _FIELD_RE.match(line)
        if field and item is not None:
            key = field.group("key").strip().lower()
            value = field.group("value").strip()
            if key == "type":
                item["type"] = value
            elif key == "summary":
                item["summary"] = value
            elif key == "why":
                item["why"] = value
            elif key == "files":
                item["files"] = value
            continue

        if line and not line.startswith("#") and item is None:
            note = current.get("notes") or ""
            current["notes"] = (note + " " + line).strip() if note else line

    if item and current is not None:
        current["changes"].append(item)
    if current is not None:
        releases.append(current)

    releases = [
        r
        for r in releases
        if r["version"] != "Unreleased" or r["changes"] or r["notes"]
    ]
    return {"current": APP_VERSION, "releases": releases}
