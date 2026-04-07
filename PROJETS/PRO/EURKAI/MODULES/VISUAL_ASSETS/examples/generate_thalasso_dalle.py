"""
Génération d'images IA pour site Thalasso
Utilise DALL-E 3 via MODEL_EXECUTOR + visual_assets_generator pour cohérence totale
"""
import json
import os
from pathlib import Path
import sys

# Import du générateur
sys.path.insert(0, str(Path(__file__).parent))
from visual_assets_generator import VisualAssetsGenerator

# Accès unifié aux modèles IA via MODEL_EXECUTOR
_MODULES_DIR = Path(__file__).parent.parent.parent
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))
from MODEL_EXECUTOR import model_execute

print("="*70)
print("  GÉNÉRATION IMAGES IA — THALASSO")
print("="*70)

# Créer preset thalasso
print("\n🌊 Étape 1 : Création preset Thalasso")

preset_thalasso = {
    "name": "Thalasso & Spa",
    "mood": "cool",  # Bleu, apaisant, zen
    "use_case": "wellness",
    "key_characteristics": [
        "Palette cool/marine (bleus, turquoise, blancs)",
        "Mood : apaisant, zen, luxueux",
        "Ambiance : spa, océan, relaxation",
        "Style : élégant, épuré, moderne",
        "Éléments : eau, vagues, minéralité, lumière douce"
    ],
    "color_system": {
        "primary": {
            "base": "rgb(72, 149, 178)",    # Bleu océan
            "light": "rgb(157, 201, 219)",  # Bleu clair
            "dark": "rgb(44, 98, 120)"      # Bleu profond
        },
        "secondary": {
            "base": "rgb(138, 186, 169)",   # Vert d'eau
            "light": "rgb(195, 220, 210)",  # Vert très clair
            "dark": "rgb(88, 136, 119)"     # Vert foncé
        }
    },
    "image_generation_prompt": "Luxury spa and thalassotherapy imagery with calming ocean blues, turquoise waters, soft lighting. Serene atmosphere, modern elegance, coastal wellness themes."
}

print(f"   Preset : {preset_thalasso['name']}")
print(f"   Mood : {preset_thalasso['mood']}")
print(f"   Couleur primaire : {preset_thalasso['color_system']['primary']['base']}")

# Générer assets visuels
print("\n🎨 Étape 2 : Génération guidelines visuels")
generator = VisualAssetsGenerator()
assets = generator.generate_assets(preset_thalasso)

print(f"   Icon style : {assets['icon_guidelines']['style']}")
print(f"   Icon library : {assets['icon_guidelines']['library']}")
print(f"   Decorative : radius={assets['decorative_elements']['border_radius']}, shadow={assets['decorative_elements']['shadow_style']}")

# Afficher prompts
print("\n📝 Étape 3 : Prompts d'illustrations générés")
prompts = assets['illustration_prompts']

for section, prompt in prompts.items():
    print(f"\n   {section.upper()} :")
    print(f"   {prompt[:120]}...")

# Générer images avec DALL-E 3 via MODEL_EXECUTOR
print("\n🤖 Étape 4 : Génération images DALL-E 3")

if True:
    output_dir = Path("output_thalasso")
    output_dir.mkdir(exist_ok=True)

    # Générer 4 images (hero, features, cta, og_image) via MODEL_EXECUTOR
    sections = ["hero", "features", "cta", "og_image"]
    generated_images = {}

    for i, section in enumerate(sections, 1):
        print(f"\n   [{i}/4] Génération image {section}...")

        prompt = prompts[section]
        is_wide = section in ["hero", "cta"]

        try:
            resp = model_execute(
                "text2img",
                prompt,
                data={
                    "width":   1792 if is_wide else 1024,
                    "height":  1024,
                    "quality": "standard",
                    "n":       1,
                },
                provider="openai",
            )

            image_url = resp["result"]
            generated_images[section] = {
                "url":    image_url,
                "prompt": prompt,
                "size":   "1792x1024" if is_wide else "1024x1024"
            }

            print(f"       ✅ {section} généré")
            print(f"       URL : {str(image_url)[:60]}...")

        except Exception as e:
            print(f"       ❌ Erreur : {e}")
            generated_images[section] = {
                "error": str(e),
                "prompt": prompt
            }

    # Sauvegarder tout
    with open(output_dir / "preset_thalasso.json", 'w') as f:
        json.dump(preset_thalasso, f, indent=2)

    with open(output_dir / "visual_assets.json", 'w') as f:
        json.dump(assets, f, indent=2)

    with open(output_dir / "generated_images.json", 'w') as f:
        json.dump(generated_images, f, indent=2)

    print(f"\n   💾 Tout sauvegardé : {output_dir}")

    # Générer page HTML avec images
    print("\n🏗️ Étape 5 : Génération page démo avec vraies images")

    hero_img = generated_images.get('hero', {}).get('url', '')
    features_img = generated_images.get('features', {}).get('url', '')
    cta_img = generated_images.get('cta', {}).get('url', '')

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{preset_thalasso['name']} — Images IA Générées</title>
    <link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.0.3/src/regular/style.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --color-primary: {preset_thalasso['color_system']['primary']['base']};
            --color-primary-light: {preset_thalasso['color_system']['primary']['light']};
            --color-primary-dark: {preset_thalasso['color_system']['primary']['dark']};
            --color-secondary: {preset_thalasso['color_system']['secondary']['base']};

            --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            --spacing-2xl: 48px;
            --spacing-3xl: 64px;

            --shadow-md: 0 4px 6px rgba(44, 98, 120, 0.1);
            --shadow-lg: 0 10px 20px rgba(44, 98, 120, 0.15);

            --radius-md: 8px;
            --radius-lg: 12px;
        }}

        body {{
            font-family: var(--font-family);
            color: #2d3748;
            background: #f8fafb;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 var(--spacing-lg);
        }}

        header {{
            padding: var(--spacing-lg) 0;
            background: white;
            border-bottom: 1px solid rgba(72, 149, 178, 0.1);
        }}

        nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            font-size: 24px;
            font-weight: 700;
            color: var(--color-primary-dark);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .hero {{
            position: relative;
            height: 600px;
            background-image: url('{hero_img}');
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
        }}

        .hero::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(44, 98, 120, 0.7) 0%, rgba(72, 149, 178, 0.5) 100%);
        }}

        .hero-content {{
            position: relative;
            z-index: 1;
            max-width: 700px;
        }}

        .hero h1 {{
            font-size: 56px;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: var(--spacing-lg);
        }}

        .hero p {{
            font-size: 20px;
            line-height: 1.6;
            margin-bottom: var(--spacing-xl);
            opacity: 0.95;
        }}

        .btn-primary {{
            background: white;
            color: var(--color-primary-dark);
            padding: 16px 48px;
            border-radius: var(--radius-md);
            border: none;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
        }}

        .features {{
            padding: var(--spacing-3xl) 0;
        }}

        .section-header {{
            text-align: center;
            margin-bottom: var(--spacing-3xl);
        }}

        .section-badge {{
            display: inline-block;
            background: rgba(72, 149, 178, 0.1);
            color: var(--color-primary-dark);
            padding: 4px 16px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
        }}

        .section-header h2 {{
            font-size: 40px;
            font-weight: 700;
            margin-bottom: 16px;
            color: var(--color-primary-dark);
        }}

        .features-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--spacing-xl);
        }}

        .feature-card {{
            background: white;
            padding: var(--spacing-xl);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            text-align: center;
        }}

        .feature-image {{
            width: 100%;
            height: 200px;
            background-image: url('{features_img}');
            background-size: cover;
            background-position: center;
            border-radius: var(--radius-md);
            margin-bottom: var(--spacing-lg);
        }}

        .feature-icon {{
            width: 56px;
            height: 56px;
            margin: 0 auto var(--spacing-md);
            background: linear-gradient(135deg, rgba(72, 149, 178, 0.1), rgba(138, 186, 169, 0.1));
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--color-primary);
            font-size: 28px;
        }}

        .feature-card h3 {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--color-primary-dark);
        }}

        .cta {{
            position: relative;
            height: 400px;
            background-image: url('{cta_img}');
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
        }}

        .cta::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(72, 149, 178, 0.85) 0%, rgba(138, 186, 169, 0.75) 100%);
        }}

        .cta-content {{
            position: relative;
            z-index: 1;
            max-width: 600px;
        }}

        .cta h2 {{
            font-size: 40px;
            font-weight: 700;
            margin-bottom: 16px;
        }}

        .prompts-section {{
            padding: var(--spacing-3xl) 0;
            background: white;
        }}

        .prompt-card {{
            background: #f8fafb;
            padding: var(--spacing-lg);
            border-radius: var(--radius-md);
            margin-bottom: var(--spacing-lg);
            border-left: 4px solid var(--color-primary);
        }}

        .prompt-card h3 {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--color-primary-dark);
        }}

        .prompt-card pre {{
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 14px;
            line-height: 1.6;
            color: #4a5568;
        }}

        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 36px; }}
            .features-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav>
                <div class="logo">
                    <i class="ph ph-waves"></i>
                    {preset_thalasso['name']}
                </div>
            </nav>
        </div>
    </header>

    <section class="hero">
        <div class="hero-content">
            <h1>L'océan comme thérapie</h1>
            <p>Découvrez les bienfaits de la thalassothérapie dans un cadre d'exception face à la mer</p>
            <button class="btn-primary">Réserver un séjour</button>
        </div>
    </section>

    <section class="features">
        <div class="container">
            <div class="section-header">
                <span class="section-badge">Nos soins</span>
                <h2>Une expérience complète de bien-être</h2>
            </div>

            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="ph ph-waves"></i>
                    </div>
                    <h3>Hydrothérapie marine</h3>
                    <p>Bains d'eau de mer chauffée, jets sous-marins, parcours aquatiques tonifiants</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="ph ph-spa"></i>
                    </div>
                    <h3>Soins du corps</h3>
                    <p>Enveloppements d'algues, gommages marins, massages aux huiles essentielles</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="ph ph-heart"></i>
                    </div>
                    <h3>Relaxation</h3>
                    <p>Espace détente, sauna, hammam, salle de repos avec vue océan</p>
                </div>
            </div>
        </div>
    </section>

    <section class="cta">
        <div class="cta-content">
            <h2>Offrez-vous une pause bien-être</h2>
            <p>Forfaits séjours de 3 à 7 jours — Tarifs à partir de 590€</p>
            <button class="btn-primary">Découvrir nos offres</button>
        </div>
    </section>

    <section class="prompts-section">
        <div class="container">
            <div class="section-header">
                <span class="section-badge">Technique</span>
                <h2>Prompts DALL-E 3 utilisés</h2>
                <p>Générés automatiquement par visual_assets_generator</p>
            </div>

            <div class="prompt-card">
                <h3>🖼️ Hero Section</h3>
                <pre>{prompts['hero']}</pre>
            </div>

            <div class="prompt-card">
                <h3>🎨 Features Section</h3>
                <pre>{prompts['features']}</pre>
            </div>

            <div class="prompt-card">
                <h3>📢 CTA Section</h3>
                <pre>{prompts['cta']}</pre>
            </div>

            <div class="prompt-card">
                <h3>📱 OG Image (social)</h3>
                <pre>{prompts['og_image']}</pre>
            </div>
        </div>
    </section>

</body>
</html>"""

    demo_path = output_dir / "demo_thalasso_images.html"
    demo_path.write_text(html)

    print(f"   ✅ Page démo : {demo_path}")

    # Ouvrir
    import subprocess
    subprocess.run(['open', str(demo_path)])

    print("\n" + "="*70)
    print("  ✅ IMAGES GÉNÉRÉES — Page ouverte avec vraies images DALL-E 3")
    print("="*70)
    print(f"\n💡 Coût : ~$0.16 (4 images DALL-E 3 standard)")
    print(f"📁 Fichiers : {output_dir}")
