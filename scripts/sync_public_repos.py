from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USERNAME = "lamineheskoura"
PROFILE_REPOSITORY = "lamineheskoura"
MAX_REPOSITORIES = 6


def fetch_repositories() -> list[dict[str, str]]:
    request = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/repos?type=public&sort=updated&per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "loucify-profile-sync"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        repositories = json.load(response)

    return [
        {"name": repository["name"], "url": repository["html_url"]}
        for repository in repositories
        if repository["name"].lower() != PROFILE_REPOSITORY.lower() and not repository["fork"]
    ][:MAX_REPOSITORIES]


def replace_block(content: str, start: str, end: str, replacement: str) -> str:
    pattern = re.compile(f"({re.escape(start)}).*?({re.escape(end)})", re.DOTALL)
    updated, replacements = pattern.subn(f"{start}\n{replacement}\n{end}", content, count=1)
    if replacements != 1:
        raise RuntimeError(f"Could not find a single {start} block.")
    return updated


def update_svg(repositories: list[dict[str, str]]) -> None:
    path = ROOT / "assets" / "loucify-console-v3.svg"
    content = path.read_text(encoding="utf-8")

    names = [f'{html.escape(repository["name"])}/' for repository in repositories]
    rows = [names[index:index + 2] for index in range(0, len(names), 2)] or [["(no public repositories yet)"]]
    output = []
    for index, row in enumerate(rows):
        y = 994 + index * 28
        left = row[0]
        right = row[1] if len(row) > 1 else ""
        output.append(f'    <text x="42" y="{y}" fill="#8be9fd">  {left}</text>')
        if right:
            output.append(f'    <text x="408" y="{y}" fill="#8be9fd">  {right}</text>')

    path.write_text(
        replace_block(content, "<!-- PUBLIC_REPOS:START -->", "<!-- PUBLIC_REPOS:END -->", "\n".join(output)),
        encoding="utf-8",
    )


def update_readme(repositories: list[dict[str, str]]) -> None:
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")

    if repositories:
        links = "\n  |\n  ".join(
            f'<a href="{html.escape(repository["url"], quote=True)}"><code>{html.escape(repository["name"])}/</code></a>'
            for repository in repositories
        )
        output = f'<p align="center">\n  {links}\n</p>'
    else:
        output = '<p align="center"><code>no public repositories yet</code></p>'

    path.write_text(
        replace_block(content, "<!-- PUBLIC_REPOS:START -->", "<!-- PUBLIC_REPOS:END -->", output),
        encoding="utf-8",
    )


def main() -> None:
    repositories = fetch_repositories()
    update_svg(repositories)
    update_readme(repositories)
    print(f"Synchronized {len(repositories)} public repositories.")


if __name__ == "__main__":
    main()
