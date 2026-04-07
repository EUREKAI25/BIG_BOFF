"""
web_scraper.models
──────────────────
Dataclasses pour les résultats de scraping.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class AssetManifest:
    images:      list[dict] = field(default_factory=list)   # {url, local, size, error}
    videos:      list[dict] = field(default_factory=list)
    audio:       list[dict] = field(default_factory=list)
    scripts:     list[dict] = field(default_factory=list)   # JS
    stylesheets: list[dict] = field(default_factory=list)   # CSS

    @property
    def total(self) -> int:
        return (len(self.images) + len(self.videos) + len(self.audio)
                + len(self.scripts) + len(self.stylesheets))

    def to_dict(self) -> dict:
        return {
            "images":      self.images,
            "videos":      self.videos,
            "audio":       self.audio,
            "scripts":     self.scripts,
            "stylesheets": self.stylesheets,
            "total":       self.total,
        }


@dataclass
class PageResult:
    url:         str
    final_url:   str
    status_code: int
    html:        str
    dom:         dict
    assets:      AssetManifest
    depth:       int          = 0
    output_dir:  Path | None  = None
    error:       str | None   = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.html)

    def to_dict(self) -> dict:
        return {
            "url":         self.url,
            "final_url":   self.final_url,
            "status_code": self.status_code,
            "depth":       self.depth,
            "assets":      self.assets.to_dict(),
            "output_dir":  str(self.output_dir) if self.output_dir else None,
            "error":       self.error,
        }


@dataclass
class ScrapeResult:
    mode:         Literal["page", "site"]
    start_url:    str
    output_dir:   Path
    pages:        list[PageResult] = field(default_factory=list)
    duration_s:   float            = 0.0
    error:        str | None       = None

    @property
    def success(self) -> bool:
        return self.error is None and len(self.pages) > 0

    @property
    def pages_count(self) -> int:
        return len(self.pages)

    @property
    def assets_count(self) -> int:
        return sum(p.assets.total for p in self.pages)

    def to_dict(self) -> dict:
        return {
            "success":      self.success,
            "mode":         self.mode,
            "start_url":    self.start_url,
            "output_dir":   str(self.output_dir),
            "pages_count":  self.pages_count,
            "assets_count": self.assets_count,
            "duration_s":   round(self.duration_s, 2),
            "error":        self.error,
            "pages":        [p.to_dict() for p in self.pages],
        }
