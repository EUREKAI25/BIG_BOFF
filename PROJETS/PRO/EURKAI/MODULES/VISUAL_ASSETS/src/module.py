"""
Visual Assets Generator - Génère icônes, illustrations, patterns cohérents avec le preset.

Utilise :
- Mood + use_case → Style d'icônes
- Caractéristiques → Prompts illustrations IA
- Palette → Patterns SVG procéduraux
"""
import json
from pathlib import Path
from typing import Dict, List


class VisualAssetsGenerator:
    """Générateur d'assets visuels cohérents avec un ThemePreset."""

    # Mapping mood → style visuel
    MOOD_STYLES = {
        "warm": {
            "icon_style": "organic",
            "icon_corners": "rounded",
            "icon_weight": "regular",
            "shape_style": "flowing",
            "pattern_type": "organic"
        },
        "minimal": {
            "icon_style": "geometric",
            "icon_corners": "sharp",
            "icon_weight": "thin",
            "shape_style": "clean",
            "pattern_type": "grid"
        },
        "vibrant": {
            "icon_style": "bold",
            "icon_corners": "rounded",
            "icon_weight": "bold",
            "shape_style": "dynamic",
            "pattern_type": "abstract"
        },
        "corporate": {
            "icon_style": "professional",
            "icon_corners": "slightly-rounded",
            "icon_weight": "medium",
            "shape_style": "structured",
            "pattern_type": "geometric"
        }
    }

    # Mapping use_case → thématiques icônes
    USE_CASE_ICONS = {
        "wellness": ["leaf", "sun", "heart", "water-drop", "flower"],
        "saas": ["code", "rocket", "chart", "cloud", "zap"],
        "ecommerce": ["shopping-cart", "package", "credit-card", "tag", "truck"],
        "blog": ["book", "pencil", "message", "bookmark", "rss"],
        "portfolio": ["briefcase", "star", "trophy", "paint-brush", "camera"]
    }

    def generate_assets(self, preset: Dict) -> Dict:
        """
        Génère tous les assets visuels pour un preset.

        Returns:
            {
                "icon_guidelines": {...},
                "illustration_prompts": {...},
                "svg_patterns": {...},
                "decorative_elements": {...}
            }
        """
        mood = preset.get('mood', 'minimal')
        use_case = preset.get('use_case', 'landing')
        characteristics = preset.get('key_characteristics', [])
        colors = preset.get('color_system', {})

        return {
            "icon_guidelines": self.generate_icon_guidelines(mood, use_case),
            "illustration_prompts": self.generate_illustration_prompts(preset),
            "svg_patterns": self.generate_svg_patterns(mood, colors),
            "decorative_elements": self.generate_decorative_elements(mood, colors)
        }

    def generate_icon_guidelines(self, mood: str, use_case: str) -> Dict:
        """
        Génère les guidelines pour les icônes.

        Returns:
            {
                "style": "organic",
                "library": "phosphor-duotone",
                "recommended_icons": ["leaf", "sun", ...],
                "customization": {...}
            }
        """
        style = self.MOOD_STYLES.get(mood, self.MOOD_STYLES['minimal'])
        recommended_icons = self.USE_CASE_ICONS.get(use_case, ["circle", "square", "star"])

        # Bibliothèques d'icônes recommandées
        if style['icon_style'] == "organic":
            library = "phosphor-duotone"  # Icônes douces, arrondies
        elif style['icon_style'] == "geometric":
            library = "heroicons-outline"  # Icônes minimales, sharp
        elif style['icon_style'] == "bold":
            library = "feather-bold"  # Icônes vibrantes
        else:
            library = "lucide"  # Professionnel

        return {
            "style": style['icon_style'],
            "corners": style['icon_corners'],
            "weight": style['icon_weight'],
            "library": library,
            "recommended_icons": recommended_icons,
            "customization": {
                "stroke_width": 2 if style['icon_weight'] == "regular" else 1,
                "size_range": "20px-32px",
                "color_usage": "Use primary color for accents, neutral for base"
            },
            "cdn_links": {
                "phosphor": "https://unpkg.com/@phosphor-icons/web",
                "heroicons": "https://heroicons.com",
                "feather": "https://feathericons.com",
                "lucide": "https://lucide.dev"
            }
        }

    def generate_illustration_prompts(self, preset: Dict) -> Dict:
        """
        Génère des prompts pour illustrations IA (Midjourney, DALL-E, etc.).

        Returns:
            {
                "hero": "prompt for hero section",
                "features": "prompt for features",
                "cta": "prompt for CTA section"
            }
        """
        base_prompt = preset.get('image_generation_prompt', '')
        mood = preset.get('mood', 'minimal')
        use_case = preset.get('use_case', 'landing')

        # Extraire couleurs dominantes
        primary = preset.get('color_system', {}).get('primary', {}).get('base', 'rgb(128,128,128)')

        # Style descriptor basé sur mood
        style_map = {
            "warm": "soft lighting, warm tones, organic shapes, natural textures",
            "minimal": "clean, simple, lots of whitespace, geometric",
            "vibrant": "colorful, energetic, dynamic, bold",
            "corporate": "professional, polished, structured, modern"
        }
        style_desc = style_map.get(mood, "clean, modern")

        return {
            "hero": f"""
{base_prompt}
Hero image for {use_case} website
Style: {style_desc}
Composition: Wide aspect ratio (16:9), centered subject
Mood: {mood}, welcoming, high quality
Colors: Incorporate {primary}
Format: Horizontal banner, 1920x1080px
            """.strip(),

            "features": f"""
Abstract illustration representing {use_case} features
Style: {style_desc}, isometric or flat design
Mood: {mood}
Colors: Use palette from {primary}
Elements: Icons, simple shapes, minimal detail
Format: Square or portrait, 800x800px
            """.strip(),

            "cta": f"""
{base_prompt}
Background for call-to-action section
Style: {style_desc}, subtle, not distracting
Mood: {mood}, inviting
Treatment: Soft gradient or subtle pattern
Colors: {primary} as accent
Format: Wide, suitable as background
            """.strip(),

            "og_image": f"""
Social media preview card for {use_case}
Style: {style_desc}, clean, readable
Mood: {mood}
Layout: Title + visual element, 1200x630px
Colors: Palette based on {primary}
            """.strip()
        }

    def generate_svg_patterns(self, mood: str, colors: Dict) -> Dict:
        """
        Génère des patterns SVG procéduraux.

        Returns:
            {
                "dots": "<svg>...</svg>",
                "waves": "<svg>...</svg>",
                "grid": "<svg>...</svg>"
            }
        """
        # Extraire couleur primaire
        primary_rgb = colors.get('primary', {}).get('base', 'rgb(128,128,128)')

        # Convertir en rgba avec alpha faible pour subtilité
        primary_rgba = primary_rgb.replace('rgb(', 'rgba(').replace(')', ', 0.1)')

        patterns = {}

        # Pattern dots (pour warm/organic)
        if mood in ["warm", "vibrant"]:
            patterns["dots"] = f"""
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
  <circle cx="10" cy="10" r="2" fill="{primary_rgba}" />
</svg>
            """.strip()

        # Pattern waves (pour warm)
        if mood == "warm":
            patterns["waves"] = f"""
<svg width="100" height="20" xmlns="http://www.w3.org/2000/svg">
  <path d="M0 10 Q 25 0, 50 10 T 100 10" stroke="{primary_rgba}" fill="none" stroke-width="2"/>
</svg>
            """.strip()

        # Pattern grid (pour minimal/corporate)
        if mood in ["minimal", "corporate"]:
            patterns["grid"] = f"""
<svg width="40" height="40" xmlns="http://www.w3.org/2000/svg">
  <rect width="40" height="40" fill="none"/>
  <path d="M0 0 L0 40 M40 0 L40 40 M0 0 L40 0 M0 40 L40 40" stroke="{primary_rgba}" stroke-width="1"/>
</svg>
            """.strip()

        # Pattern géométrique
        patterns["geometric"] = f"""
<svg width="60" height="60" xmlns="http://www.w3.org/2000/svg">
  <polygon points="30,10 50,30 30,50 10,30" fill="{primary_rgba}"/>
</svg>
        """.strip()

        return patterns

    def generate_decorative_elements(self, mood: str, colors: Dict) -> Dict:
        """
        Génère des guidelines pour éléments décoratifs.

        Returns:
            {
                "border_radius": "8px",
                "shadow_style": "soft",
                "gradient_direction": "radial",
                ...
            }
        """
        style = self.MOOD_STYLES.get(mood, self.MOOD_STYLES['minimal'])

        return {
            "border_radius": "12px" if style['icon_corners'] == "rounded" else "4px",
            "shadow_style": "soft" if mood == "warm" else "sharp",
            "gradient_type": "radial" if mood == "warm" else "linear",
            "shape_style": style['shape_style'],
            "animation_style": "smooth" if mood == "warm" else "snappy",
            "divider_style": "curved" if mood == "warm" else "straight",
            "button_style": {
                "corners": style['icon_corners'],
                "hover_effect": "lift" if mood == "warm" else "glow",
                "transition": "0.3s ease" if mood == "warm" else "0.15s linear"
            }
        }


# === DEMO ===

if __name__ == "__main__":
    print("="*70)
    print("  VISUAL ASSETS GENERATOR - Icônes, Illustrations, Patterns")
    print("="*70)

    # Charger preset myhealthprac
    preset_path = Path("output_myhealthprac/theme_preset_v2.json")
    with open(preset_path) as f:
        preset = json.load(f)

    print(f"\n📊 Preset : {preset['name']}")
    print(f"   Mood : {preset['mood']}")
    print(f"   Use case : {preset['use_case']}")

    # Générer assets
    print(f"\n🎨 Génération des assets visuels...")
    generator = VisualAssetsGenerator()
    assets = generator.generate_assets(preset)

    # Afficher guidelines icônes
    print(f"\n🎯 Guidelines Icônes :")
    icons = assets['icon_guidelines']
    print(f"   Style : {icons['style']} ({icons['corners']}, {icons['weight']})")
    print(f"   Bibliothèque : {icons['library']}")
    print(f"   Icônes recommandées : {', '.join(icons['recommended_icons'][:5])}")
    print(f"   CDN : {icons['cdn_links'][icons['library'].split('-')[0]]}")

    # Afficher prompts illustrations
    print(f"\n🖼️ Prompts Illustrations IA :")
    for section, prompt in assets['illustration_prompts'].items():
        print(f"\n   {section.upper()} :")
        print(f"   {prompt[:100]}...")

    # Afficher patterns
    print(f"\n📐 Patterns SVG générés :")
    for name in assets['svg_patterns'].keys():
        print(f"   ✓ {name}.svg")

    # Afficher éléments décoratifs
    print(f"\n✨ Éléments décoratifs :")
    deco = assets['decorative_elements']
    print(f"   Border radius : {deco['border_radius']}")
    print(f"   Shadow style : {deco['shadow_style']}")
    print(f"   Gradient : {deco['gradient_type']}")
    print(f"   Animation : {deco['animation_style']}")

    # Sauvegarder
    output_path = Path("output_myhealthprac/visual_assets.json")
    with open(output_path, 'w') as f:
        json.dump(assets, f, indent=2)

    print(f"\n💾 Assets sauvegardés : {output_path}")

    print(f"\n" + "="*70)
    print(f"  ✅ Assets visuels générés automatiquement")
    print(f"="*70)
    print(f"\n💡 Usage :")
    print(f"   • Utiliser {icons['library']} pour les icônes")
    print(f"   • Copier les prompts dans Midjourney/DALL-E")
    print(f"   • Intégrer les patterns SVG comme backgrounds")
    print(f"   • Appliquer les guidelines pour cohérence totale")
