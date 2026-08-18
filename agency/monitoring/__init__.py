"""Monitoring: Performance veröffentlichter Videos verfolgen und auswerten.

Ablauf: veröffentlichte YouTube-Videos tracken -> echte Stats abrufen ->
Report + Metrik-CSV, die direkt in den Growth-Analysten fließt (run.py --metrics).
"""

from .tracker import Tracker, parse_video_id

__all__ = ["Tracker", "parse_video_id"]
