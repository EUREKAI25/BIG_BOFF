"""
Pipeline EURKAI v2 - Merge CSS + Image Analysis
Cas myhealthprac.com : CSS monochrome + Vidéo colorée
"""
import sys
from pathlib import Path
import json
import base64

sys.path.insert(0, "scraper/src")
from image_analyzer import ImageAnalyzer

output_dir = Path("output_myhealthprac")

print("="*70)
print("  PIPELINE EURKAI v2 - CSS + IMAGE ANALYSIS")
print("="*70)

# Étape 1 : Charger données CSS
print("\n📊 Étape 1 : Analyse CSS")
with open(output_dir / "raw_styles.json") as f:
    css_data = json.load(f)

print(f"   ✓ {len(css_data['colors'])} couleurs CSS")
print(f"   → Couleurs : {css_data['colors'][:3]}")

# Étape 2 : Analyse IMAGE
print("\n🎨 Étape 2 : Analyse Screenshot (couleurs réelles)")

screenshot_b64 = base64.b64encode(
    (output_dir / "screenshot.png").read_bytes()
).decode('utf-8')

analyzer = ImageAnalyzer()
img_result = analyzer.analyze_screenshot(screenshot_b64, num_colors=10)

print(f"   ✓ Monochrome : {img_result['is_monochrome']}")
print(f"   ✓ Mood : {img_result['color_mood']}")
print(f"\n   🎨 Couleurs dominantes de l'image :")
for i, (color, pct) in enumerate(zip(img_result['dominant_colors'][:5], img_result['color_percentages'][:5])):
    r, g, b = color
    print(f"      {i+1}. rgb({r}, {g}, {b}) - {pct*100:.1f}%")

# Étape 3 : MERGE - Décision intelligente
print("\n🔀 Étape 3 : Merge CSS + Image")

# Compter couleurs grises dans CSS
gray_colors = [c for c in css_data['colors'] if 'rgb(0' in c or 'rgb(255' in c or 'rgb(241' in c or 'rgb(31' in c]
css_is_monochrome = len(gray_colors) >= 4  # Au moins 4 couleurs grises (sur 7 total = majoritaire)
image_has_colors = not img_result['is_monochrome']

print(f"   • CSS : {len(gray_colors)} couleurs grises / {len(css_data['colors'])} total")
print(f"   • Image : Monochrome = {img_result['is_monochrome']}")

if css_is_monochrome and image_has_colors:
    print(f"   ⚠️ Détecté : CSS monochrome MAIS image colorée !")
    print(f"   → Utilisation des couleurs de l'IMAGE comme source primaire")
    use_image_colors = True
else:
    print(f"   ✓ CSS et image cohérents")
    print(f"   → Utilisation des couleurs CSS")
    use_image_colors = False

# Étape 4 : Créer preset enrichi
print("\n⚙️ Étape 4 : Génération ThemePreset enrichi")

if use_image_colors:
    # Extraire top 3 couleurs de l'image
    dominant = img_result['dominant_colors']

    preset = {
        "name": "MyHealthPrac Natural",
        "mood": img_result['color_mood'],  # "warm"
        "use_case": "wellness",
        "source": "image_analysis",  # Nouveau !
        "color_system": {
            "primary": {
                "base": f"rgb{dominant[0]}",  # Beige doré
                "light": f"rgb{dominant[2]}",  # Beige clair
                "dark": f"rgb{dominant[3]}"    # Terre cuite
            },
            "secondary": {
                "base": f"rgb{dominant[1]}",   # Bronze
                "light": f"rgb{dominant[2]}",
                "dark": f"rgb{dominant[4]}"    # Marron foncé
            },
            "neutral": {
                "base": "rgb(241, 241, 241)",  # CSS neutral
                "light": "rgb(255, 255, 255)",
                "dark": "rgb(128, 128, 128)"
            }
        },
        "font_family_headings": "Neue Montreal",
        "font_family_body": "Neue Montreal",
        "shadow_system": {
            "sm": "0 1px 2px rgba(124, 72, 34, 0.1)",  # Shadow avec couleur primaire
            "md": "0 4px 6px rgba(124, 72, 34, 0.15)",
            "lg": "0 10px 15px rgba(124, 72, 34, 0.2)"
        },
        "border_system": {
            "radius": {"sm": "4px", "md": "8px", "lg": "12px"}
        },
        "harmony_description": "Palette naturelle et chaleureuse inspirée de tons or, terre et bois. Design minimaliste avec identité forte portée par les médias (vidéo/images).",
        "key_characteristics": [
            "Palette warm/naturelle (or, terre, bois)",
            "Mood : chaleureux et organique",
            f"Couleur dominante : {img_result['color_mood']} ({dominant[0]})",
            "Contraste CSS minimaliste + Médias riches",
            "Identité visuelle portée par la vidéo de fond"
        ],
        "image_generation_prompt": "Natural wellness imagery with warm golden tones, earthy browns, organic textures. Soft lighting, serene atmosphere, health and nature themes."
    }
else:
    preset = {
        "name": "MyHealthPrac Minimal",
        "mood": "minimal",
        "source": "css_analysis",
        "color_system": {
            "primary": {
                "base": "rgb(31, 31, 31)",
                "light": "rgb(128, 128, 128)",
                "dark": "rgb(0, 0, 0)"
            }
        }
    }

# Sauvegarder
preset_path = output_dir / "theme_preset_v2.json"
with open(preset_path, 'w') as f:
    json.dump(preset, f, indent=2)

print(f"   ✅ Preset créé : {preset['name']}")
print(f"   ✓ Source : {preset['source']}")
print(f"   ✓ Mood : {preset['mood']}")
print(f"   ✓ Couleur primaire : {preset['color_system']['primary']['base']}")
print(f"   💾 Sauvegardé : {preset_path}")

# Étape 5 : CSS avec vraies couleurs
print("\n⚡ Étape 5 : Génération CSS avec palette naturelle")

primary_rgb = preset['color_system']['primary']['base']
secondary_rgb = preset['color_system']['secondary']['base']

css = f"""/*
 * Thème EURKAI - {preset['name']}
 * Source : {preset['source']} (myhealthprac.com)
 * Mood : {preset['mood']}
 *
 * Palette naturelle extraite de la vidéo de fond
 */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');

:root {{
  /* Couleurs naturelles (extraites de l'image) */
  --color-primary: {primary_rgb};           /* Beige doré */
  --color-primary-light: {preset['color_system']['primary']['light']};
  --color-primary-dark: {preset['color_system']['primary']['dark']};

  --color-secondary: {secondary_rgb};        /* Bronze */
  --color-secondary-light: {preset['color_system']['secondary']['light']};
  --color-secondary-dark: {preset['color_system']['secondary']['dark']};

  --color-neutral: rgb(241, 241, 241);
  --color-text: rgb(31, 31, 31);

  /* Typography */
  --font-family: 'Inter', sans-serif;

  /* Shadows avec couleur primaire */
  --shadow-sm: {preset['shadow_system']['sm']};
  --shadow-md: {preset['shadow_system']['md']};
  --shadow-lg: {preset['shadow_system']['lg']};

  --radius-md: {preset['border_system']['radius']['md']};
}}

body {{
  font-family: var(--font-family);
  color: var(--color-text);
  background: var(--color-neutral);
}}

.hero {{
  background: linear-gradient(135deg, var(--color-primary-light), var(--color-primary));
  color: white;
  padding: 64px 24px;
  text-align: center;
}}

.btn-primary {{
  background: var(--color-primary);
  color: white;
  padding: 12px 32px;
  border-radius: var(--radius-md);
  border: none;
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: all 0.2s;
}}

.btn-primary:hover {{
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}}

.card {{
  background: white;
  border: 1px solid var(--color-primary-light);
  border-radius: var(--radius-md);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}}
"""

css_path = output_dir / "theme_v2.css"
css_path.write_text(css)
print(f"   ✅ CSS généré ({len(css)} car.)")
print(f"   💾 {css_path}")

# Étape 6 : Demo
print("\n🏗️ Étape 6 : Page de démo")

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{preset['name']} - EURKAI</title>
    <link rel="stylesheet" href="theme_v2.css">
</head>
<body>
    <div class="hero">
        <h1>🎨 {preset['name']}</h1>
        <p>{preset['harmony_description']}</p>
    </div>

    <div style="max-width: 800px; margin: 48px auto; padding: 0 24px;">
        <div class="card">
            <h2 style="margin-bottom: 16px;">Palette Naturelle Extraite</h2>
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 24px 0;">
                {''.join(f'<div style="height: 80px; background: rgb{color}; border-radius: 4px; border: 1px solid rgba(0,0,0,0.1);"></div>' for color in img_result['dominant_colors'][:5])}
            </div>

            <h3 style="margin-top: 24px;">Caractéristiques</h3>
            <ul style="list-style: none; padding: 0;">
                {''.join(f'<li style="padding: 8px 0; border-bottom: 1px solid var(--color-neutral);">✓ {char}</li>' for char in preset['key_characteristics'])}
            </ul>

            <div style="margin-top: 24px; padding: 16px; background: var(--color-neutral); border-radius: 8px;">
                <strong>Prompt génération d'images :</strong>
                <p style="margin-top: 8px; font-style: italic;">{preset.get('image_generation_prompt', '')}</p>
            </div>

            <button class="btn-primary" style="margin-top: 24px; width: 100%;">Télécharger le thème</button>
        </div>
    </div>
</body>
</html>"""

demo_path = output_dir / "demo_v2.html"
demo_path.write_text(html)
print(f"   ✅ Demo : {demo_path}")

# Résumé
print("\n" + "="*70)
print("  ✅ PIPELINE v2 TERMINÉ - Analyse CSS + Image")
print("="*70)
print(f"\n🎨 Résultat :")
print(f"   • CSS était monochrome (noir/blanc/gris)")
print(f"   • IMAGE révèle palette {preset['mood']} (or/terre/nature)")
print(f"   • Thème final utilise les couleurs de l'IMAGE")
print(f"\n💡 Lesson : L'harmonie vient souvent des MÉDIAS, pas du CSS !")

# Ouvrir
import subprocess
subprocess.run(['open', str(demo_path)])

print(f"\n✨ Démo avec vraies couleurs ouverte !")
