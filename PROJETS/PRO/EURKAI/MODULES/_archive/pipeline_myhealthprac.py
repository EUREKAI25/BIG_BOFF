"""
Pipeline complet sur myhealthprac.com
Utilise les données déjà scrapées pour aller plus vite.
"""
import sys
from pathlib import Path
import json
import re

# Import direct depuis les sources (chemins absolus)
base = Path(__file__).parent

# Scraper
sys.path.insert(0, str(base / "scraper" / "src"))
from scraper import SiteScraper, RawStyles

# Page Builder
sys.path.insert(0, str(base / "page_builder" / "src"))
import importlib.util
spec = importlib.util.spec_from_file_location("page_builder_module", base / "page_builder" / "src" / "__init__.py")
page_builder_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page_builder_module)
Page = page_builder_module.Page
Section = page_builder_module.Section
Column = page_builder_module.Column
HeroModule = page_builder_module.HeroModule
PricingModule = page_builder_module.PricingModule
PricingPlan = page_builder_module.PricingPlan
DesignTokens = page_builder_module.DesignTokens
render_page = page_builder_module.render_page

# Theme Composer
sys.path.insert(0, str(base / "theme_composer" / "theme_composer"))
from composer import ThemeComposer

# Theme Generator
sys.path.insert(0, str(base / "theme_generator" / "theme_generator"))
from generator import ThemeGenerator

output_dir = base / "output_myhealthprac"
output_dir.mkdir(exist_ok=True)

print("="*70)
print("  PIPELINE COMPLET EURKAI - myhealthprac.com")
print("="*70)

# Étape 1 : Charger données scrapées (ou re-scraper si besoin)
print("\n🔍 Étape 1/4 : Chargement données...")

raw_json_path = output_dir / "raw_styles.json"
if raw_json_path.exists():
    print(f"   ✓ Utilisation données existantes : {raw_json_path}")
    with open(raw_json_path) as f:
        raw_data = json.load(f)

    # Re-scraper juste pour le screenshot (exclu du JSON)
    scraper = SiteScraper()
    full_raw = scraper.scrape("https://www.myhealthprac.com/", screenshot=True)
    raw_data['screenshot_base64'] = full_raw.screenshot_base64
else:
    print("   ⏳ Scraping du site...")
    scraper = SiteScraper()
    full_raw = scraper.scrape("https://www.myhealthprac.com/", screenshot=True)
    raw_data = full_raw.model_dump()

print(f"   ✓ Données prêtes ({len(raw_data['colors'])} couleurs, {len(raw_data['fonts'])} fonts)")

# Étape 2 : Theme Composition
print("\n🎨 Étape 2/4 : Analyse et composition du thème...")
print("   ⏳ Analyse avec Claude (peut prendre 10-15s)...")

composer = ThemeComposer()
preset = composer.compose(
    raw_data=raw_data,
    screenshot_base64=raw_data.get('screenshot_base64')
)

print(f"   ✅ ThemePreset créé :")
print(f"      - Nom : {preset.name}")
print(f"      - Mood : {preset.mood}")
print(f"      - Use case : {preset.use_case}")
print(f"      - Font headings : {preset.font_family_headings}")
print(f"      - Font body : {preset.font_family_body}")
print(f"      - Couleurs : {list(preset.color_system.keys())}")

if preset.harmony_description:
    print(f"\n   💬 Description de l'harmonie :")
    print(f"      {preset.harmony_description}")

if preset.key_characteristics:
    print(f"\n   ✨ Caractéristiques clés :")
    for char in preset.key_characteristics:
        print(f"      • {char}")

# Sauvegarder preset
preset_path = output_dir / "theme_preset.json"
composer.save_preset(preset, str(preset_path))
print(f"\n   💾 ThemePreset : {preset_path}")

# Étape 3 : Génération CSS
print("\n⚡ Étape 3/4 : Génération du CSS...")

generator = ThemeGenerator()
css = generator.generate(preset.model_dump())

css_path = output_dir / "theme.css"
css_path.write_text(css, encoding='utf-8')
print(f"   ✅ CSS généré ({len(css)} caractères)")
print(f"   💾 CSS : {css_path}")

# Étape 4 : Page de démo
print("\n🏗️ Étape 4/4 : Génération page de démo...")

# Convertir rgb en hex
def rgb_to_hex(rgb_str):
    match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb_str)
    if match:
        r, g, b = map(int, match.groups())
        return f"#{r:02x}{g:02x}{b:02x}"
    return "#333333"  # Gris par défaut

# Extraire couleurs
color_system = preset.color_system
primary_rgb = color_system.get('primary', {}).get('base') or color_system.get('neutral', {}).get('dark', 'rgb(31, 31, 31)')
secondary_rgb = color_system.get('secondary', {}).get('base') or color_system.get('neutral', {}).get('base', 'rgb(128, 128, 128)')

primary_hex = rgb_to_hex(primary_rgb)
secondary_hex = rgb_to_hex(secondary_rgb)

print(f"   🎨 Couleurs utilisées :")
print(f"      Primary: {primary_rgb} → {primary_hex}")
print(f"      Secondary: {secondary_rgb} → {secondary_hex}")

tokens = DesignTokens(
    primary_color=primary_hex,
    secondary_color=secondary_hex,
    font_size_base=16
)

# Créer page de démo
page = Page(
    title=f"EURKAI - {preset.name}",
    description=preset.harmony_description or "Thème généré automatiquement",
    design_tokens=tokens,
    sections=[
        Section(
            order=0,
            columns=[
                Column(span=12, module=HeroModule(
                    badge=f"🎨 {preset.mood.upper()} • {preset.use_case.upper()}",
                    title=f"Thème inspiré de myhealthprac.com",
                    subtitle=preset.harmony_description or "Design system extrait et reproduit automatiquement par EURKAI",
                    cta_primary={"label": "📄 Voir le CSS", "href": "theme.css"},
                    cta_secondary={"label": "🔧 Voir le Preset", "href": "theme_preset.json"}
                ))
            ]
        ),
        Section(
            order=1,
            bg_color="#f7f7f7",
            columns=[
                Column(span=12, module=PricingModule(
                    title="Design System Détecté",
                    subtitle="Analyse automatique du site source",
                    plans=[
                        PricingPlan(
                            name="Thème EURKAI",
                            price="Auto-généré",
                            features=preset.key_characteristics[:5] if preset.key_characteristics else [
                                f"Mood: {preset.mood}",
                                f"Use case: {preset.use_case}",
                                f"Font: {preset.font_family_headings}",
                                f"Système de couleurs: {', '.join(preset.color_system.keys())}",
                                "Design minimaliste monochrome"
                            ],
                            is_featured=True,
                            cta_label="Télécharger le thème",
                            cta_href="theme.css"
                        )
                    ]
                ))
            ]
        )
    ]
)

html = render_page(page)
demo_path = output_dir / "demo.html"
demo_path.write_text(html, encoding='utf-8')
print(f"   ✅ Page de démo générée")
print(f"   💾 Demo : {demo_path}")

# Résumé final
print("\n" + "="*70)
print("  ✅ PIPELINE TERMINÉ AVEC SUCCÈS")
print("="*70)

print(f"\n📁 Fichiers générés dans {output_dir.name}/ :")
print(f"   • raw_styles.json      - Tokens bruts extraits")
print(f"   • theme_preset.json    - Seed EURKAI propriétaire")
print(f"   • theme.css            - CSS complet ({len(css)} car.)")
print(f"   • demo.html            - Page de démonstration")
print(f"   • screenshot.png       - Capture d'écran du site")

print(f"\n🎨 Thème généré : {preset.name}")
print(f"   • Mood : {preset.mood}")
print(f"   • Use case : {preset.use_case}")
print(f"   • Font : {preset.font_family_headings}")
print(f"   • Couleurs : {', '.join(preset.color_system.keys())}")

if preset.harmony_description:
    print(f"\n💭 « {preset.harmony_description} »")

print(f"\n🌐 Ouverture automatique de la démo...")

# Ouvrir la démo
import subprocess
subprocess.run(['open', str(demo_path)])

print(f"\n✨ Pipeline EURKAI terminé !")
