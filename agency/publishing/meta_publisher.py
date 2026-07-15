"""Meta Graph API – Facebook-Seite und Instagram-Business-Konto.

Facebook-Seiten-Post: einfacher Graph-Call (Token im Body).
Instagram: zweistufig (Media-Container erstellen -> veröffentlichen) und braucht
ein ÖFFENTLICH gehostetes Bild/Video (image_url/video_url). Lokale Clips müssen
vorher gehostet werden – im Dry-Run wird darauf hingewiesen.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .base import PlatformPublisher, Post, PublishResult

GRAPH = "https://graph.facebook.com/v21.0"


def _post_form(url: str, data: dict[str, str]) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fester Graph-Host
        return json.loads(resp.read().decode())


class FacebookPublisher(PlatformPublisher):
    key = "facebook"
    name = "Facebook"
    required_env = ["FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN"]
    requires_media = False

    def _post_live(self, post: Post, creds: dict[str, str | None]) -> PublishResult:
        page_id = creds["FB_PAGE_ID"]
        token = creds["FB_PAGE_ACCESS_TOKEN"]
        result = _post_form(
            f"{GRAPH}/{page_id}/feed",
            {"message": post.text, "access_token": token or ""},
        )
        post_id = result.get("id")
        return PublishResult(
            platform=self.key, ok=bool(post_id), dry_run=False,
            action="Facebook-Seiten-Post veröffentlicht",
            url=(f"https://facebook.com/{post_id}" if post_id else None),
            error=None if post_id else f"Unerwartete Antwort: {result!r}",
        )


class InstagramPublisher(PlatformPublisher):
    key = "instagram"
    name = "Instagram"
    required_env = ["IG_USER_ID", "IG_ACCESS_TOKEN"]
    requires_media = True  # IG kann nicht text-only posten

    def validate(self, post: Post) -> list[str]:
        errors = super().validate(post)
        if not post.media_urls:
            errors.append(
                "Instagram braucht eine öffentlich gehostete Medien-URL "
                "(image_url/video_url) – lokale Dateien vorher hosten."
            )
        return errors

    def _post_live(self, post: Post, creds: dict[str, str | None]) -> PublishResult:
        ig_id = creds["IG_USER_ID"]
        token = creds["IG_ACCESS_TOKEN"] or ""
        media_url = post.media_urls[0]
        is_video = media_url.lower().endswith((".mp4", ".mov"))
        params = {"caption": post.text, "access_token": token}
        params["video_url" if is_video else "image_url"] = media_url
        if is_video:
            params["media_type"] = "REELS"

        container = _post_form(f"{GRAPH}/{ig_id}/media", params)
        creation_id = container.get("id")
        if not creation_id:
            return PublishResult(
                platform=self.key, ok=False, dry_run=False,
                action="Media-Container fehlgeschlagen", error=f"{container!r}",
            )
        published = _post_form(
            f"{GRAPH}/{ig_id}/media_publish",
            {"creation_id": creation_id, "access_token": token},
        )
        media_id = published.get("id")
        return PublishResult(
            platform=self.key, ok=bool(media_id), dry_run=False,
            action="Instagram-Post veröffentlicht",
            url=(f"https://instagram.com/p/{media_id}" if media_id else None),
            error=None if media_id else f"Publish fehlgeschlagen: {published!r}",
        )
