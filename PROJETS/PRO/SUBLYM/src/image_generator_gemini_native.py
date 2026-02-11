"""
IMAGE GENERATOR GEMINI NATIVE — Génération images depuis scénario v8
Utilise SDK Gemini natif (pas Fal.ai) pour cohérence maximale
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from prompt_generator import generate_prompt, validate_prompt_rules

# Charger .env
load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

PRICING_GEMINI_PRO = 0.18  # USD per image (SDK natif)

# =============================================================================
# IMAGE GENERATOR GEMINI NATIVE
# =============================================================================

class ImageGeneratorGeminiNative:
    def __init__(self, scenario_path: str, output_dir: str = "generated_images", reference_images: list = None):
        self.scenario_path = scenario_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Support multi-photos référence
        if reference_images:
            if isinstance(reference_images, str):
                ref_path = Path(reference_images)
                if ref_path.is_dir():
                    self.reference_images = sorted([str(p) for p in ref_path.glob("*.png")])[:5]
                    print(f"📸 {len(self.reference_images)} images de référence trouvées")
                    for i, img in enumerate(self.reference_images):
                        print(f"   {i+1}. {Path(img).name}")
                else:
                    self.reference_images = [reference_images]
            else:
                self.reference_images = reference_images[:5]
        else:
            self.reference_images = None

        # Charger scénario
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

        # Stats
        self.images_generated = 0
        self.total_cost = 0.0
        self.start_time = time.time()

        # Gemini API
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY manquant dans .env")

        # Client Gemini
        self._client = None

    def _get_client(self):
        """Lazy init du client Gemini."""
        if self._client is None:
            try:
                from google import genai
            except ImportError:
                raise ImportError("Installez le SDK: pip install google-genai")

            self._client = genai.Client(api_key=self.gemini_key)
        return self._client

    def _load_image_as_bytes(self, image_path: str) -> tuple:
        """Charge une image locale en bytes."""
        path = Path(image_path)

        # Déterminer le mime type
        ext = path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }
        mime_type = mime_types.get(ext, "image/png")

        with open(path, "rb") as f:
            data = f.read()

        return data, mime_type

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
        """Génère une image via Gemini SDK natif."""

        print(f"\n🎨 Génération image scène {scene_id} ({keyframe_type})...")

        positive_prompt = self._build_positive_prompt(scene_id, keyframe_type)

        print(f"   Prompt: {positive_prompt[:100]}...")

        try:
            from google.genai import types
        except ImportError:
            raise ImportError("Installez le SDK: pip install google-genai")

        client = self._get_client()

        # Construire le contenu
        contents = []

        # Ajouter les images de référence avec instruction explicite
        if self.reference_images:
            contents.append("PRIMARY FACE REFERENCE - This person's face MUST match these photos exactly. Use ONLY these images for facial features, skin tone, and appearance:")
            for img_path in self.reference_images:
                img_data, mime_type = self._load_image_as_bytes(img_path)
                contents.append(types.Part.from_bytes(data=img_data, mime_type=mime_type))
                print(f"   📸 Ref: {Path(img_path).name}")

        # Ajouter le prompt
        contents.append(f"Generate this image: {positive_prompt}")

        print(f"   🚀 Appel Gemini SDK natif...")
        print(f"   - Modèle: gemini-3-pro-image-preview")
        print(f"   - Références: {len(self.reference_images) if self.reference_images else 0}")

        # Configuration
        config = types.GenerateContentConfig(
            response_modalities=['IMAGE', 'TEXT'],
            image_config=types.ImageConfig(
                aspect_ratio="4:3"
            )
        )

        # Générer
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=config
        )

        # Vérifier la réponse
        if not response.candidates:
            raise ValueError("Gemini n'a pas retourné de candidats (possible safety filter)")

        candidate = response.candidates[0]

        if not candidate.content or not candidate.content.parts:
            finish_reason = getattr(candidate, 'finish_reason', None)
            raise ValueError(f"Gemini n'a pas retourné de contenu. Finish reason: {finish_reason}")

        # Extraire l'image
        image_data = None
        text_response = ""

        for part in candidate.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
            elif hasattr(part, 'text') and part.text:
                text_response = part.text

        if not image_data:
            raise ValueError(f"Pas d'image dans la réponse. Texte: {text_response}")

        # Sauvegarder
        filename = f"scene_{scene_id:02d}_{keyframe_type}.png"
        filepath = self.output_dir / filename

        with open(filepath, "wb") as f:
            f.write(image_data)

        self.images_generated += 1
        self.total_cost += PRICING_GEMINI_PRO

        print(f"   ✅ Sauvegardé : {filepath}")

        return {
            "scene_id": scene_id,
            "keyframe_type": keyframe_type,
            "filepath": str(filepath),
            "cost_usd": PRICING_GEMINI_PRO,
            "text_response": text_response
        }

    def generate_with_validation(self, scene_id: int, keyframe_type: str, max_attempts: int = 3) -> dict:
        """Génère une image avec validation automatique améliorée."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from validation_images_v2 import ImageValidatorV2

        validator = ImageValidatorV2(
            reference_image=self.reference_images[0] if self.reference_images else None
        )

        for attempt in range(1, max_attempts + 1):
            print(f"\n🎨 Génération image scène {scene_id} ({keyframe_type}) - Tentative {attempt}/{max_attempts}")

            # Générer image
            result = self.generate_image(scene_id, keyframe_type)

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

            # Si validée, retourner
            if validation['overall_passed']:
                print(f"   ✅ Image validée !")
                result['validation'] = validation
                return result

            # Si échec et pas dernière tentative
            if attempt < max_attempts:
                print(f"   🔄 Validation échouée, nouvelle tentative...")
            else:
                print(f"   ⚠️  ÉCHEC après {max_attempts} tentatives → IMAGE CONSERVÉE POUR ANALYSE")
                result['validation'] = validation
                return result

    def generate_scenes(self, scene_ids: list, keyframes: str = "start", validate: bool = True, max_attempts: int = 3) -> list:
        """Génère des scènes spécifiques."""

        print(f"\n🎬 GÉNÉRATION IMAGES — Gemini SDK Natif")
        print(f"   Scénario: {self.scenario_path}")
        print(f"   Scènes: {scene_ids}")
        print(f"   Keyframes: {keyframes}")
        if self.reference_images:
            print(f"   📸 {len(self.reference_images)} images de référence")
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

    parser = argparse.ArgumentParser(description="Génération images Gemini SDK natif depuis scénario v8")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("--scenes", nargs="+", type=int, required=True,
                        help="IDs de scènes à générer (ex: 4 5)")
    parser.add_argument("--output", default="generated_images_gemini_native",
                        help="Dossier de sortie (défaut: generated_images_gemini_native)")
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

    generator = ImageGeneratorGeminiNative(args.scenario, args.output, args.reference_images)
    validate = not args.no_validate
    generator.generate_scenes(args.scenes, validate=validate, max_attempts=args.max_attempts)


if __name__ == "__main__":
    main()
