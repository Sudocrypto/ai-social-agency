"""Kleine Text-Helfer, die mehrere Module teilen."""

from __future__ import annotations

from .platforms import spec


def split_by_platform(markdown: str, platform_keys: list[str]) -> dict[str, str]:
    """Zerlegt Markdown anhand der '## <Plattform>'-Überschriften.

    Ordnet Abschnitte den Plattform-Keys über den Anzeigenamen zu. Findet sich
    keine Überschrift, bekommt jede Plattform den vollen Text (fail-safe).
    """
    markdown = markdown or ""
    lines = markdown.splitlines()
    marks: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        heading = line[3:].strip().lower()
        for pk in platform_keys:
            name = spec(pk).name.lower()
            short = name.split(" ")[0]  # "x", "instagram", "facebook", "youtube"
            if name in heading or short in heading:
                marks.append((i, pk))
                break

    if not marks:
        return {pk: markdown.strip() for pk in platform_keys}

    result: dict[str, str] = {}
    for idx, (start, pk) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        result[pk] = "\n".join(lines[start:end]).strip()
    for pk in platform_keys:
        result.setdefault(pk, markdown.strip())
    return result
