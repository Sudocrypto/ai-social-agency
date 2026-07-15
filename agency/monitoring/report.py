"""Wertet Video-Stats aus: Engagement, Ranking, Report + Metrik-CSV-Export."""

from __future__ import annotations

import csv
import io


def engagement_rate(stat: dict) -> float:
    """(Likes + Kommentare) / Views, in Prozent. 0 bei 0 Views (keine Division)."""
    views = stat.get("views", 0) or 0
    if views <= 0:
        return 0.0
    inter = (stat.get("likes", 0) or 0) + (stat.get("comments", 0) or 0)
    return round(inter / views * 100, 2)


def rank(stats: list[dict]) -> list[dict]:
    """Kopiert Stats mit Engagement-Rate, sortiert nach Views absteigend."""
    enriched = [{**s, "engagement_pct": engagement_rate(s)} for s in stats]
    return sorted(enriched, key=lambda s: s.get("views", 0), reverse=True)


def build_report(stats: list[dict]) -> str:
    """Markdown-Report: Kennzahlen-Summe + Ranking + bester/schwächster Post."""
    if not stats:
        return "# Monitoring\n\n_Keine Daten. Erst Videos tracken und Stats abrufen._\n"

    ranked = rank(stats)
    total_views = sum(s.get("views", 0) for s in stats)
    total_likes = sum(s.get("likes", 0) for s in stats)
    total_comments = sum(s.get("comments", 0) for s in stats)
    best = max(ranked, key=lambda s: s["engagement_pct"])

    L = ["# Monitoring – YouTube-Performance", ""]
    L.append(f"**Videos:** {len(stats)}  ")
    L.append(f"**Views gesamt:** {total_views:,}  ".replace(",", "."))
    L.append(f"**Likes gesamt:** {total_likes:,}  ".replace(",", "."))
    L.append(f"**Kommentare gesamt:** {total_comments:,}".replace(",", "."))
    L.append("")
    L.append("## Ranking (nach Views)")
    L.append("| # | Titel | Views | Likes | Kommentare | Engagement % |")
    L.append("|---|---|---:|---:|---:|---:|")
    for i, s in enumerate(ranked, 1):
        titel = (s.get("titel", "") or s.get("video_id", ""))[:50]
        L.append(
            f"| {i} | {titel} | {s.get('views', 0)} | {s.get('likes', 0)} | "
            f"{s.get('comments', 0)} | {s['engagement_pct']} |"
        )
    L.append("")
    L.append("## Auffälligkeiten")
    L.append(f"- **Bestes Engagement:** {best.get('titel') or best.get('video_id')} "
             f"({best['engagement_pct']} %)")
    L.append(f"- **Meiste Views:** {ranked[0].get('titel') or ranked[0].get('video_id')} "
             f"({ranked[0].get('views', 0)})")
    L.append("")
    return "\n".join(L)


def to_metrics_csv(stats: list[dict]) -> str:
    """CSV im Format, das run.py --metrics direkt versteht (plattform-Spalte)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["plattform", "titel", "views", "likes", "comments", "engagement_pct"])
    for s in rank(stats):
        w.writerow([
            "youtube", s.get("titel", ""), s.get("views", 0),
            s.get("likes", 0), s.get("comments", 0), s["engagement_pct"],
        ])
    return buf.getvalue()
