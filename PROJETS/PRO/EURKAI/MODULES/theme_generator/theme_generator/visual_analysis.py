"""
theme_generator.visual_analysis
────────────────────────────────
Adaptateur pluggable : source visuelle → StyleDNA.

L'interface est fixe. L'implémentation est interchangeable.
Aucune logique métier ne dépend d'un adaptateur spécifique.

MVP : Mock, Json, Preset — pas de vision LLM.
Futur : ClaudeVision, GPTVision, HeuristicAnalysis.
"""

from __future__ import annotations
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .style_dna import StyleDNA, style_dna_from_dict


# ─── Source ──────────────────────────────────────────────────────────────────

@dataclass
class VisualSource:
    """Décrit la source à analyser."""
    type:     str                  # image | screenshot | logo | mockup | preset | manual
    path:     Optional[Path] = None
    url:      Optional[str]  = None
    raw_json: Optional[dict] = None   # injection directe (MVP / tests)


# ─── Interface ───────────────────────────────────────────────────────────────

class VisualAnalysisAdapter(ABC):
    """Interface commune à tous les adaptateurs d'analyse visuelle."""

    @abstractmethod
    def analyze(self, source: VisualSource) -> StyleDNA:
        """Analyse une source visuelle et retourne un StyleDNA."""
        ...

    def supports(self, source_type: str) -> bool:
        """True si cet adaptateur supporte ce type de source."""
        return True


# ─── Adaptateurs MVP ─────────────────────────────────────────────────────────

class MockVisualAnalysis(VisualAnalysisAdapter):
    """
    Retourne un StyleDNA hardcodé.
    Usage : tests unitaires, CI, développement rapide.
    """

    def __init__(self, mock_dna: Optional[StyleDNA] = None):
        from .style_dna import (
            PaletteProfile, TypographyProfile, GeometryProfile,
            OrnamentProfile, LayoutProfile,
        )
        self._mock = mock_dna or StyleDNA(
            palette_profile=PaletteProfile(
                dominant=["#667eea", "#764ba2"],
                accent=["#48bb78"],
                neutral=["#ffffff", "#2d3748"],
                temperature="cold",
                saturation="medium",
                contrast="medium",
            ),
            typography_profile=TypographyProfile(
                display="neutral_sans",
                body="neutral_humanist_sans",
            ),
            geometry_profile=GeometryProfile(
                border_radius="medium",
                shape_family="geometric",
                stroke_weight="regular",
                symmetry="balanced",
            ),
            ornament_profile=OrnamentProfile(has_ornaments=False),
            layout_profile=LayoutProfile(rhythm="balanced", density="moderate"),
            emotional_tone="calm",
            complexity_level="moderate",
            aesthetic_tags=["modern", "clean"],
            source_type="manual",
        )

    def analyze(self, source: VisualSource) -> StyleDNA:
        self._mock.source_type = source.type
        self._mock.source_ref  = str(source.path or source.url or "mock")
        return self._mock


class JsonVisualAnalysis(VisualAnalysisAdapter):
    """
    Charge un StyleDNA depuis un fichier JSON ou un dict injecté.
    Usage : test de la chaîne complète sans vision LLM.

    Le JSON peut être :
    - fourni via source.raw_json (dict)
    - lu depuis source.path (fichier .json)
    """

    def supports(self, source_type: str) -> bool:
        return source_type in ("manual", "json", "image", "screenshot", "mockup", "logo")

    def analyze(self, source: VisualSource) -> StyleDNA:
        if source.raw_json is not None:
            data = source.raw_json
        elif source.path and Path(source.path).exists():
            data = json.loads(Path(source.path).read_text(encoding="utf-8"))
        else:
            raise ValueError(
                f"JsonVisualAnalysis : source.raw_json ou source.path requis "
                f"(reçu path={source.path}, raw_json={source.raw_json is not None})"
            )
        dna = style_dna_from_dict(data)
        dna.source_type = source.type
        dna.source_ref  = str(source.path or "inline")
        return dna


class PresetVisualAnalysis(VisualAnalysisAdapter):
    """
    Convertit un ThemePreset existant en StyleDNA.
    Permet de traiter un preset comme une source visuelle.
    Usage : migration de thèmes existants vers le nouveau pipeline.
    """

    def supports(self, source_type: str) -> bool:
        return source_type == "preset"

    def analyze(self, source: VisualSource) -> StyleDNA:
        from .style_dna import (
            PaletteProfile, TypographyProfile, GeometryProfile,
            OrnamentProfile, LayoutProfile,
        )

        preset = source.raw_json or {}
        cs      = preset.get("color_system", {})
        primary = cs.get("primary", {})
        sec     = cs.get("secondary", {})

        # Extraire les hex depuis les rgb() strings du preset
        def _rgb_to_hex(rgb_str: str) -> str:
            import re
            m = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", rgb_str or "")
            if m:
                return "#{:02x}{:02x}{:02x}".format(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return "#667eea"

        dominant = []
        if primary.get("base"):  dominant.append(_rgb_to_hex(primary["base"]))
        if sec.get("base"):      dominant.append(_rgb_to_hex(sec["base"]))

        style_name = preset.get("style_preset_name", "flat")
        tone_map   = {v: k for k, v in {
            "premium": "minimal", "calm": "flat", "bold": "bold",
            "playful": "rounded", "raw": "dark", "tech": "dark",
        }.items()}
        emotional_tone = tone_map.get(style_name, "calm")

        anim_map = {"subtle": "minimal", "moderate": "moderate", "rich": "rich", "none": "minimal"}
        complexity = anim_map.get(preset.get("animation_style", "subtle"), "moderate")

        return StyleDNA(
            palette_profile=PaletteProfile(
                dominant=dominant,
                temperature="cold" if preset.get("mood") == "dark" else "neutral",
            ),
            typography_profile=TypographyProfile(
                display="neutral_sans",
                body="neutral_humanist_sans",
            ),
            geometry_profile=GeometryProfile(),
            ornament_profile=OrnamentProfile(has_ornaments=False),
            layout_profile=LayoutProfile(),
            emotional_tone=emotional_tone,
            complexity_level=complexity,
            source_type="preset",
            source_ref=str(source.path or "inline_preset"),
        )


# ─── Registry & point d'entrée ────────────────────────────────────────────────

_ADAPTERS: dict[str, type[VisualAnalysisAdapter]] = {
    "mock":   MockVisualAnalysis,
    "json":   JsonVisualAnalysis,
    "preset": PresetVisualAnalysis,
}


def get_adapter(backend: str = "json") -> VisualAnalysisAdapter:
    """Retourne une instance de l'adaptateur demandé."""
    cls = _ADAPTERS.get(backend)
    if cls is None:
        raise ValueError(
            f"Adaptateur '{backend}' inconnu. Disponibles : {list(_ADAPTERS)}"
        )
    return cls()


def visual_analysis(source: VisualSource, backend: str = "json") -> StyleDNA:
    """
    Point d'entrée public.

    visual_analysis(source) → StyleDNA

    Exemple :
        dna = visual_analysis(
            VisualSource(type="manual", raw_json={...}),
            backend="json"
        )
    """
    adapter = get_adapter(backend)
    return adapter.analyze(source)


def register_adapter(name: str, cls: type[VisualAnalysisAdapter]) -> None:
    """
    Enregistre un adaptateur externe (ex: ClaudeVisionAnalysis).
    Appelé par le module vision LLM quand il sera disponible.

    Exemple :
        from my_vision_module import ClaudeVisionAnalysis
        register_adapter("claude", ClaudeVisionAnalysis)
    """
    _ADAPTERS[name] = cls
