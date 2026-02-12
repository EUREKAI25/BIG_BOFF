"""
VIDEO GENERATOR MINIMAX — Génération vidéos depuis images
Utilise MiniMax Video-01 via Fal.ai
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

# Charger .env
load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

PRICING_MINIMAX_6S = 0.27  # USD per 6s video
PRICING_MINIMAX_10S = 0.45  # USD per 10s video
ENDPOINT = "https://fal.run/fal-ai/minimax/video-01"

# =============================================================================
# VIDEO GENERATOR MINIMAX
# =============================================================================

class VideoGeneratorMinimax:
    def __init__(self, scenario_path: str, images_dir: str, output_dir: str = "generated_videos"):
        self.scenario_path = scenario_path
        self.images_dir = Path(images_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Charger scénario
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

        # Stats
        self.videos_generated = 0
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

    def _get_video_prompt(self, scene_id: int) -> str:
        """Récupère le prompt vidéo depuis le scénario."""

        # Chercher dans prompts_video
        for prompt_data in self.scenario.get("prompts_video", []):
            if prompt_data.get("scene_id") == scene_id:
                return prompt_data.get("prompt", "")

        # Fallback : construire depuis l'action
        for params in self.scenario.get("parametres_scenes", []):
            if params.get("scene_id") == scene_id:
                action = params.get("action", "")
                return f"Smooth cinematic video. {action}"

        return "Smooth cinematic video."

    def generate_video(self, scene_id: int, start_image_path: str, duration: int = 6) -> dict:
        """Génère une vidéo via MiniMax."""

        print(f"\n🎥 Génération vidéo scène {scene_id} ({duration}s)...")

        # Récupérer le prompt
        video_prompt = self._get_video_prompt(scene_id)
        print(f"   Prompt: {video_prompt[:100]}...")

        # Vérifier que l'image existe
        if not Path(start_image_path).exists():
            raise FileNotFoundError(f"Image introuvable : {start_image_path}")

        try:
            # Préparer payload pour MiniMax
            payload = {
                "prompt": video_prompt,
                "image_url": self._to_data_uri(start_image_path),
                "prompt_optimizer": False
            }

            print(f"   📸 Image de départ: {Path(start_image_path).name}")
            print(f"   🚀 Appel MiniMax via Fal.ai...")

            # Appel synchrone
            req = urllib.request.Request(
                ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Key {self.fal_key}",
                    "Content-Type": "application/json"
                }
            )

            t0 = time.time()
            with urllib.request.urlopen(req, timeout=900) as response:  # 15 min au lieu de 10 min
                result = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - t0

            # Extraire l'URL de la vidéo
            video_url = result.get("video", {}).get("url")
            if not video_url:
                raise ValueError(f"Pas d'URL de vidéo dans résultat: {result}")

            print(f"   ⏱️  Généré en {elapsed:.1f}s")

            # Télécharger et sauvegarder
            filename = f"scene_{scene_id:02d}_{duration}s.mp4"
            filepath = self.output_dir / filename

            urllib.request.urlretrieve(video_url, filepath)

            self.videos_generated += 1
            cost = PRICING_MINIMAX_6S if duration == 6 else PRICING_MINIMAX_10S
            self.total_cost += cost

            print(f"   ✅ Sauvegardé : {filepath}")

            return {
                "scene_id": scene_id,
                "video_url": video_url,
                "filepath": str(filepath),
                "duration": duration,
                "cost_usd": cost,
                "elapsed": elapsed
            }

        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            raise

    def generate_scenes(self, scene_ids: list) -> list:
        """Génère des vidéos pour les scènes spécifiées."""

        print(f"\n🎬 GÉNÉRATION VIDÉOS — MiniMax Video-01")
        print(f"   Scénario: {self.scenario_path}")
        print(f"   Images: {self.images_dir}/")
        print(f"   Scènes: {scene_ids}")
        print(f"   Output: {self.output_dir}/")

        results = []

        # Récupérer les durées depuis le scénario
        durees = {}
        rythme_data = self.scenario.get("rythme", {})
        if isinstance(rythme_data, dict):
            scenes_rythme = rythme_data.get("scenes", [])
        else:
            scenes_rythme = rythme_data if isinstance(rythme_data, list) else []

        for scene_rythme in scenes_rythme:
            durees[scene_rythme.get("scene_id")] = scene_rythme.get("duree", 6)

        for scene_id in scene_ids:
            try:
                # Trouver l'image de départ
                start_image = self.images_dir / f"scene_{scene_id:02d}_start.png"

                if not start_image.exists():
                    print(f"\n   ⚠️  Scène {scene_id} ignorée : image introuvable ({start_image.name})")
                    continue

                # Récupérer la durée
                duration = durees.get(scene_id, 6)
                if duration not in [6, 10]:
                    print(f"   ⚠️  Durée {duration}s invalide, utilisation de 6s")
                    duration = 6

                result = self.generate_video(scene_id, str(start_image), duration)
                results.append(result)

            except Exception as e:
                print(f"\n   ⚠️  Scène {scene_id} ignorée : {e}")
                continue

        # Résumé final
        duration_total = time.time() - self.start_time

        print(f"\n{'='*70}")
        print(f"  ✅ GÉNÉRATION TERMINÉE")
        print(f"{'='*70}")
        print(f"   Vidéos générées: {self.videos_generated}")
        if self.videos_generated > 0:
            print(f"   Durée totale: {duration_total:.0f}s ({duration_total/self.videos_generated:.0f}s/vidéo)")
            print(f"   Coût total: ${self.total_cost:.2f}")
            print(f"   Coût/vidéo: ${self.total_cost/self.videos_generated:.2f}")
        print(f"{'='*70}")

        return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Génération vidéos MiniMax depuis images")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("--images-dir", required=True,
                        help="Dossier contenant les images (ex: generated_images_flux_final)")
    parser.add_argument("--scenes", nargs="+", type=int, required=True,
                        help="IDs de scènes à générer (ex: 1 2 3 4 5)")
    parser.add_argument("--output", default="generated_videos",
                        help="Dossier de sortie (défaut: generated_videos)")

    args = parser.parse_args()

    if not Path(args.scenario).exists():
        print(f"❌ Fichier introuvable : {args.scenario}")
        sys.exit(1)

    if not Path(args.images_dir).exists():
        print(f"❌ Dossier images introuvable : {args.images_dir}")
        sys.exit(1)

    generator = VideoGeneratorMinimax(args.scenario, args.images_dir, args.output)
    generator.generate_scenes(args.scenes)


if __name__ == "__main__":
    main()
