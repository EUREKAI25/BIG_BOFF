"""
Génération d'images IA pour Thalasso avec Replicate (Flux) via MODEL_EXECUTOR
Nouvelle organisation de page moderne
"""
import json
import os
import time
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
print("  GÉNÉRATION IMAGES REPLICATE — THALASSO")
print("="*70)

# Preset thalasso
preset_thalasso = {
    "name": "Thalasso & Spa",
    "mood": "cool",
    "use_case": "wellness",
    "color_system": {
        "primary": {
            "base": "rgb(72, 149, 178)",
            "light": "rgb(157, 201, 219)",
            "dark": "rgb(44, 98, 120)"
        },
        "secondary": {
            "base": "rgb(138, 186, 169)",
            "light": "rgb(195, 220, 210)",
            "dark": "rgb(88, 136, 119)"
        }
    },
    "image_generation_prompt": "Luxury spa and thalassotherapy imagery with calming ocean blues, turquoise waters, soft lighting. Serene atmosphere, modern elegance, coastal wellness themes."
}

print(f"\n🌊 Preset : {preset_thalasso['name']}")

# Générer prompts
generator = VisualAssetsGenerator()
assets = generator.generate_assets(preset_thalasso)
prompts = assets['illustration_prompts']

print(f"\n🎨 Prompts générés pour {len(prompts)} sections")

# Générer images avec Replicate Flux
print(f"\n🤖 Génération images Flux (Replicate)...")

output_dir = Path("output_thalasso")
output_dir.mkdir(exist_ok=True)

# Utiliser Flux Schnell (ultra rapide, gratuit)
model = "black-forest-labs/flux-schnell"

generated_images = {}

sections = {
    "hero": "Luxury spa thalassotherapy, calming ocean blues, turquoise waters, soft natural lighting, serene coastal atmosphere, modern elegant wellness center, photorealistic, wide cinematic shot",
    "features": "Spa wellness abstract illustration, clean modern isometric design, ocean blue palette, minimalist icons, simple geometric shapes, flat design style, soft gradients",
    "cta": "Luxury spa thalasso background, soft ocean blues, turquoise water patterns, subtle elegant texture, calm serene atmosphere, perfect for overlay text, wide format",
    "service1": "Spa hydrotherapy pool, turquoise water, modern minimalist design, soft natural light, serene atmosphere, photorealistic",
    "service2": "Spa massage room, ocean view, soft blue tones, elegant minimal interior, natural lighting, peaceful ambiance",
    "service3": "Spa relaxation lounge, coastal design, turquoise accents, modern comfortable furniture, calming atmosphere"
}

for i, (section, prompt) in enumerate(sections.items(), 1):
    print(f"\n   [{i}/{len(sections)}] {section}...")

    try:
        resp = model_execute(
            "text2img",
            prompt,
            data={
                "model_id":             model,
                "num_inference_steps":  4,   # Schnell = ultra rapide
                "guidance_scale":       0,   # Schnell n'utilise pas guidance
                "num_outputs":          1,
                "aspect_ratio":         "16:9" if section in ["hero", "cta"] else "1:1",
            },
            provider="replicate",
        )

        image_url = resp["result"]

        generated_images[section] = {
            "url":    str(image_url),
            "prompt": prompt
        }

        print(f"       ✅ {image_url}")

    except Exception as e:
        print(f"       ❌ Erreur : {e}")
        generated_images[section] = {"error": str(e)}

# Sauvegarder
with open(output_dir / "generated_images_replicate.json", 'w') as f:
    json.dump(generated_images, f, indent=2)

print(f"\n💾 Images sauvegardées : {output_dir}")

# Générer page HTML moderne (bento grid layout)
print(f"\n🏗️ Génération page moderne (bento grid)...")

hero_img = generated_images.get('hero', {}).get('url', '')
features_img = generated_images.get('features', {}).get('url', '')
cta_img = generated_images.get('cta', {}).get('url', '')
service1_img = generated_images.get('service1', {}).get('url', '')
service2_img = generated_images.get('service2', {}).get('url', '')
service3_img = generated_images.get('service3', {}).get('url', '')

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thalasso & Spa — Bien-être Marine</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --color-primary: rgb(72, 149, 178);
            --color-primary-light: rgb(157, 201, 219);
            --color-primary-dark: rgb(44, 98, 120);
            --color-secondary: rgb(138, 186, 169);
            --color-text: #1e293b;
            --color-text-light: #64748b;
            --spacing: clamp(1rem, 3vw, 2rem);
            --radius: 16px;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: var(--color-text);
            background: linear-gradient(to bottom, #f0f9ff 0%, #ffffff 100%);
            line-height: 1.6;
        }}

        /* HERO FULL SCREEN */
        .hero {{
            height: 100vh;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: white;
            overflow: hidden;
        }}

        .hero-bg {{
            position: absolute;
            inset: 0;
            background: url('{hero_img}') center/cover;
            filter: brightness(0.8);
        }}

        .hero-overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(44, 98, 120, 0.7) 0%, rgba(72, 149, 178, 0.4) 100%);
        }}

        .hero-content {{
            position: relative;
            z-index: 1;
            max-width: 900px;
            padding: var(--spacing);
        }}

        .hero h1 {{
            font-size: clamp(3rem, 8vw, 6rem);
            font-weight: 700;
            line-height: 1;
            margin-bottom: 1rem;
            letter-spacing: -0.02em;
        }}

        .hero p {{
            font-size: clamp(1.25rem, 3vw, 1.75rem);
            opacity: 0.95;
            margin-bottom: 2rem;
        }}

        .btn {{
            background: white;
            color: var(--color-primary-dark);
            padding: 1.25rem 3rem;
            border: none;
            border-radius: 8px;
            font-size: 1.125rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}

        .btn:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}

        /* BENTO GRID SECTION */
        .bento-section {{
            max-width: 1400px;
            margin: -80px auto 0;
            padding: 0 var(--spacing);
            position: relative;
            z-index: 10;
        }}

        .bento-grid {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            grid-template-rows: repeat(4, 200px);
            gap: 1.5rem;
        }}

        .bento-card {{
            background: white;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            position: relative;
        }}

        .bento-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }}

        .card-large {{
            grid-column: span 3;
            grid-row: span 2;
        }}

        .card-tall {{
            grid-column: span 2;
            grid-row: span 3;
        }}

        .card-wide {{
            grid-column: span 4;
            grid-row: span 2;
        }}

        .card-small {{
            grid-column: span 2;
            grid-row: span 2;
        }}

        .card-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .card-content {{
            position: absolute;
            inset: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, transparent 60%);
            color: white;
        }}

        .card-content h3 {{
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        .card-content p {{
            font-size: 1rem;
            opacity: 0.95;
        }}

        /* STATS OVERLAY */
        .stats-overlay {{
            position: absolute;
            top: 2rem;
            right: 2rem;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}

        .stat {{
            text-align: center;
            margin-bottom: 1rem;
        }}

        .stat:last-child {{
            margin-bottom: 0;
        }}

        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--color-primary);
            line-height: 1;
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: var(--color-text-light);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* CTA FINAL */
        .cta-final {{
            margin: 6rem auto;
            max-width: 1400px;
            padding: 0 var(--spacing);
        }}

        .cta-card {{
            position: relative;
            height: 500px;
            border-radius: var(--radius);
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }}

        .cta-bg {{
            position: absolute;
            inset: 0;
            background: url('{cta_img}') center/cover;
        }}

        .cta-overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(72, 149, 178, 0.9) 0%, rgba(138, 186, 169, 0.85) 100%);
        }}

        .cta-content {{
            position: relative;
            z-index: 1;
            color: white;
            max-width: 700px;
            padding: var(--spacing);
        }}

        .cta-content h2 {{
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 700;
            margin-bottom: 1rem;
        }}

        .cta-content p {{
            font-size: 1.25rem;
            opacity: 0.95;
            margin-bottom: 2rem;
        }}

        .price-tag {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            padding: 0.75rem 2rem;
            border-radius: 999px;
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 2rem;
        }}

        @media (max-width: 1024px) {{
            .bento-grid {{
                grid-template-columns: repeat(2, 1fr);
                grid-template-rows: auto;
            }}

            .card-large,
            .card-tall,
            .card-wide,
            .card-small {{
                grid-column: span 1;
                grid-row: span 1;
                min-height: 250px;
            }}

            .stats-overlay {{
                position: static;
                margin: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <!-- HERO FULL SCREEN -->
    <section class="hero">
        <div class="hero-bg"></div>
        <div class="hero-overlay"></div>
        <div class="hero-content">
            <h1>L'Océan comme Thérapie</h1>
            <p>Thalassothérapie & Spa de luxe face à la mer</p>
            <button class="btn">Découvrir nos soins</button>
        </div>
    </section>

    <!-- BENTO GRID -->
    <section class="bento-section">
        <div class="bento-grid">
            <!-- Card 1 : Hydrothérapie (large) -->
            <div class="bento-card card-large">
                <img src="{service1_img}" alt="Hydrothérapie" class="card-image">
                <div class="card-content">
                    <h3>Hydrothérapie Marine</h3>
                    <p>Bains d'eau de mer chauffée, jets tonifiants, parcours aquatique</p>
                </div>
            </div>

            <!-- Card 2 : Stats (tall) -->
            <div class="bento-card card-tall" style="background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-primary) 100%);">
                <div class="stats-overlay" style="position: static; margin: auto; max-width: 200px;">
                    <div class="stat">
                        <div class="stat-number">15+</div>
                        <div class="stat-label">Années</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">5000+</div>
                        <div class="stat-label">Clients</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">4.9/5</div>
                        <div class="stat-label">Note</div>
                    </div>
                </div>
            </div>

            <!-- Card 3 : Massage (large) -->
            <div class="bento-card card-large">
                <img src="{service2_img}" alt="Massage" class="card-image">
                <div class="card-content">
                    <h3>Soins & Massages</h3>
                    <p>Enveloppements d'algues, gommages marins, huiles essentielles</p>
                </div>
            </div>

            <!-- Card 4 : Abstract (small) -->
            <div class="bento-card card-small">
                <img src="{features_img}" alt="Services" class="card-image">
            </div>

            <!-- Card 5 : Relaxation (wide) -->
            <div class="bento-card card-wide">
                <img src="{service3_img}" alt="Relaxation" class="card-image">
                <div class="card-content">
                    <h3>Espace Détente</h3>
                    <p>Sauna, hammam, salle de repos avec vue panoramique sur l'océan</p>
                </div>
            </div>
        </div>
    </section>

    <!-- CTA FINAL -->
    <section class="cta-final">
        <div class="cta-card">
            <div class="cta-bg"></div>
            <div class="cta-overlay"></div>
            <div class="cta-content">
                <h2>Réservez votre séjour</h2>
                <div class="price-tag">À partir de 590€ / 3 jours</div>
                <p>Forfaits tout compris : hébergement, soins, repas gastronomiques</p>
                <button class="btn">Voir les offres</button>
            </div>
        </div>
    </section>

</body>
</html>"""

demo_path = output_dir / "demo_thalasso_bento.html"
demo_path.write_text(html)

print(f"   ✅ Page générée : {demo_path}")

# Ouvrir
import subprocess
subprocess.run(['open', str(demo_path)])

print("\n" + "="*70)
print("  ✅ IMAGES GÉNÉRÉES — Bento Grid Layout")
print("="*70)
print(f"\n💰 Coût : ~$0 (Flux Schnell est gratuit sur Replicate)")
print(f"📁 Fichiers : {output_dir}")
print(f"\n✨ Layout : Bento grid moderne, hero full-screen, cards interactives")
