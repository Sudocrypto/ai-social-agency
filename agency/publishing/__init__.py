"""Phase 2: Auto-Posting-Adapter pro Plattform.

Formatiert & postet freigegebenen Content über die Plattform-APIs. Default ist
Dry-Run (nur Validierung/Vorschau, kein Netz). Echtes Posten passiert nur mit
--live und nach ausdrücklicher Bestätigung – es ist nach außen wirksam und nicht
umkehrbar.
"""

from .base import Post, PublishResult, PlatformPublisher
from .registry import get_publisher, PUBLISHERS

__all__ = ["Post", "PublishResult", "PlatformPublisher", "get_publisher", "PUBLISHERS"]
