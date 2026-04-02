#!/usr/bin/env python3
from __future__ import annotations

import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT / "site" / "assets" / "files"
MEDIA_DIR = ROOT / "site" / "assets" / "media"
DEMO_MP4_BASE64_FILE = ROOT / "scripts" / "demo-video.b64"


PDF_CONTENT = {
    "habit-checklist.pdf": {
        "title": "Чек-лист запуска привычки на 7 дней",
        "subtitle": "Шаблон для старта без перегруза",
        "bullets": [
            "Сформулируйте один ясный триггер.",
            "Запишите минимальный шаг на 60-120 секунд.",
            "Подготовьте среду заранее: вещи, место, время.",
            "Отмечайте факт запуска, а не идеальное качество.",
            "Если был пропуск, упростите шаг или уточните сигнал."
        ]
    },
    "environment-audit.pdf": {
        "title": "Аудит среды",
        "subtitle": "Что убрать, что подсветить",
        "bullets": [
            "Какие предметы мешают стартовать нужному действию?",
            "Какие сигналы можно сделать заметнее?",
            "Что стоит положить на видное место уже сегодня?",
            "Какой один отвлекающий фактор можно убрать на неделю?",
            "Какой эксперимент со средой вы проверите дальше?"
        ]
    },
    "weekly-review-template.pdf": {
        "title": "Еженедельный обзор",
        "subtitle": "Короткая ретроспектива без самокритики",
        "bullets": [
            "Что сработало лучше, чем ожидалось?",
            "Где привычка чаще всего ломалась?",
            "Какая среда помогала, а какая мешала?",
            "Какой один шаг стоит упростить на следующей неделе?",
            "Что важно сохранить без изменений?"
        ]
    }
}


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(title: str, subtitle: str, bullets: list[str]) -> bytes:
    lines: list[tuple[int, int, str]] = [
        (24, 740, title),
        (13, 712, subtitle),
        (11, 686, "Практика Привычек"),
    ]

    cursor = 640
    for bullet in bullets:
        lines.append((12, cursor, f"- {bullet}"))
        cursor -= 26

    stream_parts = []
    for size, y, text in lines:
        stream_parts.extend(
            [
                "BT",
                f"/F1 {size} Tf",
                f"72 {y} Td",
                f"({escape_pdf_text(text)}) Tj",
                "ET",
            ]
        )

    stream = "\n".join(stream_parts).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]

    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{index} 0 obj\n".encode("ascii"))
        chunks.append(body)
        chunks.append(b"\nendobj\n")

    xref_offset = sum(len(chunk) for chunk in chunks)
    xref_lines = [b"xref\n", f"0 {len(objects) + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref_lines.append(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        b"trailer\n"
        + f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii")
        + b"startxref\n"
        + f"{xref_offset}\n".encode("ascii")
        + b"%%EOF\n"
    )

    return b"".join(chunks + xref_lines + [trailer])


def write_demo_videos() -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    payload = base64.b64decode(DEMO_MP4_BASE64_FILE.read_text(encoding="ascii").strip())
    for filename in ("mobility-reset.mp4", "breath-and-core.mp4", "desk-reset.mp4"):
        (MEDIA_DIR / filename).write_bytes(payload)


def write_pdfs() -> None:
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    for filename, content in PDF_CONTENT.items():
        (FILES_DIR / filename).write_bytes(
            build_pdf(content["title"], content["subtitle"], content["bullets"])
        )


def main() -> None:
    write_demo_videos()
    write_pdfs()
    print("Generated media assets in site/assets.")


if __name__ == "__main__":
    main()
