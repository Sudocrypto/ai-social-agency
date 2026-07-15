"""Video-Assembly (Erweiterung): baut aus Segmenten + Musik + Untertiteln eine .mp4.

Folgt dem Post-Production-Schnittplan. Der Zusammenschnitt passiert per ffmpeg;
das eigentliche Rendern läuft lokal (ffmpeg installiert). Der Dry-Run erzeugt das
ffmpeg-Kommando und die Untertitel-Datei ohne zu rendern.
"""

from .plan import AssemblyPlan, Segment, Music

__all__ = ["AssemblyPlan", "Segment", "Music"]
