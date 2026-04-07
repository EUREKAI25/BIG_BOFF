"""
Pipeline EURKAI simplifié - myhealthprac.com
Sans dépendances complexes, juste le core.
"""
import json
from pathlib import Path

output_dir = Path("output_myhealthprac")
output_dir.mkdir(exist_ok=True)

print("="*70)
print("  PIPELINE EURKAI - myhealthprac.com")
print("="*70)

# Étape 1 : Charger données scrapées
print("\n📊 Étape 1 : Données scrapées")
with open(output_dir / "raw_styles.json") as f:
    raw_data = json.load(f)

print(f"   ✓ {len(raw_data['colors'])} couleurs")
print(f"   ✓ {len(raw_data['fonts'])} fonts")
print(f"   ✓ {len(raw_data['component_styles']['buttons'])} boutons")

# Afficher couleurs
print(f"\n   🎨 Couleurs extraites :")
for color in raw_data['colors']:
    print(f"      - {color}")

# Étape 2 : Analyse simple (sans LLM pour l'instant)
print("\n🎨 Étape 2 : Analyse du design")

# Détecter que c'est monochrome
has_colors = any('rgb(0' not in c and 'rgb(255' not in c and 'rgb(241' not in c and 'rgb(31' not in c for c in raw_data['colors'])

if not has_colors:
    print("   ✓ Design MONOCHROME détecté (tons de gris uniquement)")
    mood = "minimal"
    use_case = "professional"
else:
    print("   ✓ Design avec couleurs")
    mood = "colorful"
    use_case = "creative"

# Font principale
main_font = raw_data['fonts'][0] if raw_data['fonts'] else "sans-serif"
clean_font = main_font.split(',')[0].strip().strip('"')
print(f"   ✓ Font principale : {clean_font}")

# Étape 3 : Créer preset minimal
print("\n⚙️ Étape 3 : Génération ThemePreset")

preset = {
    "name": "MyHealthPrac Minimal",
    "mood": mood,
    "use_case": use_case,
    "color_system": {
        "primary": {
            "base": "rgb(31, 31, 31)",  # Gris foncé
            "light": "rgb(128, 128, 128)",
            "dark": "rgb(0, 0, 0)"
        },
        "neutral": {
            "base": "rgb(241, 241, 241)",  # Gris clair
            "light": "rgb(255, 255, 255)",
            "dark": "rgb(200, 200, 200)"
        }
    },
    "font_family_headings": clean_font or "Inter",
    "font_family_body": clean_font or "Inter",
    "shadow_system": {
        "sm": "0 1px 2px rgba(0,0,0,0.05)",
        "md": "0 4px 6px rgba(0,0,0,0.07)",
        "lg": "0 10px 15px rgba(0,0,0,0.1)"
    },
    "border_system": {
        "radius": {
            "sm": "4px",
            "md": "8px",
            "lg": "12px"
        }
    },
    "harmony_description": "Design minimaliste et épuré avec une palette monochrome sophistiquée. L'accent est mis sur la typographie et les espaces blancs.",
    "key_characteristics": [
        "Palette monochrome (noir, blanc, gris)",
        f"Typographie: {clean_font}",
        "Design ultra-minimaliste",
        "Espaces généreux",
        "Contraste élevé pour la lisibilité"
    ]
}

# Sauvegarder
preset_path = output_dir / "theme_preset.json"
with open(preset_path, 'w') as f:
    json.dump(preset, f, indent=2)

print(f"   ✓ Preset créé : {preset['name']}")
print(f"   ✓ Mood : {preset['mood']}")
print(f"   ✓ Font : {preset['font_family_headings']}")
print(f"   💾 Sauvegardé : {preset_path}")

# Étape 4 : Générer CSS minimal
print("\n⚡ Étape 4 : Génération CSS")

css = f"""/*
 * Thème EURKAI - {preset['name']}
 * Source : myhealthprac.com
 * Mood : {preset['mood']}
 */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');

:root {{
  /* Couleurs */
  --color-primary: {preset['color_system']['primary']['base']};
  --color-primary-light: {preset['color_system']['primary']['light']};
  --color-primary-dark: {preset['color_system']['primary']['dark']};
  --color-neutral: {preset['color_system']['neutral']['base']};
  --color-neutral-light: {preset['color_system']['neutral']['light']};
  --color-neutral-dark: {preset['color_system']['neutral']['dark']};

  /* Typographie */
  --font-family: '{preset['font_family_headings']}', sans-serif;
  --font-size-base: 16px;
  --line-height-base: 1.6;

  /* Shadows */
  --shadow-sm: {preset['shadow_system']['sm']};
  --shadow-md: {preset['shadow_system']['md']};
  --shadow-lg: {preset['shadow_system']['lg']};

  /* Border Radius */
  --radius-sm: {preset['border_system']['radius']['sm']};
  --radius-md: {preset['border_system']['radius']['md']};
  --radius-lg: {preset['border_system']['radius']['lg']};

  /* Spacing */
  --spacing-xs: 8px;
  --spacing-sm: 16px;
  --spacing-md: 24px;
  --spacing-lg: 32px;
  --spacing-xl: 48px;
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
  color: var(--color-primary);
  background: var(--color-neutral-light);
}}

.container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-md);
}}

.hero {{
  text-align: center;
  padding: var(--spacing-xl) var(--spacing-md);
  background: var(--color-neutral-light);
}}

.hero h1 {{
  font-size: 48px;
  font-weight: 700;
  margin-bottom: var(--spacing-sm);
  color: var(--color-primary-dark);
}}

.hero p {{
  font-size: 20px;
  color: var(--color-primary-light);
  margin-bottom: var(--spacing-lg);
}}

.btn {{
  display: inline-block;
  padding: 12px 32px;
  background: var(--color-primary);
  color: var(--color-neutral-light);
  text-decoration: none;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all 0.2s;
}}

.btn:hover {{
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}}

.card {{
  background: var(--color-neutral-light);
  border: 1px solid var(--color-neutral-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}}
"""

css_path = output_dir / "theme.css"
css_path.write_text(css)
print(f"   ✓ CSS généré ({len(css)} caractères)")
print(f"   💾 Sauvegardé : {css_path}")

# Étape 5 : HTML de démo
print("\n🏗️ Étape 5 : Page de démo")

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{preset['name']} - EURKAI</title>
    <link rel="stylesheet" href="theme.css">
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🎨 {preset['name']}</h1>
            <p>{preset['harmony_description']}</p>
            <a href="theme.css" class="btn">Télécharger le CSS</a>
        </div>

        <div style="margin-top: 48px;">
            <div class="card">
                <h2 style="margin-bottom: 16px;">Caractéristiques</h2>
                <ul style="list-style: none; padding: 0;">
                    {''.join(f'<li style="padding: 8px 0; border-bottom: 1px solid var(--color-neutral-dark);">✓ {char}</li>' for char in preset['key_characteristics'])}
                </ul>
            </div>
        </div>

        <div style="margin-top: 48px; text-align: center; padding: 32px; background: var(--color-neutral); border-radius: var(--radius-lg);">
            <p style="color: var(--color-primary-light);">Thème généré automatiquement par EURKAI</p>
            <p style="margin-top: 8px; font-size: 14px;">Source : myhealthprac.com • Mood : {preset['mood']}</p>
        </div>
    </div>
</body>
</html>"""

demo_path = output_dir / "demo.html"
demo_path.write_text(html)
print(f"   ✓ HTML généré")
print(f"   💾 Sauvegardé : {demo_path}")

# Résumé
print("\n" + "="*70)
print("  ✅ PIPELINE TERMINÉ")
print("="*70)
print(f"\n📁 Fichiers dans {output_dir.name}/ :")
print(f"   • theme_preset.json")
print(f"   • theme.css")
print(f"   • demo.html")

print(f"\n🎨 Thème : {preset['name']}")
for char in preset['key_characteristics']:
    print(f"   • {char}")

# Ouvrir
import subprocess
subprocess.run(['open', str(demo_path)])
subprocess.run(['open', str(css_path)])

print(f"\n✨ Démo ouverte automatiquement !")
