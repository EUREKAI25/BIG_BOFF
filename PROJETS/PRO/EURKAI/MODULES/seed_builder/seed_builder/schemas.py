"""
Schémas Pydantic pour les seeds de pages EURKAI.

Une seed définit la STRUCTURE d'une page (quelles sections, quels blocs,
quels champs éditables) indépendamment du contenu et du thème.

C'est la source de vérité unique :
  → le renderer lit seed.sections[].block_type + structure
  → l'admin génère ses champs depuis seed.sections[].fields
"""
from __future__ import annotations
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field


# ── Types disponibles ──────────────────────────────────────────────────────────

BlockType = Literal[
    "hero_block",
    "navbar_block",
    "stat_block",
    "steps_block",
    "faq_block",
    "pricing_block",
    "cta_block",
    "testimonial_block",
    "content_block",
    "footer_block",
]

FieldType = Literal["text", "textarea", "image", "url", "number", "select", "boolean"]

PageType = Literal["landing", "home", "product", "blog", "about", "contact", "generic"]


# ── Champ éditable ────────────────────────────────────────────────────────────

class SeedField(BaseModel):
    """Un champ éditable dans l'admin, lu par le renderer."""
    key: str = Field(description="Clé snake_case lue par le renderer (ex: cta_label)")
    label: str = Field(description="Label affiché dans l'admin (ex: Texte du bouton)")
    type: FieldType = "text"
    required: bool = False
    default: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[list[str]] = None  # pour type=select


# ── Section de la seed ────────────────────────────────────────────────────────

class SeedSection(BaseModel):
    """Une section de la page avec son bloc, sa structure et ses champs."""
    key: str = Field(description="Identifiant unique de la section (ex: hero, benefits)")
    order: int = Field(description="Position dans la page (1 = en haut)")
    block_type: BlockType
    full_width: bool = Field(
        default=False,
        description="True = bord à bord (pas de container centré). "
                    "Toujours True pour hero, footer, navbar."
    )
    structure: dict[str, Any] = Field(
        default_factory=dict,
        description="Options visuelles du bloc (layout, direction, colonnes, variantes)"
    )
    content_role: str = Field(
        default="",
        description="Rôle éditorial de cette section — ce qu'elle doit exprimer "
                    "(ex: 'Accroche problème/solution', 'Arguments de réassurance', "
                    "'Preuve sociale'). Sert de prompt de base pour la génération de contenu."
    )
    fields: list[SeedField] = Field(
        default_factory=list,
        description="Champs éditables de cette section"
    )
    enabled: bool = True
    notes: Optional[str] = None  # observations visuelles de l'analyseur


# ── Responsive config ─────────────────────────────────────────────────────────

class ResponsiveConfig(BaseModel):
    """Largeurs de container par breakpoint. Tout le reste est relatif à ça."""
    mobile: str = "100%"
    tablet: str = "768px"
    desktop: str = "1200px"
    wide: str = "1440px"


# ── Seed complète ─────────────────────────────────────────────────────────────

class PageSeed(BaseModel):
    """
    Seed complète d'un template de page.

    Générée par l'analyseur de maquettes, utilisée par :
      - le renderer pour savoir quels blocs afficher et comment
      - l'admin pour générer les champs éditables
      - l'agent de contenu pour savoir quoi remplir
    """
    template_id: str = Field(description="Identifiant unique du template (ex: landing_service_a)")
    page_type: PageType = "landing"
    description: str = Field(description="Description courte du template")
    source_image: Optional[str] = None  # nom du fichier maquette source
    responsive: ResponsiveConfig = Field(default_factory=ResponsiveConfig)
    sections: list[SeedSection] = Field(default_factory=list)

    def get_section(self, key: str) -> Optional[SeedSection]:
        return next((s for s in self.sections if s.key == key), None)

    def field_keys(self, section_key: str) -> list[str]:
        """Retourne les clés de champs d'une section (pour le renderer)."""
        section = self.get_section(section_key)
        return [f.key for f in section.fields] if section else []
