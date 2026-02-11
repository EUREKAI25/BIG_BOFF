"""
IMAGE GENERATOR — Génération images depuis scénario v8
Utilise Flux Kontext Pro via Fal.ai pour cohérence maximale
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

# Charger .env
load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

NEGATIVE_PROMPT_BASE = """
gros plan visage, très gros plan, close-up face, facial close-up,
texte lisible, text, writing, letters, words,
reflets complexes, miroirs, complex reflections, mirrors,
air triste, sad face, inquiet, worried, effrayé, scared, en colère, angry,
artefacts, glitches, distortions, blurry, flou,
mouvements rapides, fast motion, mouvement flou, motion blur,
foule dense, crowd, many people,
rotation caméra rapide, camera spin,
demi-tour, back turned completely, dos prolongé,
mauvaise qualité, low quality, amateur
""".strip()

PRICING_FLUX_KONTEXT = 0.04  # USD per image (Fal.ai)

# =============================================================================
# IMAGE GENERATOR
# =============================================================================

class ImageGenerator:
    def __init__(self, scenario_path: str, output_dir: str = "generated_images", reference_images: list = None):
        self.scenario_path = scenario_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Support multi-photos référence (jusqu'à 5)
        if reference_images:
            if isinstance(reference_images, str):
                # Si c'est un dossier, charger toutes les images
                ref_path = Path(reference_images)
                if ref_path.is_dir():
                    self.reference_images = sorted([str(p) for p in ref_path.glob("*.png")])[:5]
                else:
                    self.reference_images = [reference_images]
            else:
                self.reference_images = reference_images[:5]  # Max 5
        else:
            self.reference_images = None

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
        """Construit le prompt positif pour une image."""

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

        # Construire prompt détaillé
        # Si image de référence : ne pas décrire le protagoniste physiquement, juste la tenue
        if self.reference_images:
            protagonist_desc = f"This person is wearing {params['tenue_protagoniste']}"
        else:
            protagonist_desc = params['tenue_protagoniste']

        # Construire section partenaire si présent
        partner_section = ""
        if params.get('tenue_partenaire', 'Aucun') not in ['Aucun', 'N/A', 'None']:
            partner_section = f"""
- Second character: {params['tenue_partenaire']}
  Position: {kf_data.get('position_partenaire', 'nearby')}
  (background character, slightly blurred)"""

        # Récupérer imaginaire collectif si présent
        # IMPORTANT: Scène 1 = préparatifs (pas encore dans le lieu du rêve)
        # On applique l'imaginaire seulement aux scènes 2+
        imaginaire = self.scenario.get('imaginaire_collectif', {})
        if scene_id == 1:
            # Scène 1 = préparatifs, pas d'imaginaire paradisiaque
            imaginaire_desc = ''
            atmosphere = ''
        else:
            # Scènes 2+ = dans le lieu du rêve, appliquer l'imaginaire
            imaginaire_desc = imaginaire.get('imaginaire', '')
            atmosphere = imaginaire.get('atmosphere', '')

        prompt = f"""
Photo-realistic image, cinematic quality, professional photography.
NO TEXT, NO WORDS, NO LETTERS, NO WRITING, NO SIGNS, NO LABELS.

Location: {params['lieu_precis']}
Time of day: {params['moment']}
Atmosphere: {atmosphere}

Visual context: {imaginaire_desc}

Main character: {protagonist_desc}
Position: {kf_data['position_protagoniste']}
Emotion: {kf_data['emotion']}
Gesture: {kf_data['geste']}{partner_section}

Interaction: {kf_data['interaction']}

Shot type: {cadrage['type_plan']}
Camera angle: {cadrage['angle']}

Color palette: dominant {palette['dominante']}, accent {palette['accent']}
Lighting: {palette['lumiere']}, saturation {palette['saturation']}

Style: cinematic, dreamy mood, professional composition, depth of field, bokeh background,
postcard perfect, iconic representation, paradise atmosphere
""".strip()

        return prompt

    def _build_negative_prompt(self) -> str:
        """Construit le prompt négatif."""
        return NEGATIVE_PROMPT_BASE

    def generate_image(self, scene_id: int, keyframe_type: str) -> dict:
        """Génère une image via Flux Kontext Pro."""

        print(f"\n🎨 Génération image scène {scene_id} ({keyframe_type})...")

        positive_prompt = self._build_positive_prompt(scene_id, keyframe_type)
        negative_prompt = self._build_negative_prompt()

        print(f"   Prompt: {positive_prompt[:100]}...")

        try:
            # Encoder 1ère image de référence en base64 si fournie
            # Note : Flux Kontext ne supporte qu'UNE image de référence
            image_url_data = None
            if self.reference_images:
                # Utiliser la 1ère image (la plus représentative)
                ref_img = self.reference_images[0]
                with open(ref_img, "rb") as img_file:
                    image_b64 = base64.b64encode(img_file.read()).decode('utf-8')
                    image_url_data = f"data:image/png;base64,{image_b64}"
                print(f"   📸 Image de référence: {Path(ref_img).name}")

            # Préparer input pour Flux Kontext via Fal.ai
            payload = {
                "prompt": positive_prompt,
                "guidance_scale": 3.5,
                "num_images": 1,
                "output_format": "png",
                "safety_tolerance": "2",
                "aspect_ratio": "4:3",
                "sync_mode": True  # Mode synchrone pour simplicité
            }

            # Ajouter image de référence
            if image_url_data:
                payload["image_url"] = image_url_data

            # Appel Fal.ai Flux Kontext Pro
            req = urllib.request.Request(
                "https://queue.fal.run/fal-ai/flux-pro/kontext",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Key {self.fal_key}",
                    "Content-Type": "application/json"
                }
            )

            # Soumettre la requête (retourne request_id)
            with urllib.request.urlopen(req, timeout=30) as response:
                queue_result = json.loads(response.read().decode("utf-8"))

            # Récupérer status_url et response_url
            status_url = queue_result.get("status_url")
            response_url = queue_result.get("response_url")

            if not status_url or not response_url:
                raise ValueError(f"Réponse queue invalide: {queue_result}")

            # Polling jusqu'à completion (max 2 minutes)
            print(f"   ⏳ En attente de génération...")
            max_wait = 120  # secondes
            poll_interval = 2  # secondes
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

                    image_url = result.get("images", [{}])[0].get("url")
                    if not image_url:
                        raise ValueError(f"Pas d'URL d'image: {result}")
                    break

                elif status == "FAILED":
                    error = status_data.get("error", "Unknown error")
                    raise ValueError(f"Génération échouée: {error}")

                # Attendre avant prochain poll
                time.sleep(poll_interval)
                elapsed += poll_interval

            else:
                raise TimeoutError(f"Timeout après {max_wait}s")

            # Télécharger et sauvegarder
            filename = f"scene_{scene_id:02d}_{keyframe_type}.png"
            filepath = self.output_dir / filename

            urllib.request.urlretrieve(image_url, filepath)

            self.images_generated += 1
            self.total_cost += PRICING_FLUX_KONTEXT

            print(f"   ✅ Sauvegardé : {filepath}")

            return {
                "scene_id": scene_id,
                "keyframe_type": keyframe_type,
                "url": image_url,
                "filepath": str(filepath),
                "cost_usd": PRICING_FLUX_KONTEXT
            }

        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            raise

    def generate_with_validation(self, scene_id: int, keyframe_type: str, max_attempts: int = 3) -> dict:
        """
        Génère une image avec validation automatique.
        Régénère jusqu'à max_attempts si score ressemblance < 0.8.

        Returns:
            dict avec image validée
        """
        from validation_images import ImageValidator

        validator = ImageValidator(
            reference_image=self.reference_images[0] if self.reference_images else None
        )

        for attempt in range(1, max_attempts + 1):
            print(f"\n🎨 Génération image scène {scene_id} ({keyframe_type}) - Tentative {attempt}/{max_attempts}")

            # Générer image
            result = self.generate_image(scene_id, keyframe_type)

            # Valider
            validation = validator.validate_image(result['filepath'])

            # Afficher scores
            quality_score = validation['quality']['score']
            resemblance_score = validation['resemblance']['score']

            print(f"   📊 Qualité: {quality_score:.2f} {'✅' if quality_score >= 0.7 else '❌'}")
            print(f"   📊 Ressemblance: {resemblance_score:.2f} {'✅' if resemblance_score >= 0.8 else '❌'}")

            # Si validée, retourner
            if validation['overall_passed']:
                print(f"   ✅ Image validée !")
                result['validation'] = validation
                return result

            # Si échec et pas dernière tentative
            if attempt < max_attempts:
                print(f"   🔄 Scores insuffisants, nouvelle tentative...")
                # Supprimer l'image rejetée
                Path(result['filepath']).unlink(missing_ok=True)

        # Si toutes les tentatives échouent
        print(f"   ⚠️  Échec validation après {max_attempts} tentatives, image conservée quand même")
        result['validation'] = validation
        return result

    def generate_all(self, keyframes: str = "start", validate: bool = True, max_attempts: int = 3) -> list:
        """
        Génère toutes les images.

        Args:
            keyframes: "start", "end", ou "both"

        Returns:
            Liste des images générées
        """

        print(f"\n🎬 GÉNÉRATION IMAGES — Flux Kontext Pro")
        print(f"   Scénario: {self.scenario_path}")
        print(f"   Keyframes: {keyframes}")
        if self.reference_images:
            print(f"   📸 {len(self.reference_images)} images de référence")
        print(f"   Output: {self.output_dir}/")

        scenes = self.scenario.get("decoupage", [])
        nb_scenes = len(scenes)

        if keyframes == "both":
            total_images = nb_scenes * 2
        else:
            total_images = nb_scenes

        print(f"   Images à générer: {total_images}")
        print(f"   Validation: {'✅ Activée' if validate else '❌ Désactivée'}")
        print(f"   Coût estimé: ${total_images * PRICING_FLUX_KONTEXT:.2f}\n")

        results = []

        for scene in scenes:
            scene_id = scene["id"]

            # Générer start keyframe
            if keyframes in ["start", "both"]:
                if validate:
                    result = self.generate_with_validation(scene_id, "start", max_attempts)
                else:
                    result = self.generate_image(scene_id, "start")
                results.append(result)

            # Générer end keyframe
            if keyframes in ["end", "both"]:
                if validate:
                    result = self.generate_with_validation(scene_id, "end", max_attempts)
                else:
                    result = self.generate_image(scene_id, "end")
                results.append(result)

        # Sauvegarder métadonnées
        duration = time.time() - self.start_time

        metadata = {
            "scenario": self.scenario_path,
            "generated_at": datetime.now().isoformat(),
            "keyframes": keyframes,
            "images_generated": self.images_generated,
            "total_cost_usd": round(self.total_cost, 2),
            "duration_seconds": round(duration, 2),
            "images": results
        }

        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*70}")
        print(f"  ✅ GÉNÉRATION TERMINÉE")
        print(f"{'='*70}")
        print(f"   Images générées: {self.images_generated}")
        print(f"   Images validées: {sum(1 for r in results if r.get('validation', {}).get('overall_passed', True))}/{self.images_generated}")
        print(f"   Durée totale: {duration:.0f}s ({duration/self.images_generated:.0f}s/image)")
        print(f"   Coût total: ${self.total_cost:.2f}")
        print(f"   Coût/image: ${self.total_cost/self.images_generated:.2f}")
        print(f"   Métadonnées: {metadata_path}")
        print(f"{'='*70}")

        return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Génération images depuis scénario v8")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("--keyframes", choices=["start", "end", "both"], default="start",
                        help="Quels keyframes générer (défaut: start)")
    parser.add_argument("--output", default="generated_images",
                        help="Dossier de sortie (défaut: generated_images)")
    parser.add_argument("--reference-images", help="Image(s) de référence : fichier unique ou dossier (max 5)")
    parser.add_argument("--validate", action="store_true", default=True,
                        help="Activer validation automatique avec régénération (défaut: True)")
    parser.add_argument("--no-validate", dest="validate", action="store_false",
                        help="Désactiver validation automatique")
    parser.add_argument("--max-attempts", type=int, default=3,
                        help="Nombre max de tentatives par image si validation échoue (défaut: 3)")

    args = parser.parse_args()

    # Vérifier que le scénario existe
    if not Path(args.scenario).exists():
        print(f"❌ Fichier introuvable : {args.scenario}")
        sys.exit(1)

    # Vérifier que les images de référence existent si fournies
    if args.reference_images and not Path(args.reference_images).exists():
        print(f"❌ Images de référence introuvables : {args.reference_images}")
        sys.exit(1)

    # Générer
    generator = ImageGenerator(args.scenario, args.output, args.reference_images)
    generator.generate_all(args.keyframes, validate=args.validate, max_attempts=args.max_attempts)


if __name__ == "__main__":
    main()
