#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from content_loader import ContentError, load_content

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"


def article_href(slug: str) -> str:
    return f"habit-{slug}.html"


def exercise_href(slug: str) -> str:
    return f"exercise-{slug}.html"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    data = load_content()
    errors: list[str] = []

    article_slugs = [item["slug"] for item in data["articles"]]
    resource_slugs = [item["slug"] for item in data["resources"]]
    exercise_slugs = [item["slug"] for item in data["exercises"]]

    require(len(article_slugs) == len(set(article_slugs)), "Article slugs must be unique.", errors)
    require(len(resource_slugs) == len(set(resource_slugs)), "Resource slugs must be unique.", errors)
    require(len(exercise_slugs) == len(set(exercise_slugs)), "Exercise slugs must be unique.", errors)

    for path in [
        SITE_DIR / "index.html",
        SITE_DIR / "habits.html",
        SITE_DIR / "resources.html",
        SITE_DIR / "exercises.html",
        SITE_DIR / "404.html",
        SITE_DIR / "assets" / "css" / "styles.css",
    ]:
        require(path.exists(), f"Missing required file: {path}", errors)

    for article in data["articles"]:
        require((SITE_DIR / article_href(article["slug"])).exists(), f"Missing article page for {article['slug']}.", errors)

    media_budget = 0
    for resource in data["resources"]:
        file_path = SITE_DIR / resource["filePath"]
        require(file_path.exists(), f"Missing resource file: {file_path}", errors)
        require((SITE_DIR / resource["coverPath"]).exists(), f"Missing resource cover: {resource['coverPath']}", errors)
        if file_path.exists():
            media_budget += file_path.stat().st_size

    for exercise in data["exercises"]:
        video_path = SITE_DIR / exercise["videoPath"]
        poster_path = SITE_DIR / exercise["posterPath"]
        require((SITE_DIR / exercise_href(exercise["slug"])).exists(), f"Missing exercise page for {exercise['slug']}.", errors)
        require(video_path.exists(), f"Missing exercise video: {video_path}", errors)
        require(poster_path.exists(), f"Missing exercise poster: {poster_path}", errors)
        if video_path.exists():
            media_budget += video_path.stat().st_size
            require(video_path.stat().st_size < 5_000_000, f"Video is too large for starter GitHub Pages setup: {video_path.name}", errors)

    require(media_budget < 25_000_000, "Starter media payload exceeds 25 MB budget.", errors)

    if errors:
        for message in errors:
            print(f"ERROR: {message}")
        return 1

    print("Validation passed.")
    print(f"Checked {len(article_slugs)} articles, {len(resource_slugs)} PDFs, {len(exercise_slugs)} exercises.")
    print(f"Starter media payload: {media_budget / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ContentError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
