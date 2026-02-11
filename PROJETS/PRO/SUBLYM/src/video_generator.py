"""
VIDEO GENERATOR — Génération vidéos depuis images + scénario v8
Utilise MiniMax video-01 pour img2video
"""

import json
import os
import sys
import time
import base64
import urllib.request
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Charger .env
load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

PRICING_MINIMAX_VIDEO = 0.10  # USD per 6s video (estimation)
DEFAULT_MODEL_ENDPOINT = "https://queue.fal.run/fal-ai/minimax/video-01/image-to-video"

# =============================================================================
# VIDEO GENERATOR
# =============================================================================

class VideoGenerator:
    def __init__(self, scenario_path: str, images_dir: str, output_dir: str = "generated_videos", model_endpoint: str = None):
        self.scenario_path = scenario_path
        self.images_dir = Path(images_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Endpoint configurable
        self.model_endpoint = model_endpoint or os.getenv("MINIMAX_ENDPOINT", DEFAULT_MODEL_ENDPOINT)

        # Charger scénario
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

        # Stats
        self.videos_generated = 0
        self.total_cost = 0.0
        self.start_time = time.time()

        # Fal.ai API (pour MiniMax)
        self.fal_key = os.getenv("FAL_KEY")
        if not self.fal_key:
            raise ValueError("FAL_KEY manquant dans .env")

    def generate_video(self, scene_id: int) -> dict:
        """Génère une vidéo pour une scène via MiniMax video-01."""

        print(f"\n🎥 Génération vidéo scène {scene_id}...")

        # Trouver l'image start correspondante
        image_path = self.images_dir / f"scene_{scene_id:02d}_start.png"
        if not image_path.exists():
            raise FileNotFoundError(f"Image introuvable : {image_path}")

        # Trouver le prompt vidéo
        video_prompt = None
        for prompt in self.scenario.get("prompts_video", []):
            if prompt.get("scene_id") == scene_id:
                video_prompt = prompt.get("prompt")
                break

        if not video_prompt:
            raise ValueError(f"Prompt vidéo introuvable pour scène {scene_id}")

        print(f"   Image: {image_path.name}")
        print(f"   Prompt: {video_prompt[:100]}...")

        # Encoder image en base64
        with open(image_path, "rb") as img_file:
            image_b64 = base64.b64encode(img_file.read()).decode('utf-8')

        # Préparer requête Fal.ai MiniMax
        payload = {
            "prompt": video_prompt,
            "image_url": f"data:image/png;base64,{image_b64}",
            "prompt_optimizer": True
        }

        try:
            # Appel API Fal.ai MiniMax (endpoint configurable)
            req = urllib.request.Request(
                self.model_endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Key {self.fal_key}",
                    "Content-Type": "application/json"
                }
            )

            print(f"   ⏳ Envoi requête Fal.ai MiniMax...")

            with urllib.request.urlopen(req, timeout=30) as response:
                queue_result = json.loads(response.read().decode("utf-8"))

            # Récupérer URLs de statut
            status_url = queue_result.get("status_url")
            response_url = queue_result.get("response_url")

            if not status_url or not response_url:
                raise ValueError(f"Réponse queue invalide: {queue_result}")

            print(f"   ⏳ Attente génération vidéo...")

            # Polling jusqu'à completion
            video_url = self._poll_fal_task(status_url, response_url)

            # Télécharger vidéo
            filename = f"scene_{scene_id:02d}.mp4"
            filepath = self.output_dir / filename

            urllib.request.urlretrieve(video_url, filepath)

            self.videos_generated += 1
            self.total_cost += PRICING_MINIMAX_VIDEO

            print(f"   ✅ Sauvegardé : {filepath}")

            # Copier aussi l'image keyframe dans le dossier de sortie
            keyframe_output = self.output_dir / f"scene_{scene_id:02d}_start.png"
            shutil.copy(image_path, keyframe_output)
            print(f"   📸 Keyframe copiée : {keyframe_output}")

            return {
                "scene_id": scene_id,
                "url": video_url,
                "filepath": str(filepath),
                "keyframe": str(keyframe_output),
                "cost_usd": PRICING_MINIMAX_VIDEO
            }

        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            raise

    def _poll_fal_task(self, status_url: str, response_url: str, max_wait: int = 300) -> str:
        """Poll le statut d'une tâche Fal.ai jusqu'à completion."""
        poll_interval = 10  # secondes (vidéos prennent du temps)
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

                video_url = result.get("video", {}).get("url")
                if not video_url:
                    raise ValueError(f"Pas d'URL vidéo: {result}")
                return video_url

            elif status == "FAILED":
                error = status_data.get("error", "Unknown error")
                raise ValueError(f"Génération échouée: {error}")

            # Attendre avant prochain poll
            time.sleep(poll_interval)
            elapsed += poll_interval
            print(f"   ⏳ {elapsed}s écoulées...")

        raise TimeoutError(f"Timeout après {max_wait}s")

    def generate_all(self, scene_ids: list = None) -> list:
        """
        Génère toutes les vidéos.

        Args:
            scene_ids: Liste des IDs de scènes à générer (None = toutes)

        Returns:
            Liste des vidéos générées
        """

        print(f"\n🎬 GÉNÉRATION VIDÉOS — MiniMax video-01")
        print(f"   Scénario: {self.scenario_path}")
        print(f"   Images: {self.images_dir}/")
        print(f"   Output: {self.output_dir}/")

        scenes = self.scenario.get("decoupage", [])

        if scene_ids:
            scenes = [s for s in scenes if s["id"] in scene_ids]

        nb_scenes = len(scenes)

        print(f"   Vidéos à générer: {nb_scenes}")
        print(f"   Coût estimé: ${nb_scenes * PRICING_MINIMAX_VIDEO:.2f}\n")

        results = []

        for scene in scenes:
            scene_id = scene["id"]

            try:
                result = self.generate_video(scene_id)
                results.append(result)
            except Exception as e:
                print(f"   ⚠️  Scène {scene_id} ignorée : {e}")
                continue

        # Sauvegarder métadonnées
        duration = time.time() - self.start_time

        metadata = {
            "scenario": self.scenario_path,
            "images_dir": str(self.images_dir),
            "generated_at": datetime.now().isoformat(),
            "videos_generated": self.videos_generated,
            "total_cost_usd": round(self.total_cost, 2),
            "duration_seconds": round(duration, 2),
            "videos": results
        }

        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*70}")
        print(f"  ✅ GÉNÉRATION VIDÉOS TERMINÉE")
        print(f"{'='*70}")
        print(f"   Vidéos générées: {self.videos_generated}")
        print(f"   Durée totale: {duration:.0f}s ({duration/self.videos_generated:.0f}s/vidéo)")
        print(f"   Coût total: ${self.total_cost:.2f}")
        print(f"   Coût/vidéo: ${self.total_cost/self.videos_generated:.2f}")
        print(f"   Métadonnées: {metadata_path}")
        print(f"{'='*70}")

        return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Génération vidéos depuis images v8")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("images_dir", help="Dossier contenant les images start")
    parser.add_argument("--output", default="generated_videos",
                        help="Dossier de sortie (défaut: generated_videos)")
    parser.add_argument("--scenes", nargs="+", type=int,
                        help="IDs de scènes à générer (défaut: toutes)")

    args = parser.parse_args()

    # Vérifier que le scénario existe
    if not Path(args.scenario).exists():
        print(f"❌ Fichier introuvable : {args.scenario}")
        sys.exit(1)

    # Vérifier que le dossier d'images existe
    if not Path(args.images_dir).exists():
        print(f"❌ Dossier d'images introuvable : {args.images_dir}")
        sys.exit(1)

    # Générer
    generator = VideoGenerator(args.scenario, args.images_dir, args.output)
    generator.generate_all(args.scenes)


if __name__ == "__main__":
    main()
