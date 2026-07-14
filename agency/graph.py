"""Abhängigkeitsgraph der Pipeline – ermöglicht optionale parallele Ausführung.

Die Fachagents "liefern parallel" (siehe Spec-Workflow), hängen aber teils
voneinander ab. Hier stehen die Abhängigkeiten explizit; der Scheduler leitet
daraus Ebenen ab, die je Ebene parallel laufen können. Default bleibt
sequenziell (transparent/debugbar) – Parallelität ist opt-in.
"""

from __future__ import annotations

# step.key -> Liste von step.keys, die vorher fertig sein müssen.
DEPENDENCIES: dict[str, list[str]] = {
    "trend_scout": [],
    "content_strategist": ["trend_scout"],
    "copywriter": ["content_strategist"],
    "video_scriptwriter": ["content_strategist"],
    "post_production": ["video_scriptwriter"],
    "visual_designer": ["content_strategist", "post_production"],
    "seo_hashtag": ["copywriter"],
    "community_manager": ["copywriter"],
    "video_producer": ["visual_designer"],
    "editor": ["copywriter"],
    "publisher": ["editor", "seo_hashtag"],
    "growth_analyst": [],
    "creative_director": ["publisher"],
}


def compute_levels(step_keys: list[str], deps: dict[str, list[str]] = DEPENDENCIES) -> list[list[str]]:
    """Ordnet Schritte in Ebenen (Longest-Path-Topologie).

    Ebene N enthält nur Schritte, deren Abhängigkeiten alle in Ebenen < N liegen.
    Innerhalb einer Ebene sind die Schritte unabhängig und dürfen parallel laufen.
    Reihenfolge innerhalb einer Ebene folgt der Eingabereihenfolge (stabil).
    """
    present = set(step_keys)
    level_of: dict[str, int] = {}

    def resolve(key: str, stack: frozenset[str]) -> int:
        if key in level_of:
            return level_of[key]
        if key in stack:
            raise ValueError(f"Zyklus im Abhängigkeitsgraph bei '{key}'")
        # Nur vorhandene Abhängigkeiten berücksichtigen.
        d = [k for k in deps.get(key, []) if k in present]
        lvl = 0 if not d else 1 + max(resolve(k, stack | {key}) for k in d)
        level_of[key] = lvl
        return lvl

    for k in step_keys:
        resolve(k, frozenset())

    max_level = max(level_of.values(), default=-1)
    levels: list[list[str]] = [[] for _ in range(max_level + 1)]
    for k in step_keys:  # stabile Reihenfolge
        levels[level_of[k]].append(k)
    return levels
