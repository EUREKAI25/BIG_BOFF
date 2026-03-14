"""
ContractRegistry — registre externe des contrats de modules.

Les modules sont des boîtes noires. Ce fichier est la SEULE source de vérité
sur ce qu'ils acceptent et produisent, en termes de types de données.

Règle de chaînage :
    outputs(A) ∩ inputs(B) ≠ ∅  →  B peut suivre A

Note : temporaire MVP. Sera remplacé par les SuperTools.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os


@dataclass
class ModuleContract:
    module_id: str
    input_datas:  List[str]   # types de données acceptés en entrée
    output_datas: List[str]   # types de données produits en sortie
    description:  str = ""


# ---------------------------------------------------------------------------
# Registre statique des contrats
# Étendre librement — ne modifie jamais les modules eux-mêmes.
# ---------------------------------------------------------------------------

_STATIC_CONTRACTS: Dict[str, ModuleContract] = {

    # ── Analyse ─────────────────────────────────────────────────────────────
    "extract_brand_dna": ModuleContract(
        module_id    = "extract_brand_dna",
        input_datas  = ["ImageInput", "UrlInput", "LogoInput"],
        output_datas = ["BrandDNA"],
        description  = "Extrait le DNA de marque depuis une image, un logo ou une URL",
    ),
    "extract_theme_dna": ModuleContract(
        module_id    = "extract_theme_dna",
        input_datas  = ["ImageInput", "UrlInput", "BrandDNA"],
        output_datas = ["ThemeDNA"],
    ),
    "extract_visual_signature": ModuleContract(
        module_id    = "extract_visual_signature",
        input_datas  = ["ImageInput"],
        output_datas = ["VisualSignature"],
    ),
    "analyze_palette": ModuleContract(
        module_id    = "analyze_palette",
        input_datas  = ["ImageInput", "UrlInput"],
        output_datas = ["PaletteProfile"],
    ),
    "analyze_typography": ModuleContract(
        module_id    = "analyze_typography",
        input_datas  = ["ImageInput", "UrlInput"],
        output_datas = ["TypographyProfile"],
    ),
    "score_theme_coherence": ModuleContract(
        module_id    = "score_theme_coherence",
        input_datas  = ["ThemeTokens"],
        output_datas = ["CoherenceReport"],
    ),
    "compare_styles": ModuleContract(
        module_id    = "compare_styles",
        input_datas  = ["ThemeDNA", "BrandDNA"],
        output_datas = ["StyleDiff", "DriftReport"],
    ),
    "validate_accessibility": ModuleContract(
        module_id    = "validate_accessibility",
        input_datas  = ["ThemeTokens"],
        output_datas = ["AccessibilityReport"],
    ),
    "validate_identity_drift": ModuleContract(
        module_id    = "validate_identity_drift",
        input_datas  = ["BrandDNA"],
        output_datas = ["DriftReport"],
    ),

    # ── Génération ──────────────────────────────────────────────────────────
    "generate_theme": ModuleContract(
        module_id    = "generate_theme",
        input_datas  = ["BrandDNA", "ThemeDNA", "ImageInput", "LogoInput"],
        output_datas = ["ThemeTokens"],
    ),
    "generate_theme_from_brand_dna": ModuleContract(
        module_id    = "generate_theme_from_brand_dna",
        input_datas  = ["BrandDNA"],
        output_datas = ["ThemeTokens"],
    ),
    "generate_ui_kit": ModuleContract(
        module_id    = "generate_ui_kit",
        input_datas  = ["ThemeTokens"],
        output_datas = ["UiKitBundle"],
    ),
    "generate_brand_guidelines": ModuleContract(
        module_id    = "generate_brand_guidelines",
        input_datas  = ["ThemeTokens", "BrandDNA"],
        output_datas = ["BrandGuidelines"],
    ),
    "generate_design_tokens": ModuleContract(
        module_id    = "generate_design_tokens",
        input_datas  = ["ThemeTokens"],
        output_datas = ["JsonTokens"],
    ),

    # ── Mutation ────────────────────────────────────────────────────────────
    "mutate_theme": ModuleContract(
        module_id    = "mutate_theme",
        input_datas  = ["ThemeTokens"],
        output_datas = ["ThemeTokens"],
    ),
    "evolve_brand_identity": ModuleContract(
        module_id    = "evolve_brand_identity",
        input_datas  = ["BrandDNA"],
        output_datas = ["BrandDNA"],
    ),
    "create_theme_variants": ModuleContract(
        module_id    = "create_theme_variants",
        input_datas  = ["ThemeTokens"],
        output_datas = ["ThemeVariantSet"],
    ),
    "adapt_theme_to_target": ModuleContract(
        module_id    = "adapt_theme_to_target",
        input_datas  = ["ThemeTokens"],
        output_datas = ["ThemeTokens"],
    ),

    # ── Reverse ─────────────────────────────────────────────────────────────
    "reverse_brand_from_site": ModuleContract(
        module_id    = "reverse_brand_from_site",
        input_datas  = ["UrlInput"],
        output_datas = ["BrandDNA", "ThemeDNA"],
    ),
    "reverse_brand_from_mockup": ModuleContract(
        module_id    = "reverse_brand_from_mockup",
        input_datas  = ["ImageInput"],
        output_datas = ["BrandDNA", "ThemeDNA"],
    ),

    # ── Rendu ───────────────────────────────────────────────────────────────
    "render_css_bundle": ModuleContract(
        module_id    = "render_css_bundle",
        input_datas  = ["ThemeTokens"],
        output_datas = ["CssBundle"],
    ),
    "render_scss_tokens": ModuleContract(
        module_id    = "render_scss_tokens",
        input_datas  = ["ThemeTokens"],
        output_datas = ["ScssBundle"],
    ),
    "render_json_tokens": ModuleContract(
        module_id    = "render_json_tokens",
        input_datas  = ["ThemeTokens", "JsonTokens"],
        output_datas = ["JsonTokens"],
    ),
    "render_preview_pack": ModuleContract(
        module_id    = "render_preview_pack",
        input_datas  = ["ThemeTokens"],
        output_datas = ["PreviewPack"],
    ),
    "render_brand_guidelines": ModuleContract(
        module_id    = "render_brand_guidelines",
        input_datas  = ["BrandGuidelines"],
        output_datas = ["PreviewPack"],
    ),

    # ── Modules existants (EURKAI MODULES) ──────────────────────────────────
    "model_executor": ModuleContract(
        module_id    = "model_executor",
        input_datas  = ["BriefInput", "ImageInput"],
        output_datas = ["ModelOutput"],
        description  = "Interface universelle modèles IA",
    ),
}


class ContractRegistry:
    """
    Registre des contrats de modules.

    Priorité de résolution :
    1. MANIFEST.json du module (si champs input_datas / output_datas présents)
    2. Registre statique _STATIC_CONTRACTS
    3. KeyError si module inconnu

    Ajouter un module : étendre _STATIC_CONTRACTS ci-dessus.
    Ou ajouter input_datas / output_datas dans son MANIFEST.json.
    """

    def __init__(self, manifests_base_path: Optional[str] = None):
        self._cache: Dict[str, ModuleContract] = dict(_STATIC_CONTRACTS)
        if manifests_base_path:
            self._load_from_manifests(manifests_base_path)

    def _load_from_manifests(self, base_path: str) -> None:
        """Charge les contrats depuis les MANIFEST.json qui ont input_datas/output_datas."""
        for root, _, files in os.walk(base_path):
            if "MANIFEST.json" in files:
                path = os.path.join(root, "MANIFEST.json")
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if "input_datas" in data and "output_datas" in data:
                        mid = data.get("name") or data.get("ident", "")
                        self._cache[mid] = ModuleContract(
                            module_id    = mid,
                            input_datas  = data["input_datas"],
                            output_datas = data["output_datas"],
                            description  = data.get("description", ""),
                        )
                except Exception:
                    pass

    def get(self, module_id: str) -> ModuleContract:
        if module_id not in self._cache:
            raise KeyError(f"Module inconnu : '{module_id}'. Ajouter son contrat dans contracts.py")
        return self._cache[module_id]

    def list_ids(self) -> List[str]:
        return sorted(self._cache.keys())

    def compatible_next(self, module_id: str) -> List[str]:
        """Retourne tous les modules qui peuvent suivre module_id."""
        contract = self.get(module_id)
        outputs  = set(contract.output_datas)
        return [
            mid for mid, c in self._cache.items()
            if outputs & set(c.input_datas)
        ]

    def compatible_prev(self, module_id: str) -> List[str]:
        """Retourne tous les modules qui peuvent précéder module_id."""
        contract = self.get(module_id)
        inputs   = set(contract.input_datas)
        return [
            mid for mid, c in self._cache.items()
            if inputs & set(c.output_datas)
        ]

    def bridges(self, from_id: str, to_id: str) -> List[str]:
        """
        Retourne les modules M qui peuvent s'insérer entre from_id et to_id
        quand la transition directe est invalide.
        """
        contract_from = self.get(from_id)
        contract_to   = self.get(to_id)
        from_outputs  = set(contract_from.output_datas)
        to_inputs     = set(contract_to.input_datas)

        return [
            mid for mid, c in self._cache.items()
            if mid not in (from_id, to_id)
            and from_outputs & set(c.input_datas)     # M accepte la sortie de A
            and set(c.output_datas) & to_inputs       # B accepte la sortie de M
        ]
