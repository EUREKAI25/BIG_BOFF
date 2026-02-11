"""
IMAGE GENERATOR FLUX — Génération images depuis scénario v8
Utilise FLUX General avec IP-Adapter pour cohérence faciale
"""

import json
import os
import sys
import time
import base64
import urllib.request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from prompt_generator import generate_prompt, validate_prompt_rules

# Charger .env
load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

PRICING_FLUX = 0.05  # USD per image (estimation)
ENDPOINT = "https://queue.fal.run/fal-ai/flux-general"

# =============================================================================
# IMAGE GENERATOR FLUX
# =============================================================================

class ImageGeneratorFlux:
    def __init__(self, scenario_path: str, output_dir: str = "generated_images", reference_images: list = None):
        self.scenario_path = scenario_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Support multi-photos référence (prendre la première pour IP-Adapter)
        if reference_images:
            if isinstance(reference_images, str):
                ref_path = Path(reference_images)
                if ref_path.is_dir():
                    all_images = sorted([str(p) for p in ref_path.glob("*.png")])
                    self.reference_image = all_images[0] if all_images else None
                    print(f"📸 Utilisation de: {Path(self.reference_image).name}")
                else:
                    self.reference_image = reference_images
            else:
                self.reference_image = reference_images[0]
        else:
            self.reference_image = None

        # Charger scénario
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

        # Stats
        self.images_generated = 0
        self.total_cost = 0.0
        self.start_time = time.time()

        # Fal.ai API
        self.fal_key = os.getenv("FAL_KEY")
        if not self.fal_key:
            raise ValueError("FAL_KEY manquant dans .env")

    def _build_positive_prompt(self, scene_id: int, keyframe_type: str) -> str:
        """Construit le prompt positif pour une image en utilisant le générateur de prompt."""

        # Récupérer données de la scène
        params = None
        keyframe = None
        palette = None
        cadrage = None

        for p in self.scenario.get("parametres_scenes", []):
            if p.get("scene_id") == scene_id:
                params = p
                break

        for k in self.scenario.get("keyframes", []):
            if k.get("scene_id") == scene_id:
                keyframe = k
                break

        for pal in self.scenario.get("palettes_scenes", []):
            if pal.get("scene_id") == scene_id:
                palette = pal
                break

        for cad in self.scenario.get("cadrages", []):
            if cad.get("scene_id") == scene_id:
                cadrage = cad
                break

        if not all([params, keyframe, palette, cadrage]):
            raise ValueError(f"Données incomplètes pour scène {scene_id}")

        # Sélectionner keyframe start ou end
        kf_data = keyframe.get("start") if keyframe_type == "start" else keyframe.get("end")

        # Récupérer imaginaire collectif
        imaginaire = self.scenario.get('imaginaire_collectif', {})

        # Récupérer le genre depuis les métadonnées
        user_profile = self.scenario.get('metadata', {}).get('user_profile', {})
        gender = user_profile.get('gender', 'person')

        # Récupérer palette globale
        palette_globale = self.scenario.get('palette_globale', {})

        # GÉNÉRER LE PROMPT avec le générateur narratif
        prompt = generate_prompt(
            scene_id=scene_id,
            params=params,
            kf_data=kf_data,
            palette=palette,
            cadrage=cadrage,
            imaginaire=imaginaire,
            gender=gender,
            palette_globale=palette_globale,
            keyframe_type=keyframe_type
        )

        # Valider que le prompt respecte les règles
        validation = validate_prompt_rules(prompt)
        if not validation['valid']:
            print(f"   ⚠️  Prompt validation score: {validation['score']}/100")
            failed = [k for k, v in validation['criteria'].items() if not v['passed']]
            print(f"   ⚠️  Failed criteria: {', '.join(failed)}")

        return prompt

    def generate_image(self, scene_id: int, keyframe_type: str) -> dict:
        """Génère une image via FLUX General avec IP-Adapter."""

        print(f"\n🎨 Génération image scène {scene_id} ({keyframe_type})...")

        positive_prompt = self._build_positive_prompt(scene_id, keyframe_type)

        print(f"   Prompt: {positive_prompt[:100]}...")

        try:
            # Encoder l'image de référence en base64 si fournie
            ip_adapter_image_url = None
            if self.reference_image:
                print(f"   📸 Chargement référence: {Path(self.reference_image).name}")

                with open(self.reference_image, "rb") as img_file:
                    img_bytes = img_file.read()
                    image_b64 = base64.b64encode(img_bytes).decode('utf-8')
                    ip_adapter_image_url = f"data:image/png;base64,{image_b64}"
                    print(f"   📸 Référence encodée: {len(img_bytes)} bytes")

            # Préparer input pour FLUX General avec IP-Adapter
            payload = {
                "prompt": positive_prompt,
                "image_size": {
                    "width": 1024,
                    "height": 768
                },
                "num_inference_steps": 28,
                "num_images": 1,
                "enable_safety_checker": False
            }

            # Ajouter IP-Adapter si image fournie
            if ip_adapter_image_url:
                payload["ip_adapter"] = {
                    "image_url": ip_adapter_image_url,
                    "scale": 0.8  # Force de l'influence (0-1)
                }
                print(f"   🎯 IP-Adapter activé (scale: 0.8)")

            # Appel Fal.ai FLUX General
            req = urllib.request.Request(
                ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Key {self.fal_key}",
                    "Content-Type": "application/json"
                }
            )

            print(f"   🚀 Appel Fal.ai FLUX General...")

            # Soumettre la requête
            with urllib.request.urlopen(req, timeout=30) as response:
                queue_result = json.loads(response.read().decode("utf-8"))

            # Récupérer URLs de statut
            status_url = queue_result.get("status_url")
            response_url = queue_result.get("response_url")

            if not status_url or not response_url:
                raise ValueError(f"Réponse queue invalide: {queue_result}")

            # Polling jusqu'à completion
            print(f"   ⏳ En attente de génération...")
            max_wait = 120
            poll_interval = 2
            elapsed = 0

            while elapsed < max_wait:
                status_req = urllib.request.Request(
                    status_url,
                    headers={"Authorization": f"Key {self.fal_key}"}
                )

                with urllib.request.urlopen(status_req, timeout=10) as status_resp:
                    status_data = json.loads(status_resp.read().decode("utf-8"))

                status = status_data.get("status")

                if status == "COMPLETED":
                    # Récupérer le résultat final
                    result_req = urllib.request.Request(
                        response_url,
                        headers={"Authorization": f"Key {self.fal_key}"}
                    )

                    with urllib.request.urlopen(result_req, timeout=10) as result_resp:
                        result = json.loads(result_resp.read().decode("utf-8"))

                    images = result.get("images", [])
                    if not images:
                        raise ValueError(f"Pas d'images dans résultat: {result}")

                    image_url = images[0].get("url")
                    if not image_url:
                        raise ValueError(f"Pas d'URL d'image: {result}")
                    break

                elif status == "FAILED":
                    error = status_data.get("error", "Unknown error")
                    raise ValueError(f"Génération échouée: {error}")

                time.sleep(poll_interval)
                elapsed += poll_interval

            else:
                raise TimeoutError(f"Timeout après {max_wait}s")

            # Télécharger et sauvegarder
            filename = f"scene_{scene_id:02d}_{keyframe_type}.png"
            filepath = self.output_dir / filename

            urllib.request.urlretrieve(image_url, filepath)

            self.images_generated += 1
            self.total_cost += PRICING_FLUX

            print(f"   ✅ Sauvegardé : {filepath}")

            return {
                "scene_id": scene_id,
                "keyframe_type": keyframe_type,
                "url": image_url,
                "filepath": str(filepath),
                "cost_usd": PRICING_FLUX
            }

        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            raise

    def generate_scenes(self, scene_ids: list, keyframes: str = "start", validate: bool = False) -> list:
        """Génère des scènes spécifiques."""

        print(f"\n🎬 GÉNÉRATION IMAGES — FLUX General + IP-Adapter")
        print(f"   Scénario: {self.scenario_path}")
        print(f"   Scènes: {scene_ids}")
        print(f"   Keyframes: {keyframes}")
        if self.reference_image:
            print(f"   📸 Image de référence: {Path(self.reference_image).name}")
        print(f"   Output: {self.output_dir}/")

        results = []

        for scene_id in scene_ids:
            try:
                result = self.generate_image(scene_id, "start")
                results.append(result)
            except Exception as e:
                print(f"\n   ⚠️  Scène {scene_id} ignorée : {e}")
                continue

        # Résumé final
        duration = time.time() - self.start_time

        print(f"\n{'='*70}")
        print(f"  ✅ GÉNÉRATION TERMINÉE")
        print(f"{'='*70}")
        print(f"   Images générées: {self.images_generated}")
        if self.images_generated > 0:
            print(f"   Durée totale: {duration:.0f}s ({duration/self.images_generated:.0f}s/image)")
            print(f"   Coût total: ${self.total_cost:.2f}")
            print(f"   Coût/image: ${self.total_cost/self.images_generated:.2f}")
        print(f"{'='*70}")

        return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Génération images FLUX depuis scénario v8")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("--scenes", nargs="+", type=int, required=True,
                        help="IDs de scènes à générer (ex: 4 5)")
    parser.add_argument("--output", default="generated_images_flux",
                        help="Dossier de sortie (défaut: generated_images_flux)")
    parser.add_argument("--reference-images", help="Image(s) de référence : fichier unique ou dossier")

    args = parser.parse_args()

    if not Path(args.scenario).exists():
        print(f"❌ Fichier introuvable : {args.scenario}")
        sys.exit(1)

    if args.reference_images and not Path(args.reference_images).exists():
        print(f"❌ Images de référence introuvables : {args.reference_images}")
        sys.exit(1)

    generator = ImageGeneratorFlux(args.scenario, args.output, args.reference_images)
    generator.generate_scenes(args.scenes)


if __name__ == "__main__":
    main()
