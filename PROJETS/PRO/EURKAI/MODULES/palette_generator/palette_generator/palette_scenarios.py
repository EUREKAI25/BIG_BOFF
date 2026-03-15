"""
palette_generator.palette_scenarios
─────────────────────────────────────
Définit les règles de composition par scénario.
Chaque scénario détermine :
  - quelles harmonies générer
  - si la validation WCAG est requise
  - si ui_safe doit être généré
  - l'équilibre saturation/contraste attendu
  - le nombre de couleurs primaires recommandé
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .schemas import PaletteScenario, HarmonyType, WCAGLevel


@dataclass
class ScenarioConfig:
    scenario:          PaletteScenario
    harmonies:         List[HarmonyType]    # harmonies à générer
    generate_bw:       bool = True
    generate_metal:    bool = False
    generate_minimal:  bool = True
    validate_wcag:     bool = False
    generate_ui_safe:  bool = False
    wcag_level:        WCAGLevel = WCAGLevel.AA
    n_primary_colors:  int = 3
    saturation_hint:   str = "medium"       # low / medium / high / vivid
    contrast_hint:     str = "medium"       # low / medium / high / extreme
    notes:             str = ""


_SCENARIO_CONFIGS: dict[PaletteScenario, ScenarioConfig] = {
    PaletteScenario.BRAND: ScenarioConfig(
        scenario=PaletteScenario.BRAND,
        harmonies=[
            HarmonyType.COMPLEMENTARY,
            HarmonyType.ANALOGOUS,
            HarmonyType.MONOCHROMATIC,
            HarmonyType.TRIADIC,
        ],
        generate_bw=True,
        generate_metal=True,
        generate_minimal=True,
        validate_wcag=False,
        n_primary_colors=3,
        saturation_hint="medium",
        contrast_hint="medium",
        notes="Palette complète pour identité de marque",
    ),

    PaletteScenario.UI: ScenarioConfig(
        scenario=PaletteScenario.UI,
        harmonies=[
            HarmonyType.COMPLEMENTARY,
            HarmonyType.MONOCHROMATIC,
            HarmonyType.ANALOGOUS,
        ],
        generate_bw=True,
        generate_metal=False,
        generate_minimal=True,
        validate_wcag=True,
        generate_ui_safe=True,
        wcag_level=WCAGLevel.AA,
        n_primary_colors=2,
        saturation_hint="medium",
        contrast_hint="high",
        notes="Palette pour interface — validation WCAG AA obligatoire",
    ),

    PaletteScenario.ILLUSTRATION: ScenarioConfig(
        scenario=PaletteScenario.ILLUSTRATION,
        harmonies=[
            HarmonyType.ANALOGOUS,
            HarmonyType.TRIADIC,
            HarmonyType.TETRADIC,
            HarmonyType.SPLIT_COMPLEMENTARY,
        ],
        generate_bw=True,
        generate_metal=False,
        generate_minimal=False,
        validate_wcag=False,
        n_primary_colors=5,
        saturation_hint="high",
        contrast_hint="medium",
        notes="Palette riche pour illustration — maximise la diversité chromatique",
    ),

    PaletteScenario.PHOTO: ScenarioConfig(
        scenario=PaletteScenario.PHOTO,
        harmonies=[
            HarmonyType.ANALOGOUS,
            HarmonyType.COMPLEMENTARY,
        ],
        generate_bw=True,
        generate_metal=False,
        generate_minimal=True,
        validate_wcag=False,
        n_primary_colors=3,
        saturation_hint="medium",
        contrast_hint="medium",
        notes="Palette pour ambiance photo — tons naturels et cohérents",
    ),

    PaletteScenario.MINIMAL: ScenarioConfig(
        scenario=PaletteScenario.MINIMAL,
        harmonies=[
            HarmonyType.MONOCHROMATIC,
        ],
        generate_bw=True,
        generate_metal=False,
        generate_minimal=True,
        validate_wcag=True,
        generate_ui_safe=True,
        n_primary_colors=2,
        saturation_hint="low",
        contrast_hint="high",
        notes="Palette minimaliste — 1-2 couleurs max + neutres",
    ),

    PaletteScenario.DARK_MODE: ScenarioConfig(
        scenario=PaletteScenario.DARK_MODE,
        harmonies=[
            HarmonyType.MONOCHROMATIC,
            HarmonyType.COMPLEMENTARY,
        ],
        generate_bw=True,
        generate_metal=True,
        generate_minimal=True,
        validate_wcag=True,
        generate_ui_safe=True,
        wcag_level=WCAGLevel.AA,
        n_primary_colors=2,
        saturation_hint="medium",
        contrast_hint="extreme",
        notes="Dark mode — accents vifs sur fonds sombres, WCAG sur fond dark",
    ),

    PaletteScenario.DATA_VISUALIZATION: ScenarioConfig(
        scenario=PaletteScenario.DATA_VISUALIZATION,
        harmonies=[
            HarmonyType.TRIADIC,
            HarmonyType.TETRADIC,
            HarmonyType.SPLIT_COMPLEMENTARY,
        ],
        generate_bw=False,
        generate_metal=False,
        generate_minimal=False,
        validate_wcag=True,
        generate_ui_safe=True,
        n_primary_colors=6,
        saturation_hint="vivid",
        contrast_hint="high",
        notes="Dataviz — couleurs distinctes et discriminables, WCAG validé",
    ),
}


def get_config(scenario: PaletteScenario) -> ScenarioConfig:
    return _SCENARIO_CONFIGS.get(scenario, _SCENARIO_CONFIGS[PaletteScenario.BRAND])
