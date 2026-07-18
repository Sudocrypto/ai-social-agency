"""Sammelt den Zustand für das Dashboard aus den lokalen Dateien.

Quellen: output/{datum}/ (Entwürfe + Freigabe-/Compliance-Status),
monitoring/post_log.json (was gepostet wurde), monitoring/metrics.csv (Performance).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..config import ROOT
from ..platforms import ALL_PLATFORMS, spec
from ..publishing.approval import load_approvals, load_compliance
from ..publishing.post_log import POST_LOG, load_post_log
from ..scheduling import SCHEDULE, load_schedule

OUTPUT_ROOT = ROOT / "output"
METRICS_CSV = ROOT / "monitoring" / "metrics.csv"


def _perf(metrics_csv: Path) -> list[dict]:
    if not Path(metrics_csv).exists():
        return []
    from ..metrics import Metrics

    def num(v):
        try:
            return int(float(str(v).replace(",", "")))
        except (ValueError, TypeError):
            return 0

    try:
        rows = Metrics.load(metrics_csv).rows
    except Exception:
        return []
    out = [
        {
            "titel": r.get("titel", "") or r.get("video_id", ""),
            "views": num(r.get("views")),
            "likes": num(r.get("likes")),
            "comments": num(r.get("comments")),
            "engagement_pct": r.get("engagement_pct", ""),
        }
        for r in rows
    ]
    return sorted(out, key=lambda x: x["views"], reverse=True)


def gather_state(
    output_root: Path | str = OUTPUT_ROOT,
    *,
    post_log_store: Path | str = POST_LOG,
    metrics_csv: Path | str = METRICS_CSV,
    schedule_store: Path | str = SCHEDULE,
) -> dict:
    """Baut das Zustands-Dict fürs Dashboard."""
    output_root = Path(output_root)
    posts = load_post_log(post_log_store)
    posted = {(p["platform"], p["package_date"]) for p in posts}

    packages: list[dict] = []
    if output_root.exists():
        days = sorted((d for d in output_root.iterdir() if d.is_dir()), reverse=True)
        for day in days:
            approvals = load_approvals(day)
            compliance = load_compliance(day)
            plats = []
            for pk in ALL_PLATFORMS:
                if not (day / pk / "post.md").exists():
                    continue
                director = approvals.get(pk, {}).get("approved")
                comp = compliance.get(pk, {}).get("ok")
                is_posted = (pk, day.name) in posted
                blocked = director is False or comp is False
                if is_posted:
                    status = "gepostet"
                elif blocked:
                    status = "blockiert"
                else:
                    status = "bereit"
                plats.append({
                    "platform": pk, "name": spec(pk).name,
                    "director": director, "compliance": comp,
                    "posted": is_posted, "status": status,
                })
            if plats:
                packages.append({"date": day.name, "platforms": plats})

    # Geplante Termine mit Status (gepostet / überfällig / geplant).
    now_iso = datetime.now().isoformat(timespec="minutes")
    scheduled = []
    for e in load_schedule(schedule_store):
        key = (e.get("platform"), e.get("package_date"))
        if key in posted:
            st = "gepostet"
        elif e.get("at", "") < now_iso:
            st = "überfällig"
        else:
            st = "geplant"
        scheduled.append({**e, "name": _name(e.get("platform", "")), "status": st})

    planned = sum(
        1 for pkg in packages for p in pkg["platforms"] if p["status"] == "bereit"
    )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "packages": packages,
        "scheduled": scheduled,
        "posts": sorted(posts, key=lambda p: p.get("when", ""), reverse=True),
        "performance": _perf(metrics_csv),
        "counts": {
            "pakete": len(packages),
            "geplant": planned,
            "termine": sum(1 for s in scheduled if s["status"] != "gepostet"),
            "gepostet": len(posts),
        },
    }


def _name(platform_key: str) -> str:
    try:
        return spec(platform_key).name
    except KeyError:
        return platform_key
