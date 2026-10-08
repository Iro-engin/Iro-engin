#!/usr/bin/env python3
"""Refresh generated sections of the GitHub profile README."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
CONFIG_PATH = ROOT / "profile.json"


def github_get(path: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Iro-engin-profile-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"https://api.github.com{path}", headers=headers
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def normalize_description(value: str | None) -> str:
    if not value:
        return "Public project"
    return " ".join(value.split())


def render_recent_work(
    username: str, repository_names: list[str], token: str | None
) -> str:
    lines: list[str] = []
    for name in repository_names:
        repo = github_get(f"/repos/{username}/{name}", token)
        language = repo.get("language") or "Mixed"
        description = normalize_description(repo.get("description"))
        lines.append(
            f"- [**{name}**]({repo['html_url']}) — {language} · {description}"
        )
    return "\n".join(lines)


def render_oss_contributions(
    username: str, limit: int, token: str | None
) -> str:
    query = urllib.parse.quote(f"author:{username} is:pr -user:{username}")
    result = github_get(
        f"/search/issues?q={query}&sort=created&order=desc&per_page=50", token
    )
    lines: list[str] = []
    own_prefix = f"https://api.github.com/repos/{username}/"

    for item in result.get("items", []):
        repository_url = item.get("repository_url", "")
        if repository_url.startswith(own_prefix):
            continue
        merged = bool(item.get("pull_request", {}).get("merged_at"))
        if item.get("state") != "open" and not merged:
            continue
        repository = repository_url.removeprefix("https://api.github.com/repos/")
        status = "merged" if merged else "open"
        lines.append(
            f"- [**{repository} #{item['number']}**]({item['html_url']}) — "
            f"{item['title']} ({status} PR)"
        )
        if len(lines) >= limit:
            break

    if not lines:
        return "Recent external pull requests will appear here."
    return "\n".join(lines)


def replace_section(document: str, name: str, content: str) -> str:
    pattern = re.compile(
        rf"(<!-- {re.escape(name)}:start -->\n).*?(\n<!-- {re.escape(name)}:end -->)",
        re.DOTALL,
    )
    updated, count = pattern.subn(rf"\g<1>{content}\g<2>", document)
    if count != 1:
        raise ValueError(f"Expected exactly one generated section named {name!r}")
    return updated


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    token = os.getenv("GITHUB_TOKEN")
    username = config["github_user"]
    readme = README_PATH.read_text(encoding="utf-8")

    readme = replace_section(
        readme,
        "recent-work",
        render_recent_work(username, config["featured_repositories"], token),
    )
    readme = replace_section(
        readme,
        "oss-contributions",
        render_oss_contributions(
            username, int(config["max_oss_contributions"]), token
        ),
    )
    README_PATH.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
