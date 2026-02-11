"""
VALIDATION IMAGES — Qualité + Ressemblance
Valide les images générées selon critères qualité et ressemblance faciale
"""

import json
import os
import base64
import urllib.request
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

RESEMBLANCE_MIN_SCORE = 0.8  # Score minimum requis
QUALITY_MIN_SCORE = 0.7      # Score minimum qualité

# =============================================================================
# IMAGE VALIDATOR
# =============================================================================

class ImageValidator:
    def __init__(self, reference_image: str = None):
        self.reference_image = reference_image
        self.openai_key = os.getenv("OPENAI_API_TOKEN") or os.getenv("OPENAI_API_KEY")

        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY manquant dans .env")

    def _call_gpt4o_vision(self, image_path: str, prompt: str) -> dict:
        """Appel GPT-4o Vision pour analyse image."""
        with open(image_path, "rb") as img_file:
            image_b64 = base64.b64encode(img_file.read()).decode('utf-8')

        payload = {
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }],
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            return json.loads(result["choices"][0]["message"]["content"])

    def validate_quality(self, image_path: str) -> Dict:
        """
        Valide la qualité technique de l'image.

        Returns:
            {
                "score": 0.0-1.0,
                "issues": ["artefacts", "flou", ...],
                "passed": bool
            }
        """
        prompt = f"""
Analyse cette image et évalue sa qualité technique sur une échelle de 0.0 à 1.0.

Critères à vérifier :
- Netteté et résolution
- Présence d'artefacts IA (mains déformées, texte illisible, distorsions)
- Éclairage et cohérence visuelle
- Composition et cadrage
- Qualité générale (réalisme photo)

Retourne un JSON avec :
{{
    "score": 0.85,
    "issues": ["liste des problèmes détectés ou []"],
    "comments": "brève analyse"
}}

Score minimum acceptable : {QUALITY_MIN_SCORE}
"""
        result = self._call_gpt4o_vision(image_path, prompt)
        result["passed"] = result.get("score", 0) >= QUALITY_MIN_SCORE
        return result

    def validate_resemblance(self, generated_image: str) -> Dict:
        """
        Valide la ressemblance entre image générée et référence.

        Returns:
            {
                "score": 0.0-1.0,
                "passed": bool,
                "comments": str
            }
        """
        if not self.reference_image:
            return {"score": 1.0, "passed": True, "comments": "Pas d'image de référence"}

        # Charger les deux images
        with open(self.reference_image, "rb") as ref_file:
            ref_b64 = base64.b64encode(ref_file.read()).decode('utf-8')

        with open(generated_image, "rb") as gen_file:
            gen_b64 = base64.b64encode(gen_file.read()).decode('utf-8')

        prompt = f"""
Compare ces deux images et évalue la RESSEMBLANCE FACIALE de la personne.

Image 1 = Photo de référence (la vraie personne)
Image 2 = Image générée (à valider)

Évalue la ressemblance sur une échelle de 0.0 à 1.0 en analysant :
- Traits du visage (forme, proportions)
- Couleur de peau
- Morphologie générale
- Style (lunettes, barbe, cheveux si visibles)

Score minimum requis : {RESEMBLANCE_MIN_SCORE}

Retourne un JSON :
{{
    "score": 0.85,
    "similarities": ["liste des points communs"],
    "differences": ["liste des différences"],
    "comments": "analyse brève"
}}
"""

        payload = {
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_b64}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{gen_b64}"}}
                ]
            }],
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            analysis = json.loads(result["choices"][0]["message"]["content"])

        analysis["passed"] = analysis.get("score", 0) >= RESEMBLANCE_MIN_SCORE
        return analysis

    def validate_image(self, image_path: str) -> Dict:
        """
        Validation complète d'une image (qualité + ressemblance).

        Returns:
            {
                "quality": {...},
                "resemblance": {...},
                "overall_passed": bool
            }
        """
        print(f"\n🔍 Validation: {Path(image_path).name}")

        quality = self.validate_quality(image_path)
        print(f"   Qualité: {quality['score']:.2f} {'✅' if quality['passed'] else '❌'}")

        resemblance = self.validate_resemblance(image_path)
        print(f"   Ressemblance: {resemblance['score']:.2f} {'✅' if resemblance['passed'] else '❌'}")

        overall_passed = quality["passed"] and resemblance["passed"]

        return {
            "image": str(image_path),
            "quality": quality,
            "resemblance": resemblance,
            "overall_passed": overall_passed
        }

    def validate_batch(self, image_dir: str) -> Dict:
        """
        Valide toutes les images PNG d'un dossier.

        Returns:
            {
                "total": int,
                "passed": int,
                "failed": int,
                "results": [...],
                "failed_images": [...]
            }
        """
        image_dir = Path(image_dir)
        images = sorted(image_dir.glob("scene_*.png"))

        print(f"\n🎬 VALIDATION BATCH")
        print(f"   Dossier: {image_dir}")
        print(f"   Images: {len(images)}")
        if self.reference_image:
            print(f"   Référence: {Path(self.reference_image).name}")
        print()

        results = []
        failed_images = []

        for img_path in images:
            result = self.validate_image(img_path)
            results.append(result)

            if not result["overall_passed"]:
                failed_images.append({
                    "image": result["image"],
                    "quality_score": result["quality"]["score"],
                    "resemblance_score": result["resemblance"]["score"],
                    "issues": result["quality"].get("issues", [])
                })

        passed = sum(1 for r in results if r["overall_passed"])
        failed = len(results) - passed

        summary = {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
            "failed_images": failed_images
        }

        print(f"\n{'='*70}")
        print(f"  📊 RÉSUMÉ VALIDATION")
        print(f"{'='*70}")
        print(f"   Total: {summary['total']}")
        print(f"   ✅ Validées: {summary['passed']}")
        print(f"   ❌ Rejetées: {summary['failed']}")

        if failed_images:
            print(f"\n   Images rejetées:")
            for img in failed_images:
                print(f"   - {Path(img['image']).name}")
                print(f"     Qualité: {img['quality_score']:.2f}, Ressemblance: {img['resemblance_score']:.2f}")

        # Sauvegarder rapport
        report_path = image_dir / "validation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n   Rapport: {report_path}")

        return summary


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validation images générées")
    parser.add_argument("image_dir", help="Dossier contenant les images à valider")
    parser.add_argument("--reference-image", help="Image de référence pour ressemblance")

    args = parser.parse_args()

    if not Path(args.image_dir).exists():
        print(f"❌ Dossier introuvable : {args.image_dir}")
        return

    validator = ImageValidator(args.reference_image)
    validator.validate_batch(args.image_dir)


if __name__ == "__main__":
    main()
