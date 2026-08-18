"""Dashboard: erzeugt eine lokale HTML-Übersicht (Entwürfe, gepostet, Performance)."""

from .state import gather_state
from .html import render_html

__all__ = ["gather_state", "render_html"]
