"""
IMAGE GENERATOR FLUX KONTEXT — Génération images depuis scénario v8
Utilise FLUX Pro Kontext pour cohérence faciale (10x moins cher que Gemini!)
"""

import json
import os
import sys
import time
import base64
import mimetypes
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

PRICING_FLUX_KONTEXT = 0.04  # USD per image (Flux Pro Kontext)
ENDPOINT = "https://fal.run/fal-ai/flux-pro/kontext"

# =============================================================================
# IMAGE GENERATOR FLUX KONTEXT
# =============================================================================

class ImageGeneratorFluxKontext:
    def __init__(self, scenario_path: str, output_dir: str = "generated_images", reference_images: list = None):
        self.scenario_path = scenario_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Support multi-photos référence (prendre la première pour Flux Kontext)
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

    def _to_data_uri(self, path: str) -> str:
        """Convertit une image en data URI."""
        mime, _ = mimetypes.guess_type(path)
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime or 'image/png'};base64,{data}"

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

        # Adapter le prompt pour Flux Kontext (besoin de "Change the ENTIRE background")
        prompt = f"Change the ENTIRE background and scene. Place this person in:\n\n{prompt}"

        # Valider que le prompt respecte les règles
        validation = validate_prompt_rules(prompt)
        if not validation['valid']:
            print(f"   ⚠️  Prompt validation score: {validation['score']}/100")
            failed = [k for k, v in validation['criteria'].items() if not v['passed']]
            print(f"   ⚠️  Failed criteria: {', '.join(failed)}")

        return prompt

    def generate_image(self, scene_id: int, keyframe_type: str) -> dict:
        """Génère une image via FLUX Pro Kontext."""

        print(f"\n🎨 Génération image scène {scene_id} ({keyframe_type})...")

        positive_prompt = self._build_positive_prompt(scene_id, keyframe_type)

        print(f"   Prompt: {positive_prompt[:100]}...")

        try:
            # Préparer payload pour Flux Kontext
            payload = {
                "prompt": positive_prompt,
                "image_url": self._to_data_uri(self.reference_image),
                "guidance_scale": 4.0,
                "num_images": 1,
                "output_format": "png"
            }

            print(f"   📸 Référence: {Path(self.reference_image).name}")
            print(f"   🚀 Appel Fal.ai Flux Pro Kontext (synchrone)...")

            # Appel synchrone direct (pas de queue)
            req = urllib.request.Request(
                ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Key {self.fal_key}",
                    "Content-Type": "application/json"
                }
            )

            t0 = time.time()
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - t0

            # Extraire l'image
            images = result.get("images", [])
            if not images:
                raise ValueError(f"Pas d'images dans résultat: {result}")

            image_url = images[0]["url"]
            width = images[0].get("width", "?")
            height = images[0].get("height", "?")

            print(f"   ⏱️  Généré en {elapsed:.1f}s ({width}x{height})")

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
                "cost_usd": PRICING_FLUX_KONTEXT,
                "elapsed": elapsed
            }

        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            raise

    def generate_with_validation(self, scene_id: int, keyframe_type: str, max_attempts: int = 3) -> dict:
        """Génère une image avec validation automatique améliorée."""
        import sys
        import shutil
        sys.path.insert(0, str(Path(__file__).parent))
        from validation_images_v2 import ImageValidatorV2

        validator = ImageValidatorV2(
            reference_image=self.reference_image if self.reference_image else None
        )

        best_result = None
        best_score = -1.0
        all_attempts = []

        for attempt in range(1, max_attempts + 1):
            print(f"\n🎨 Génération image scène {scene_id} ({keyframe_type}) - Tentative {attempt}/{max_attempts}")

            # Générer image
            result = self.generate_image(scene_id, keyframe_type)

            # Renommer avec suffixe de tentative
            original_path = Path(result['filepath'])
            attempt_path = original_path.parent / f"{original_path.stem}_attempt{attempt}{original_path.suffix}"
            shutil.copy(original_path, attempt_path)
            print(f"   💾 Copie sauvegardée: {attempt_path.name}")

            # Valider
            validation = validator.validate_image_v2(
                image_path=result['filepath'],
                scene_id=scene_id,
                scenario=self.scenario
            )

            # Afficher scores
            quality_score = validation['quality']['score']
            resemblance_score = validation['resemblance']['score']
            is_ref_copy = validation['is_reference_copy']
            people_check = validation['people_count_check']

            print(f"   📊 Qualité: {quality_score:.2f} {'✅' if quality_score >= 0.7 else '❌'}")
            print(f"   📊 Ressemblance: {resemblance_score:.2f} {'✅' if resemblance_score >= 0.8 else '❌'}")
            print(f"   📊 Copie ref: {'❌ OUI' if is_ref_copy else '✅ NON'}")
            print(f"   📊 Nb personnes: {people_check['detected']}/{people_check['expected']} {'✅' if people_check['valid'] else '❌'}")

            # Calculer score combiné (ressemblance prioritaire)
            combined_score = resemblance_score * 0.7 + quality_score * 0.3

            # Garder la meilleure
            if combined_score > best_score:
                best_score = combined_score
                best_result = {
                    'attempt': attempt,
                    'result': result,
                    'validation': validation,
                    'attempt_path': str(attempt_path),
                    'combined_score': combined_score
                }
                print(f"   ⭐ Nouvelle meilleure image (score combiné: {combined_score:.2f})")

            all_attempts.append({
                'attempt': attempt,
                'resemblance': resemblance_score,
                'quality': quality_score,
                'combined': combined_score
            })

            # Si validée, retourner
            if validation['overall_passed']:
                print(f"   ✅ Image validée !")
                result['validation'] = validation
                result['all_attempts'] = all_attempts
                return result

            # Si échec et pas dernière tentative
            if attempt < max_attempts:
                print(f"   🔄 Validation échouée, nouvelle tentative...")

        # Fin des tentatives - garder la meilleure
        print(f"\n   ⚠️  ÉCHEC après {max_attempts} tentatives")
        print(f"   ⭐ MEILLEURE image: tentative {best_result['attempt']} (score: {best_result['combined_score']:.2f})")

        # Copier la meilleure vers le fichier final
        shutil.copy(best_result['attempt_path'], original_path)
        print(f"   💾 Meilleure image conservée: {original_path.name}")

        best_result['result']['validation'] = best_result['validation']
        best_result['result']['all_attempts'] = all_attempts
        best_result['result']['best_attempt'] = best_result['attempt']
        return best_result['result']

    def generate_scenes(self, scene_ids: list, keyframes: str = "start", validate: bool = True, max_attempts: int = 3) -> list:
        """Génère des scènes spécifiques."""

        print(f"\n🎬 GÉNÉRATION IMAGES — Flux Pro Kontext")
        print(f"   Scénario: {self.scenario_path}")
        print(f"   Scènes: {scene_ids}")
        print(f"   Keyframes: {keyframes}")
        if self.reference_image:
            print(f"   📸 Image de référence: {Path(self.reference_image).name}")
        print(f"   Validation: {'✅ Activée' if validate else '❌ Désactivée'}")
        print(f"   Output: {self.output_dir}/")

        results = []

        for scene_id in scene_ids:
            try:
                if validate:
                    result = self.generate_with_validation(scene_id, "start", max_attempts)
                else:
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

    parser = argparse.ArgumentParser(description="Génération images FLUX Kontext depuis scénario v8")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("--scenes", nargs="+", type=int, required=True,
                        help="IDs de scènes à générer (ex: 4 5)")
    parser.add_argument("--output", default="generated_images_flux_kontext",
                        help="Dossier de sortie (défaut: generated_images_flux_kontext)")
    parser.add_argument("--reference-images", help="Image(s) de référence : fichier unique ou dossier")
    parser.add_argument("--max-attempts", type=int, default=3,
                        help="Nombre max de tentatives (défaut: 3)")
    parser.add_argument("--no-validate", action="store_true",
                        help="Désactiver la validation (plus rapide)")

    args = parser.parse_args()

    if not Path(args.scenario).exists():
        print(f"❌ Fichier introuvable : {args.scenario}")
        sys.exit(1)

    if args.reference_images and not Path(args.reference_images).exists():
        print(f"❌ Images de référence introuvables : {args.reference_images}")
        sys.exit(1)

    generator = ImageGeneratorFluxKontext(args.scenario, args.output, args.reference_images)
    validate = not args.no_validate
    generator.generate_scenes(args.scenes, validate=validate, max_attempts=args.max_attempts)


if __name__ == "__main__":
    main()
