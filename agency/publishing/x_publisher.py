"""X (Twitter) API v2 – Tweet/Thread posten.

Echtes Posten nutzt OAuth 1.0a User-Context. Das Signieren übernimmt die
optionale Bibliothek `tweepy` (lazy import), damit der Dry-Run ganz ohne
Zusatz-Abhängigkeiten läuft.
"""

from __future__ import annotations

import re

from .base import PlatformPublisher, Post, PublishResult

X_LIMIT = 280


class XPublisher(PlatformPublisher):
    key = "x"
    name = "X (Twitter)"
    required_env = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]
    requires_media = False

    def validate(self, post: Post) -> list[str]:
        # X: einzelne Tweets müssen je <= 280 Zeichen sein (Thread erlaubt).
        errors: list[str] = []
        tweets = self._split_thread(post.text)
        if not tweets:
            errors.append("Leerer Tweet.")
        for i, t in enumerate(tweets, 1):
            if len(t) > X_LIMIT:
                errors.append(f"Tweet {i} zu lang: {len(t)} > {X_LIMIT} Zeichen.")
        return errors

    @staticmethod
    def _split_thread(text: str) -> list[str]:
        """Zerlegt einen (ggf. nummerierten) Thread in einzelne Tweets.

        Erkennt Muster wie '1/', '1.', '(1/5)' am Zeilenanfang; sonst Absätze.
        """
        text = (text or "").strip()
        if not text:
            return []
        # Nummerierte Thread-Marker am Zeilenanfang -> an diesen splitten.
        parts = re.split(r"\n(?=\s*\(?\d+\s*[/.)])", text)
        if len(parts) > 1:
            return [p.strip() for p in parts if p.strip()]
        # sonst: Doppel-Zeilenumbruch als Absatz-/Tweet-Grenze, aber nur wenn nötig.
        if len(text) <= X_LIMIT:
            return [text]
        return [p.strip() for p in text.split("\n\n") if p.strip()]

    def _post_live(self, post: Post, creds: dict[str, str | None]) -> PublishResult:
        try:
            import tweepy  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Paket 'tweepy' nicht installiert. Für echtes X-Posten: pip install tweepy"
            ) from exc

        client = tweepy.Client(
            consumer_key=creds["X_API_KEY"],
            consumer_secret=creds["X_API_SECRET"],
            access_token=creds["X_ACCESS_TOKEN"],
            access_token_secret=creds["X_ACCESS_SECRET"],
        )
        tweets = self._split_thread(post.text)
        reply_to = None
        first_id = None
        for t in tweets:
            resp = client.create_tweet(text=t, in_reply_to_tweet_id=reply_to)
            tid = resp.data["id"]
            reply_to = tid
            first_id = first_id or tid
        return PublishResult(
            platform=self.key, ok=bool(first_id), dry_run=False,
            action=f"{len(tweets)} Tweet(s) veröffentlicht",
            url=(f"https://x.com/i/web/status/{first_id}" if first_id else None),
        )
