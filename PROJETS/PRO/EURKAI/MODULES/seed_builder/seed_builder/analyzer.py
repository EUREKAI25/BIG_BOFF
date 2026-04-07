"""
Analyseur de maquettes — Claude Vision → PageSeed.

Envoie une image (wireframe, mockup, screenshot annoté) à l'API Anthropic
et retourne une PageSeed structurée.
"""
from __future__ import annotations
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from .schemas import PageSeed

# Accès unifié aux modèles IA via MODEL_EXECUTOR
_MODULES_DIR = Path(__file__).parent.parent.parent.parent
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))
from MODEL_EXECUTOR import model_execute


# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Tu es un expert en architecture de pages web.
Tu analyses des maquettes, wireframes ou schémas annotés de pages web
et tu produis une définition structurée (seed) en JSON.

Blocs disponibles :
- hero_block       : grande section d'accroche (titre, sous-titre, CTA, image)
- navbar_block     : barre de navigation
- stat_block       : chiffres/statistiques clés en ligne
- steps_block      : étapes numérotées ou bénéfices en colonnes
- faq_block        : questions/réponses accordion
- pricing_block    : cartes tarifaires
- cta_block        : appel à l'action simple (texte + bouton)
- testimonial_block: témoignages / avis clients
- content_block    : section texte+image générique
- footer_block     : pied de page avec liens

Règles :
- full_width: true uniquement pour hero, navbar, footer et les sections bord-à-bord
- Les keys de sections sont en snake_case, uniques (ex: hero, benefits, how_it_works)
- Les keys de champs correspondent EXACTEMENT à ce que le renderer lira en DB
- Chaque field a : key (snake_case), label (français clair), type, required
- Types disponibles : text, textarea, image, url, number, select, boolean
- Pour steps_block avec N éléments : champs step_1_title, step_1_desc, step_2_title, etc.
- Pour testimonial_block : item_1_name, item_1_role, item_1_content, etc.
- Pour pricing_block : les cartes viennent d'un module offres, pas de champs directs
- Pour stat_block : stat_1_value, stat_1_label, stat_2_value, etc.
- Pour faq_block : q1, a1, q2, a2, etc.
"""

_USER_PROMPT = """Analyse cette maquette de page web de haut en bas.

Pour chaque section identifiée, extrais :

1. **block_type** : le type parmi les blocs disponibles
2. **full_width** : true si bord à bord, false si centré
3. **structure** : toutes les options visuelles observées :
   - colonnes (ex: 2, 3)
   - direction (horizontal / vertical)
   - alignement texte (left / center / right)
   - variante (cards / timeline / simple / split / grid)
   - présence d'image, d'icône, de numéro
   - min_height si section haute (ex: "90vh" pour un hero plein écran)
4. **content_role** : ce que cette section doit EXPRIMER éditorialement
   (ex: "Accroche problème/solution pour capter l'attention",
        "Réassurance par 3 arguments clés (bénéfices produit)",
        "Preuve sociale — témoignages clients",
        "Conversion finale — pricing et CTA")
5. **fields** : liste exacte des champs éditables avec :
   - key en snake_case (ex: step_1_title, q1, stat_2_value)
   - label en français clair
   - type : text / textarea / image / url / number
   - required : true pour les champs essentiels
6. **notes** : observations particulières sur la mise en page

Réponds UNIQUEMENT avec ce JSON valide :
{
  "template_id": "",
  "page_type": "landing|home|product|blog|about|contact|generic",
  "description": "1 phrase décrivant le template et son objectif",
  "sections": [
    {
      "key": "snake_case_unique",
      "order": 1,
      "block_type": "hero_block|...",
      "full_width": true,
      "structure": {},
      "content_role": "Ce que cette section exprime",
      "fields": [
        { "key": "field_key", "label": "Label FR", "type": "text", "required": false }
      ],
      "notes": ""
    }
  ]
}"""


# ── Analyseur ─────────────────────────────────────────────────────────────────

class MockupAnalyzer:
    """Analyse une image de maquette et retourne une PageSeed."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-opus-4-6"):
        self.model = model
        # api_key conservé pour compatibilité — géré par MODEL_EXECUTOR
        if api_key:
            os.environ.setdefault("ANTHROPIC_API_KEY", api_key)

    def analyze(self, image_path: str | Path, template_id: Optional[str] = None) -> PageSeed:
        """
        Analyse une image et retourne la PageSeed.

        Args:
            image_path: Chemin vers l'image (PNG, JPG, WEBP, GIF)
            template_id: Override de l'ID template (sinon déduit du nom de fichier)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image non trouvée : {path}")

        # Encoder l'image en base64
        media_type = _get_media_type(path)
        with open(path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Appel vision via MODEL_EXECUTOR
        resp = model_execute(
            "img2text",
            _USER_PROMPT,
            data={
                "image_base64":   image_data,
                "media_type":     media_type,
                "max_tokens":     4096,
                "system":         _SYSTEM_PROMPT,
                "model_override": self.model,
            },
            provider="anthropic",
        )

        # Parser la réponse JSON
        raw = resp["result"]
        seed_dict = _extract_json(raw)

        # Override template_id si fourni
        if template_id:
            seed_dict["template_id"] = template_id
        elif "template_id" not in seed_dict or not seed_dict["template_id"]:
            seed_dict["template_id"] = path.stem.lower().replace(" ", "_").replace("-", "_")

        seed_dict["source_image"] = path.name

        return PageSeed(**seed_dict)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_media_type(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def _extract_json(text: str) -> dict:
    """Extrait le JSON de la réponse Claude (gère les balises ```json```)."""
    # Chercher un bloc ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())

    # Chercher le premier { ... } valide
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"Aucun JSON valide trouvé dans la réponse :\n{text[:500]}")
