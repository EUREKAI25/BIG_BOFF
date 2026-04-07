"""
Test pipeline sur myhealthprac.com
"""
import sys
from pathlib import Path

# Les modules sont installés avec pip install -e
# On peut les importer directement
from scraper import SiteScraper
from theme_composer import ThemeComposer
from theme_generator import ThemeGenerator
from page_builder import Page, Section, Column, HeroModule, PricingModule, PricingPlan, DesignTokens, render_page
import json
import re

base = Path(__file__).parent

# Output
output_dir = base / "output_myhealthprac"
output_dir.mkdir(exist_ok=True)

print("="*60)
print("  TEST PIPELINE - myhealthprac.com")
print("="*60)

# 1. Scraping
print("\n🔍 Étape 1/4 : Scraping...")
scraper = SiteScraper()

try:
    raw_styles = scraper.scrape("https://www.myhealthprac.com/", screenshot=True)

    print(f"   ✓ Extraction réussie :")
    print(f"      - {len(raw_styles.colors)} couleurs")
    print(f"      - {len(raw_styles.backgrounds)} backgrounds")
    print(f"      - {len(raw_styles.shadows)} shadows")
    print(f"      - {len(raw_styles.fonts)} fonts")
    print(f"      - {len(raw_styles.component_styles['buttons'])} boutons")
    print(f"      - {len(raw_styles.component_styles['inputs'])} inputs")
    print(f"      - {len(raw_styles.component_styles['cards'])} cards")
    print(f"      - Screenshot: {'✓' if raw_styles.screenshot_base64 else '✗'}")

    # Sauvegarder raw data
    raw_path = output_dir / "raw_styles.json"
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(raw_styles.model_dump(exclude={'screenshot_base64'}), f, indent=2, ensure_ascii=False)
    print(f"\n   💾 Raw data sauvegardé : {raw_path}")

    # Afficher quelques couleurs détectées
    print(f"\n   🎨 Couleurs principales détectées :")
    for color in raw_styles.colors[:5]:
        print(f"      - {color}")

    # Afficher fonts
    print(f"\n   📝 Fonts détectées :")
    for font in raw_styles.fonts[:3]:
        print(f"      - {font}")

    # 2. Theme Composition
    print("\n🎨 Étape 2/4 : Composition du thème...")
    composer = ThemeComposer()

    preset = composer.compose(
        raw_data=raw_styles.model_dump(),
        screenshot_base64=raw_styles.screenshot_base64
    )

    print(f"   ✓ ThemePreset créé :")
    print(f"      - Nom : {preset.name}")
    print(f"      - Mood : {preset.mood}")
    print(f"      - Use case : {preset.use_case}")
    print(f"      - Font headings : {preset.font_family_headings}")
    print(f"      - Font body : {preset.font_family_body}")
    print(f"      - Couleurs système : {list(preset.color_system.keys())}")

    if preset.key_characteristics:
        print(f"\n   ✨ Caractéristiques clés :")
        for char in preset.key_characteristics:
            print(f"      - {char}")

    # Sauvegarder preset
    preset_path = output_dir / "theme_preset.json"
    composer.save_preset(preset, str(preset_path))
    print(f"\n   💾 ThemePreset sauvegardé : {preset_path}")

    # 3. CSS Generation
    print("\n⚡ Étape 3/4 : Génération CSS...")
    generator = ThemeGenerator()
    css = generator.generate(preset.model_dump())

    css_path = output_dir / "theme.css"
    css_path.write_text(css, encoding='utf-8')
    print(f"   ✓ CSS généré ({len(css)} caractères)")
    print(f"   💾 CSS sauvegardé : {css_path}")

    # 4. Page de démo
    print("\n🏗️ Étape 4/4 : Génération page de démo...")

    # Convertir rgb en hex
    def rgb_to_hex(rgb_str):
        match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb_str)
        if match:
            r, g, b = map(int, match.groups())
            return f"#{r:02x}{g:02x}{b:02x}"
        return "#667eea"

    # Extraire couleurs du preset
    color_system = preset.color_system
    primary = color_system.get('primary', {}).get('base', 'rgb(102, 126, 234)')
    secondary = color_system.get('secondary', {}).get('base', 'rgb(118, 75, 162)')

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
                        title=f"Design inspiré de myhealthprac.com",
                        subtitle=preset.harmony_description or "Design extrait et reproduit automatiquement par EURKAI",
                        cta_primary={"label": "Voir le CSS", "href": "theme.css"},
                        cta_secondary={"label": "Voir le preset", "href": "theme_preset.json"}
                    ))
                ]
            ),
            Section(
                order=1,
                bg_color="#f7fafc",
                columns=[
                    Column(span=12, module=PricingModule(
                        title="Design System détecté",
                        subtitle="Analyse automatique du site",
                        plans=[
                            PricingPlan(
                                name="Thème généré",
                                price="Auto",
                                features=preset.key_characteristics or [
                                    f"Primary: {primary}",
                                    f"Secondary: {secondary}",
                                    f"Font: {preset.font_family_headings}",
                                    f"Mood: {preset.mood}",
                                    f"Use case: {preset.use_case}"
                                ],
                                is_featured=True,
                                cta_label="Télécharger CSS",
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
    print(f"   ✓ Page HTML générée")
    print(f"   💾 Démo sauvegardée : {demo_path}")

    print("\n" + "="*60)
    print("  ✅ PIPELINE TERMINÉ AVEC SUCCÈS")
    print("="*60)
    print(f"\n📁 Fichiers générés dans : {output_dir}")
    print(f"   - raw_styles.json (tokens bruts)")
    print(f"   - theme_preset.json (seed EURKAI)")
    print(f"   - theme.css (CSS complet)")
    print(f"   - demo.html (page de démo)")

    print(f"\n🎨 Thème : {preset.name}")
    print(f"   Mood : {preset.mood}")
    print(f"   Font : {preset.font_family_headings}")

    if preset.harmony_description:
        print(f"\n💬 Description : {preset.harmony_description}")

    print(f"\n🌐 Ouvrir la démo : open {demo_path}")

    # Ouvrir automatiquement
    import subprocess
    subprocess.run(['open', str(demo_path)])

except Exception as e:
    print(f"\n❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()
