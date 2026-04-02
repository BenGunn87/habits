#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
SITE_FILE = CONTENT_DIR / "site.json"
ARTICLES_DIR = CONTENT_DIR / "articles"
RESOURCES_DIR = CONTENT_DIR / "resources"
EXERCISES_DIR = CONTENT_DIR / "exercises"

SLUG_RE = re.compile(r"^[a-z0-9-]+$")
FRONTMATTER_RE = re.compile(r"\A\+\+\+\n(.*?)\n\+\+\+\n?(.*)\Z", re.DOTALL)

RESOURCE_HIGHLIGHT_HEADINGS = {"главное", "highlights"}
EXERCISE_SECTION_ALIASES = {
    "benefits": {"польза", "benefits"},
    "steps": {"шаги", "steps"},
    "cautions": {"осторожность", "ограничения", "cautions"},
}

SITE_REQUIRED_KEYS = {
    "title",
    "tagline",
    "description",
    "heroIntro",
    "disclaimer",
    "githubPagesNotes",
    "featuredArticleSlugs",
    "featuredResourceSlugs",
    "featuredExerciseSlugs",
}


class ContentError(ValueError):
    pass


def load_content() -> dict:
    site = load_site_config()
    articles = load_articles()
    resources = load_resources()
    exercises = load_exercises()

    data = {
        "site": site,
        "articles": articles,
        "resources": resources,
        "exercises": exercises,
    }
    validate_featured_slugs(data)
    return data


def load_site_config() -> dict:
    if not SITE_FILE.exists():
        raise ContentError(f"Missing site config: {SITE_FILE}")

    site = json.loads(SITE_FILE.read_text(encoding="utf-8"))
    if not isinstance(site, dict):
        raise ContentError(f"{SITE_FILE}: top-level JSON value must be an object")

    missing = sorted(SITE_REQUIRED_KEYS - set(site))
    if missing:
        raise ContentError(f"{SITE_FILE}: missing required keys: {', '.join(missing)}")

    list_keys = {
        "githubPagesNotes",
        "featuredArticleSlugs",
        "featuredResourceSlugs",
        "featuredExerciseSlugs",
    }
    for key, value in site.items():
        if key in list_keys:
            if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
                raise ContentError(f"{SITE_FILE}: '{key}' must be a non-empty string list")
        elif not isinstance(value, str) or not value.strip():
            raise ContentError(f"{SITE_FILE}: '{key}' must be a non-empty string")

    return site


def load_articles() -> list[dict]:
    required = ("title", "summary", "category", "readTime")
    items = []
    for path, frontmatter, body in iter_documents(ARTICLES_DIR):
        validate_required_fields(path, frontmatter, required)
        items.append(
            {
                "slug": path.stem,
                "title": frontmatter["title"],
                "summary": frontmatter["summary"],
                "category": frontmatter["category"],
                "readTime": frontmatter["readTime"],
                "sections": parse_article_sections(path, body),
            }
        )
    return items


def load_resources() -> list[dict]:
    required = ("title", "summary", "format", "pages", "audience", "downloadLabel")
    items = []
    for path, frontmatter, body in iter_documents(RESOURCES_DIR):
        validate_required_fields(path, frontmatter, required)
        pages = frontmatter["pages"]
        if not isinstance(pages, int) or pages <= 0:
            raise ContentError(f"{path}: 'pages' must be a positive integer")

        items.append(
            {
                "slug": path.stem,
                "title": frontmatter["title"],
                "summary": frontmatter["summary"],
                "format": frontmatter["format"],
                "pages": pages,
                "audience": frontmatter["audience"],
                "downloadLabel": frontmatter["downloadLabel"],
                "coverPath": f"assets/images/resource-{path.stem}.svg",
                "filePath": f"assets/files/{path.stem}.pdf",
                "highlights": parse_list_section(
                    path,
                    body,
                    RESOURCE_HIGHLIGHT_HEADINGS,
                    "resource highlights",
                ),
            }
        )
    return items


def load_exercises() -> list[dict]:
    required = ("title", "summary", "duration", "level", "focus", "videoNote")
    items = []
    for path, frontmatter, body in iter_documents(EXERCISES_DIR):
        validate_required_fields(path, frontmatter, required)
        section_map = parse_named_list_sections(path, body)
        items.append(
            {
                "slug": path.stem,
                "title": frontmatter["title"],
                "summary": frontmatter["summary"],
                "duration": frontmatter["duration"],
                "level": frontmatter["level"],
                "focus": frontmatter["focus"],
                "videoNote": frontmatter["videoNote"],
                "posterPath": f"assets/images/poster-{path.stem}.svg",
                "videoPath": f"assets/media/{path.stem}.mp4",
                "benefits": require_named_section(path, section_map, EXERCISE_SECTION_ALIASES["benefits"], "benefits"),
                "steps": require_named_section(path, section_map, EXERCISE_SECTION_ALIASES["steps"], "steps"),
                "cautions": require_named_section(path, section_map, EXERCISE_SECTION_ALIASES["cautions"], "cautions"),
            }
        )
    return items


def iter_documents(directory: Path) -> list[tuple[Path, dict, str]]:
    if not directory.exists():
        raise ContentError(f"Missing content directory: {directory}")

    documents = []
    for path in sorted(directory.glob("*.md")):
        validate_slug(path)
        frontmatter, body = parse_document(path)
        documents.append((path, frontmatter, body))
    if not documents:
        raise ContentError(f"No markdown files found in {directory}")
    return documents


def validate_slug(path: Path) -> None:
    slug = path.stem
    if not SLUG_RE.fullmatch(slug):
        raise ContentError(
            f"{path}: filename must be a lowercase slug using only letters, numbers, and hyphens"
        )


def parse_document(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        raise ContentError(
            f"{path}: document must start with TOML frontmatter wrapped in +++ delimiters"
        )

    frontmatter = tomllib.loads(match.group(1))
    if not isinstance(frontmatter, dict):
        raise ContentError(f"{path}: frontmatter must be a TOML table")
    body = match.group(2).strip()
    if not body:
        raise ContentError(f"{path}: markdown body cannot be empty")
    return frontmatter, body


def validate_required_fields(path: Path, frontmatter: dict, required_fields: tuple[str, ...]) -> None:
    missing = [field for field in required_fields if field not in frontmatter]
    if missing:
        raise ContentError(f"{path}: missing required fields: {', '.join(missing)}")

    for field in required_fields:
        value = frontmatter[field]
        if isinstance(value, str):
            if not value.strip():
                raise ContentError(f"{path}: '{field}' cannot be blank")
        elif field != "pages":
            raise ContentError(f"{path}: '{field}' must be a string")


def parse_article_sections(path: Path, body: str) -> list[dict]:
    sections = []
    for heading, lines in split_sections(path, body):
        paragraphs: list[str] = []
        bullets: list[str] = []
        callout: str | None = None

        for block in split_blocks(lines):
            list_items = parse_list_items(block)
            if list_items:
                bullets.extend(list_items)
                continue

            if is_callout_block(block):
                callout_text = " ".join(line[1:].strip() for line in block).strip()
                callout = callout_text if callout is None else f"{callout} {callout_text}"
                continue

            paragraphs.append(" ".join(line.strip() for line in block).strip())

        if not paragraphs and not bullets and not callout:
            raise ContentError(f"{path}: article section '{heading}' cannot be empty")

        section = {"heading": heading}
        if paragraphs:
            section["paragraphs"] = paragraphs
        if bullets:
            section["bullets"] = bullets
        if callout:
            section["callout"] = callout
        sections.append(section)

    return sections


def parse_list_section(path: Path, body: str, allowed_headings: set[str], label: str) -> list[str]:
    section_map = parse_named_list_sections(path, body)
    return require_named_section(path, section_map, allowed_headings, label)


def parse_named_list_sections(path: Path, body: str) -> dict[str, list[str]]:
    section_map: dict[str, list[str]] = {}
    for heading, lines in split_sections(path, body):
        key = normalize_heading(heading)
        if key in section_map:
            raise ContentError(f"{path}: duplicate section heading '{heading}'")

        items = []
        for block in split_blocks(lines):
            parsed = parse_list_items(block)
            if not parsed:
                raise ContentError(
                    f"{path}: section '{heading}' must contain list items that start with '- ' or '1. '"
                )
            items.extend(parsed)

        if not items:
            raise ContentError(f"{path}: section '{heading}' cannot be empty")
        section_map[key] = items
    return section_map


def require_named_section(
    path: Path,
    section_map: dict[str, list[str]],
    aliases: set[str],
    label: str,
) -> list[str]:
    for alias in aliases:
        items = section_map.get(alias)
        if items:
            return items
    expected = ", ".join(sorted(aliases))
    raise ContentError(f"{path}: missing section for {label}. Expected one of: {expected}")


def split_sections(path: Path, body: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    heading: str | None = None
    lines: list[str] = []

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            if heading is not None:
                sections.append((heading, trim_blank_edges(lines)))
            heading = line[3:].strip()
            if not heading:
                raise ContentError(f"{path}: section heading cannot be blank")
            lines = []
        else:
            lines.append(line)

    if heading is None:
        raise ContentError(f"{path}: body must contain at least one '##' section")

    sections.append((heading, trim_blank_edges(lines)))
    return sections


def split_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.strip():
            current.append(line)
            continue
        if current:
            blocks.append(current)
            current = []

    if current:
        blocks.append(current)
    return blocks


def parse_list_items(block: list[str]) -> list[str]:
    items = []
    for line in block:
        stripped = line.strip()
        if stripped.startswith("- "):
            value = stripped[2:].strip()
        else:
            match = re.match(r"\d+\.\s+(.*)", stripped)
            if not match:
                return []
            value = match.group(1).strip()
        if not value:
            return []
        items.append(value)
    return items


def is_callout_block(block: list[str]) -> bool:
    return all(line.strip().startswith(">") for line in block)


def trim_blank_edges(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def normalize_heading(value: str) -> str:
    return " ".join(value.strip().lower().split())


def validate_featured_slugs(data: dict) -> None:
    site = data["site"]
    index_map = {
        "featuredArticleSlugs": {item["slug"] for item in data["articles"]},
        "featuredResourceSlugs": {item["slug"] for item in data["resources"]},
        "featuredExerciseSlugs": {item["slug"] for item in data["exercises"]},
    }

    for key, known_slugs in index_map.items():
        missing = [slug for slug in site[key] if slug not in known_slugs]
        if missing:
            raise ContentError(f"{SITE_FILE}: unknown slug(s) in {key}: {', '.join(missing)}")
