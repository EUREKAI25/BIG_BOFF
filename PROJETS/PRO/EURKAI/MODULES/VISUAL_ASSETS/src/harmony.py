"""
Harmony Transfer - Applique l'harmonie d'un preset à une nouvelle couleur.

Principe : Extraire les rapports relatifs (HSL), les appliquer à une couleur cible.
"""
import json
from pathlib import Path
import colorsys
import re


def rgb_str_to_tuple(rgb_str):
    """Convertit 'rgb(r, g, b)' en (r, g, b)."""
    match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb_str)
    if match:
        return tuple(map(int, match.groups()))
    return (128, 128, 128)


def rgb_to_hsl(r, g, b):
    """Convertit RGB (0-255) en HSL (H:0-360, S:0-1, L:0-1)."""
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return (h * 360, s, l)


def hsl_to_rgb(h, s, l):
    """Convertit HSL en RGB (0-255)."""
    r, g, b = colorsys.hls_to_rgb(h/360, l, s)
    return (int(r*255), int(g*255), int(b*255))


def analyze_harmony(preset):
    """
    Analyse les rapports entre couleurs d'un preset.

    Returns:
        {
            "primary_hsl": (h, s, l),
            "relationships": {
                "secondary": {"hue_diff": +2, "sat_diff": +0.08, "light_diff": -0.13},
                "accent": {...}
            }
        }
    """
    color_system = preset['color_system']

    # Primary comme référence
    primary_rgb = rgb_str_to_tuple(color_system['primary']['base'])
    primary_hsl = rgb_to_hsl(*primary_rgb)

    # Analyser secondary
    secondary_rgb = rgb_str_to_tuple(color_system['secondary']['base'])
    secondary_hsl = rgb_to_hsl(*secondary_rgb)

    # Calculer rapports
    relationships = {
        "secondary": {
            "hue_diff": secondary_hsl[0] - primary_hsl[0],
            "sat_diff": secondary_hsl[1] - primary_hsl[1],
            "light_diff": secondary_hsl[2] - primary_hsl[2]
        }
    }

    # Si accent existe
    if 'dark' in color_system['primary']:
        accent_rgb = rgb_str_to_tuple(color_system['primary']['dark'])
        accent_hsl = rgb_to_hsl(*accent_rgb)
        relationships["accent"] = {
            "hue_diff": accent_hsl[0] - primary_hsl[0],
            "sat_diff": accent_hsl[1] - primary_hsl[1],
            "light_diff": accent_hsl[2] - primary_hsl[2]
        }

    return {
        "primary_hsl": primary_hsl,
        "relationships": relationships
    }


def apply_harmony(target_color_hex, harmony_analysis, preset_name="Variant"):
    """
    Applique l'harmonie à une couleur cible.

    Args:
        target_color_hex: Couleur cible (ex: "#3b82f6")
        harmony_analysis: Résultat de analyze_harmony()
        preset_name: Nom du nouveau preset

    Returns:
        Nouveau preset avec couleurs dérivées
    """
    # Convertir couleur cible en HSL
    hex_color = target_color_hex.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    target_hsl = rgb_to_hsl(r, g, b)

    # Appliquer rapports
    relationships = harmony_analysis['relationships']

    # Primary = target
    primary_rgb = (r, g, b)

    # Secondary = primary + rapports
    sec_rel = relationships['secondary']
    secondary_hsl = (
        (target_hsl[0] + sec_rel['hue_diff']) % 360,
        max(0, min(1, target_hsl[1] + sec_rel['sat_diff'])),
        max(0, min(1, target_hsl[2] + sec_rel['light_diff']))
    )
    secondary_rgb = hsl_to_rgb(*secondary_hsl)

    # Accent (si existe)
    if 'accent' in relationships:
        acc_rel = relationships['accent']
        accent_hsl = (
            (target_hsl[0] + acc_rel['hue_diff']) % 360,
            max(0, min(1, target_hsl[1] + acc_rel['sat_diff'])),
            max(0, min(1, target_hsl[2] + acc_rel['light_diff']))
        )
        accent_rgb = hsl_to_rgb(*accent_hsl)
    else:
        accent_rgb = secondary_rgb

    # Light = primary + 15% lightness
    light_hsl = (target_hsl[0], target_hsl[1], min(1, target_hsl[2] + 0.15))
    light_rgb = hsl_to_rgb(*light_hsl)

    # Créer nouveau preset
    new_preset = {
        "name": preset_name,
        "mood": "variant",
        "source": "harmony_transfer",
        "color_system": {
            "primary": {
                "base": f"rgb{primary_rgb}",
                "light": f"rgb{light_rgb}",
                "dark": f"rgb{accent_rgb}"
            },
            "secondary": {
                "base": f"rgb{secondary_rgb}",
                "light": f"rgb{light_rgb}",
                "dark": f"rgb{accent_rgb}"
            }
        },
        "harmony_source": target_color_hex
    }

    return new_preset


# === DEMO ===

print("="*70)
print("  HARMONY TRANSFER - Générer variantes de couleurs")
print("="*70)

# Charger preset original (myhealthprac)
preset_path = Path("output_myhealthprac/theme_preset_v2.json")
with open(preset_path) as f:
    original_preset = json.load(f)

print(f"\n📊 Preset original : {original_preset['name']}")
print(f"   Couleur primaire : {original_preset['color_system']['primary']['base']}")

# Analyser harmonie
print(f"\n🔍 Analyse de l'harmonie...")
harmony = analyze_harmony(original_preset)

print(f"   Primary HSL : H={harmony['primary_hsl'][0]:.1f}°, S={harmony['primary_hsl'][1]:.2f}, L={harmony['primary_hsl'][2]:.2f}")
print(f"   Rapports détectés :")
for key, rel in harmony['relationships'].items():
    print(f"      - {key}: ΔH={rel['hue_diff']:.1f}°, ΔS={rel['sat_diff']:+.2f}, ΔL={rel['light_diff']:+.2f}")

# Générer 5 variantes
print(f"\n🎨 Génération de 5 variantes...")

variants = [
    ("#3b82f6", "Blue Variant"),      # Bleu
    ("#ef4444", "Red Variant"),       # Rouge
    ("#10b981", "Green Variant"),     # Vert
    ("#8b5cf6", "Purple Variant"),    # Violet
    ("#f59e0b", "Amber Variant")      # Ambre
]

output_dir = Path("output_myhealthprac/variants")
output_dir.mkdir(exist_ok=True)

for color_hex, name in variants:
    new_preset = apply_harmony(color_hex, harmony, name)

    # Sauvegarder
    variant_path = output_dir / f"{name.lower().replace(' ', '_')}.json"
    with open(variant_path, 'w') as f:
        json.dump(new_preset, f, indent=2)

    print(f"   ✅ {name} ({color_hex})")
    print(f"      Primary: {new_preset['color_system']['primary']['base']}")
    print(f"      Secondary: {new_preset['color_system']['secondary']['base']}")

# Générer HTML de comparaison
print(f"\n🏗️ Génération page de comparaison...")

html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Harmony Transfer - Variantes</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, sans-serif;
            padding: 48px 24px;
            background: #fafafa;
        }
        .header {
            text-align: center;
            margin-bottom: 48px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .variant {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .variant h3 {
            margin-bottom: 16px;
            font-size: 18px;
        }
        .palette {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 16px;
        }
        .color-box {
            height: 80px;
            border-radius: 8px;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .btn {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Harmony Transfer</h1>
        <p style="margin-top: 8px; color: #666;">Même harmonie, 5 couleurs différentes</p>
        <p style="margin-top: 16px; padding: 16px; background: white; border-radius: 8px; max-width: 600px; margin: 16px auto;">
            <strong>Principe :</strong> Les rapports entre couleurs (HSL) sont préservés, seule la couleur de base change.
        </p>
    </div>

    <div class="grid">
"""

# Ajouter variantes
for color_hex, name in variants:
    variant_path = output_dir / f"{name.lower().replace(' ', '_')}.json"
    with open(variant_path) as f:
        variant = json.load(f)

    primary = variant['color_system']['primary']['base']
    secondary = variant['color_system']['secondary']['base']
    accent = variant['color_system']['primary']['dark']

    # Extraire RGB pour background
    primary_rgb = rgb_str_to_tuple(primary)
    secondary_rgb = rgb_str_to_tuple(secondary)
    accent_rgb = rgb_str_to_tuple(accent)

    html += f"""
        <div class="variant">
            <h3>{name}</h3>
            <div class="palette">
                <div class="color-box" style="background: rgb{primary_rgb};" title="{primary}"></div>
                <div class="color-box" style="background: rgb{secondary_rgb};" title="{secondary}"></div>
                <div class="color-box" style="background: rgb{accent_rgb};" title="{accent}"></div>
            </div>
            <button class="btn" style="background: rgb{primary_rgb}; color: white;">Bouton Primary</button>
        </div>
    """

html += """
    </div>
</body>
</html>
"""

demo_path = output_dir / "comparison.html"
demo_path.write_text(html)

print(f"   ✅ Comparaison : {demo_path}")

print(f"\n" + "="*70)
print(f"  ✅ 5 variantes générées avec la MÊME harmonie")
print(f"="*70)
print(f"\n📁 Fichiers : {output_dir}")
print(f"   • 5 presets JSON")
print(f"   • comparison.html (ouverture...)")

# Ouvrir
import subprocess
subprocess.run(['open', str(demo_path)])

print(f"\n💡 Même structure relationnelle, 5 palettes différentes !")
