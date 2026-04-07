"""
Pipeline complet EURKAI : Site → Scraping → Theme → CSS → Page

Workflow :
1. Scraper extrait les tokens d'un site
2. ThemeComposer analyse et crée le seed
3. ThemeGenerator génère le CSS
4. PageBuilder rend la page avec le theme
"""
import sys
from pathlib import Path

# Ajouter les modules au path
sys.path.insert(0, str(Path(__file__).parent / "scraper/src"))
sys.path.insert(0, str(Path(__file__).parent / "theme_composer/src"))
sys.path.insert(0, str(Path(__file__).parent / "theme_generator/src"))
sys.path.insert(0, str(Path(__file__).parent / "page_builder/src"))

from scraper import SiteScraper
from composer import ThemeComposer
from generator import ThemeGenerator
from page_builder import Page, Section, Column, HeroModule, PricingModule, PricingPlan


def scrape_to_theme_pipeline(url: str, output_dir: Path):
    """Pipeline complet : URL → ThemePreset → CSS."""

    print(f"🔍 Étape 1/4 : Scraping de {url}...")
    scraper = SiteScraper()
    raw_styles = scraper.scrape(url, screenshot=True)

    # Sauvegarder raw data
    raw_path = output_dir / f"{Path(url).name}_raw.json"
    scraper.scrape_to_json(url, str(raw_path))
    print(f"   ✓ Raw data : {raw_path}")

    print(f"\n🎨 Étape 2/4 : Composition du thème...")
    composer = ThemeComposer()
    preset = composer.compose(
        raw_data=raw_styles.model_dump(),
        screenshot_base64=raw_styles.screenshot_base64
    )

    # Sauvegarder preset
    preset_path = output_dir / f"{Path(url).name}_preset.json"
    composer.save_preset(preset, str(preset_path))
    print(f"   ✓ ThemePreset : {preset_path}")
    print(f"   - Mood : {preset.mood}")
    print(f"   - Use case : {preset.use_case}")
    print(f"   - Font : {preset.font_family_headings}")

    print(f"\n⚡ Étape 3/4 : Génération CSS...")
    generator = ThemeGenerator()
    css = generator.generate(preset.model_dump())

    # Sauvegarder CSS
    css_path = output_dir / f"{Path(url).name}_theme.css"
    css_path.write_text(css, encoding='utf-8')
    print(f"   ✓ CSS : {css_path}")

    print(f"\n🏗️ Étape 4/4 : Génération page de démo...")

    # Créer une page de démo avec le theme
    # (On ne peut pas appliquer directement le CSS car page_builder a son propre système)
    # Mais on peut utiliser les couleurs du preset

    from src import DesignTokens, render_page

    # Extraire couleurs du preset
    color_system = preset.color_system
    primary = color_system.get('primary', {}).get('base', 'rgb(102, 126, 234)')
    secondary = color_system.get('secondary', {}).get('base', 'rgb(118, 75, 162)')

    # Convertir rgb(...) en hex pour DesignTokens
    def rgb_to_hex(rgb_str):
        import re
        match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb_str)
        if match:
            r, g, b = map(int, match.groups())
            return f"#{r:02x}{g:02x}{b:02x}"
        return "#667eea"

    tokens = DesignTokens(
        primary_color=rgb_to_hex(primary),
        secondary_color=rgb_to_hex(secondary),
        font_size_base=16
    )

    page = Page(
        title=f"Démo - {preset.name}",
        description=preset.harmony_description,
        design_tokens=tokens,
        sections=[
            Section(
                order=0,
                columns=[
                    Column(span=12, module=HeroModule(
                        badge=f"Mood: {preset.mood} | Use case: {preset.use_case}",
                        title=f"Thème inspiré de {url}",
                        subtitle=preset.harmony_description or "Design extrait et reproduit automatiquement",
                        cta_primary={"label": "Voir le CSS", "href": str(css_path)},
                        cta_secondary={"label": "Site original", "href": url}
                    ))
                ]
            ),
            Section(
                order=1,
                bg_color="#f7fafc",
                columns=[
                    Column(span=12, module=PricingModule(
                        title="Caractéristiques détectées",
                        plans=[
                            PricingPlan(
                                name="Design System",
                                price="Auto-détecté",
                                features=preset.key_characteristics or [
                                    f"Couleur primaire: {primary}",
                                    f"Font: {preset.font_family_headings}",
                                    f"Mood: {preset.mood}"
                                ],
                                is_featured=True,
                                cta_label="Télécharger CSS",
                                cta_href=str(css_path)
                            )
                        ]
                    ))
                ]
            )
        ]
    )

    html = render_page(page)
    demo_path = output_dir / f"{Path(url).name}_demo.html"
    demo_path.write_text(html, encoding='utf-8')
    print(f"   ✓ Démo HTML : {demo_path}")

    print(f"\n✅ Pipeline terminé ! Fichiers générés dans {output_dir}")

    return preset, css, html


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline EURKAI : Site → Theme → CSS")
    parser.add_argument("url", help="URL du site à analyser")
    parser.add_argument("--output", default="./output", help="Répertoire de sortie")

    args = parser.parse_args()

    # Créer output dir
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)

    # Lancer pipeline
    print(f"\n{'='*60}")
    print(f"  PIPELINE EURKAI - Site → Theme → CSS → Page")
    print(f"{'='*60}\n")

    try:
        preset, css, html = scrape_to_theme_pipeline(args.url, output_dir)

        print(f"\n{'='*60}")
        print(f"  ✅ SUCCÈS")
        print(f"{'='*60}")
        print(f"\n📁 Fichiers générés :")
        print(f"   - Raw data (JSON)")
        print(f"   - ThemePreset (JSON)")
        print(f"   - CSS généré")
        print(f"   - Page démo (HTML)")
        print(f"\n🎨 Thème : {preset.name}")
        print(f"   Mood : {preset.mood}")
        print(f"   Use case : {preset.use_case}")
        print(f"\n💡 Commande pour tester un autre site :")
        print(f"   python example_pipeline.py https://example.com --output ./output")

    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
