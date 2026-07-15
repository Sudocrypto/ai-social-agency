"""Rendert das Dashboard als eigenständige, lokal öffenbare HTML-Datei."""

from __future__ import annotations

from html import escape

_STATUS = {
    "bereit": ("Bereit", "#1a7f37", "#dafbe1"),
    "blockiert": ("Blockiert", "#b35900", "#fff1e5"),
    "gepostet": ("Gepostet", "#0969da", "#ddf4ff"),
}
_TRI = {True: "✅", False: "⚠️", None: "–"}

CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
  margin: 0; padding: 2rem; background: #f6f8fa; color: #1f2328; }
h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
.sub { color: #656d76; margin-bottom: 1.5rem; font-size: .9rem; }
.tiles { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }
.tile { background: #fff; border: 1px solid #d0d7de; border-radius: 10px;
  padding: 1rem 1.5rem; min-width: 130px; }
.tile .n { font-size: 2rem; font-weight: 700; }
.tile .l { color: #656d76; font-size: .85rem; }
h2 { font-size: 1.15rem; margin: 2rem 0 .75rem; }
table { width: 100%; border-collapse: collapse; background: #fff;
  border: 1px solid #d0d7de; border-radius: 10px; overflow: hidden; }
th, td { text-align: left; padding: .6rem .8rem; border-bottom: 1px solid #eaeef2;
  font-size: .9rem; }
th { background: #f6f8fa; font-weight: 600; }
tr:last-child td { border-bottom: none; }
.badge { display: inline-block; padding: .15rem .55rem; border-radius: 999px;
  font-size: .78rem; font-weight: 600; }
.bar { height: 8px; background: #0969da; border-radius: 4px; min-width: 2px; }
.empty { color: #656d76; font-style: italic; padding: .5rem 0; }
a { color: #0969da; }
@media (prefers-color-scheme: dark) {
  body { background: #0d1117; color: #e6edf3; }
  .tile, table { background: #161b22; border-color: #30363d; }
  th { background: #161b22; } td, th { border-color: #21262d; }
  .sub, .tile .l, .empty { color: #8b949e; }
}
"""


def _rows_planned(packages: list[dict]) -> str:
    rows = []
    for pkg in packages:
        for p in pkg["platforms"]:
            label, fg, bg = _STATUS[p["status"]]
            rows.append(
                "<tr>"
                f"<td>{escape(pkg['date'])}</td>"
                f"<td>{escape(p['name'])}</td>"
                f"<td>{_TRI[p['director']]}</td>"
                f"<td>{_TRI[p['compliance']]}</td>"
                f'<td><span class="badge" style="color:{fg};background:{bg}">{label}</span></td>'
                "</tr>"
            )
    if not rows:
        return '<p class="empty">Noch keine Pakete erzeugt. Mit run.py generieren.</p>'
    return (
        "<table><thead><tr><th>Datum</th><th>Plattform</th><th>Director</th>"
        "<th>Compliance</th><th>Status</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table>"
    )


def _rows_posted(posts: list[dict]) -> str:
    if not posts:
        return '<p class="empty">Noch nichts gepostet.</p>'
    rows = []
    for p in posts:
        url = escape(p.get("url", ""))
        link = f'<a href="{url}">{url}</a>' if url else "–"
        rows.append(
            "<tr>"
            f"<td>{escape(p.get('when', ''))}</td>"
            f"<td>{escape(p.get('platform', ''))}</td>"
            f"<td>{escape(p.get('package_date', ''))}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Wann</th><th>Plattform</th><th>Paket</th>"
        "<th>Link</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _rows_perf(perf: list[dict]) -> str:
    if not perf:
        return ('<p class="empty">Keine Performance-Daten. '
                "Mit monitor.py fetch abrufen.</p>")
    top = max((x["views"] for x in perf), default=1) or 1
    rows = []
    for x in perf:
        w = max(2, round(x["views"] / top * 160))
        rows.append(
            "<tr>"
            f"<td>{escape(str(x['titel']))[:60]}</td>"
            f"<td>{x['views']:,}".replace(",", ".") + "</td>"
            f'<td><div class="bar" style="width:{w}px"></div></td>'
            f"<td>{x['likes']}</td><td>{x['comments']}</td>"
            f"<td>{escape(str(x['engagement_pct']))} %</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Titel</th><th>Views</th><th></th><th>Likes</th>"
        "<th>Kommentare</th><th>Engagement</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table>"
    )


def render_html(state: dict) -> str:
    c = state["counts"]
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Social Media Agentur – Dashboard</title>
<style>{CSS}</style></head><body>
<h1>Social Media Agentur – Dashboard</h1>
<div class="sub">Stand: {escape(state['generated_at'])}</div>
<div class="tiles">
  <div class="tile"><div class="n">{c['pakete']}</div><div class="l">Pakete</div></div>
  <div class="tile"><div class="n">{c['geplant']}</div><div class="l">Bereit / geplant</div></div>
  <div class="tile"><div class="n">{c['gepostet']}</div><div class="l">Gepostet</div></div>
</div>
<h2>Geplant &amp; Entwürfe</h2>
{_rows_planned(state['packages'])}
<h2>Gepostet</h2>
{_rows_posted(state['posts'])}
<h2>Performance (YouTube)</h2>
{_rows_perf(state['performance'])}
</body></html>
"""
