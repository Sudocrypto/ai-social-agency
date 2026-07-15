"""Basistypen der Publishing-Schicht: Post, PublishResult, PlatformPublisher."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from ..platforms import spec


@dataclass
class Post:
    """Ein fertiger, freigegebener Beitrag für genau eine Plattform."""

    platform: str                       # Plattform-Key: x/instagram/facebook/youtube
    text: str                           # finaler Post-Text (inkl. Hashtags)
    title: str | None = None            # v.a. YouTube
    description: str | None = None
    media: list[Path] = field(default_factory=list)      # lokale Bild-/Videodateien
    media_urls: list[str] = field(default_factory=list)  # öffentlich gehostete Medien


@dataclass
class PublishResult:
    """Ergebnis eines (Dry-Run- oder echten) Post-Versuchs."""

    platform: str
    ok: bool
    dry_run: bool
    action: str                         # was getan wurde / würde
    url: str | None = None              # Link zum Post (bei echtem Posten)
    error: str | None = None
    warnings: list[str] = field(default_factory=list)


class PlatformPublisher(ABC):
    """Adapter für eine Plattform. Unterklassen kapseln die konkrete API."""

    key: str = ""
    name: str = ""
    #: Env-Variablen, die für echtes Posten vorhanden sein müssen.
    required_env: list[str] = []
    #: Plattform braucht zwingend Medien (Bild/Video)?
    requires_media: bool = False

    # --- Validierung (offline) -----------------------------------------------
    def validate(self, post: Post) -> list[str]:
        """Prüft den Post gegen Plattform-Regeln. Gibt Fehlerliste zurück (leer = ok)."""
        errors: list[str] = []
        if not post.text.strip() and not (post.title or "").strip():
            errors.append("Leerer Post-Text.")
        limit = spec(self.key).max_chars
        if len(post.text) > limit:
            errors.append(
                f"Text zu lang: {len(post.text)} > {limit} Zeichen (Plattform-Limit)."
            )
        if self.requires_media and not (post.media or post.media_urls):
            errors.append(f"{self.name} benötigt mindestens ein Medium (Bild/Video).")
        return errors

    def missing_env(self, creds: dict[str, str | None]) -> list[str]:
        """Welche Pflicht-Env-Variablen fehlen (für echtes Posten)?"""
        return [k for k in self.required_env if not creds.get(k)]

    # --- Posten --------------------------------------------------------------
    def publish(self, post: Post, creds: dict[str, str | None], *, dry_run: bool = True) -> PublishResult:
        """Postet den Beitrag – oder simuliert es im Dry-Run.

        Gemeinsamer Ablauf: validieren -> (Dry-Run: Vorschau) -> (Live: API-Call).
        """
        errors = self.validate(post)
        if errors:
            return PublishResult(
                platform=self.key, ok=False, dry_run=dry_run,
                action="Validierung fehlgeschlagen", error="; ".join(errors),
            )

        warnings: list[str] = []
        missing = self.missing_env(creds)

        if dry_run:
            action = f"WÜRDE auf {self.name} posten"
            if missing:
                warnings.append(
                    f"Für echtes Posten fehlen: {', '.join(missing)}"
                )
            return PublishResult(
                platform=self.key, ok=True, dry_run=True, action=action, warnings=warnings,
            )

        if missing:
            return PublishResult(
                platform=self.key, ok=False, dry_run=False,
                action="Abbruch (fehlende Zugangsdaten)",
                error=f"Fehlende Env-Variablen: {', '.join(missing)}",
            )
        try:
            return self._post_live(post, creds)
        except Exception as exc:  # echtes Posten darf nie unkontrolliert crashen
            return PublishResult(
                platform=self.key, ok=False, dry_run=False,
                action="API-Fehler beim Posten", error=str(exc),
            )

    @abstractmethod
    def _post_live(self, post: Post, creds: dict[str, str | None]) -> PublishResult:
        """Echter API-Call. Nur nach Validierung + Credential-Check aufgerufen."""
        raise NotImplementedError
