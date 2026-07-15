"""YouTube Data API v3 – Video-Upload.

YouTube "posten" = ein Video hochladen. Das braucht zwingend eine fertige
Videodatei (dein zusammengeschnittenes Video) sowie OAuth2-Zugangsdaten.
Der echte Upload nutzt die optionalen Google-Bibliotheken (lazy import).
"""

from __future__ import annotations

from pathlib import Path

from .base import PlatformPublisher, Post, PublishResult


class YouTubePublisher(PlatformPublisher):
    key = "youtube"
    name = "YouTube"
    required_env = ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"]
    requires_media = True  # Upload braucht eine Videodatei

    def validate(self, post: Post) -> list[str]:
        errors: list[str] = []
        if not (post.title or "").strip():
            errors.append("YouTube-Upload braucht einen Titel.")
        video_files = [p for p in post.media if str(p).lower().endswith((".mp4", ".mov"))]
        if not video_files:
            errors.append(
                "YouTube-Upload braucht eine fertige Videodatei (.mp4/.mov). "
                "Das System liefert bisher nur das Schnitt-Briefing – Video separat erstellen."
            )
        if post.title and len(post.title) > 100:
            errors.append(f"Titel zu lang: {len(post.title)} > 100 Zeichen.")
        return errors

    def _post_live(self, post: Post, creds: dict[str, str | None]) -> PublishResult:
        try:
            from google.oauth2.credentials import Credentials  # type: ignore
            from googleapiclient.discovery import build  # type: ignore
            from googleapiclient.http import MediaFileUpload  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Google-Bibliotheken fehlen. Für echten YouTube-Upload: "
                "pip install google-api-python-client google-auth google-auth-oauthlib"
            ) from exc

        creds_obj = Credentials(
            token=None,
            refresh_token=creds["YT_REFRESH_TOKEN"],
            client_id=creds["YT_CLIENT_ID"],
            client_secret=creds["YT_CLIENT_SECRET"],
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )
        youtube = build("youtube", "v3", credentials=creds_obj)
        video = next(
            Path(p) for p in post.media if str(p).lower().endswith((".mp4", ".mov"))
        )
        body = {
            "snippet": {
                "title": post.title,
                "description": post.description or post.text,
            },
            "status": {"privacyStatus": "private"},  # sicher: startet privat
        }
        request = youtube.videos().insert(
            part="snippet,status", body=body,
            media_body=MediaFileUpload(str(video), resumable=True),
        )
        response = request.execute()
        vid = response.get("id")
        return PublishResult(
            platform=self.key, ok=bool(vid), dry_run=False,
            action="YouTube-Video hochgeladen (privat)",
            url=(f"https://youtu.be/{vid}" if vid else None),
            warnings=["Video ist auf 'privat' gesetzt – manuell auf öffentlich schalten."],
        )
