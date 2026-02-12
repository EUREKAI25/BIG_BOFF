"""
PIPELINE COMPLET PARALLÈLE — Images Gemini + Vidéos MiniMax
Génération en parallèle pour optimiser le temps d'exécution
"""

import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from image_generator_gemini_native import ImageGeneratorGeminiNative
from video_generator_minimax import VideoGeneratorMinimax


def generate_single_image_with_validation(args_tuple):
    """
    Fonction wrapper pour générer une image (à exécuter dans un process séparé).

    Args:
        args_tuple: (scene_id, scenario_path, output_dir, reference_images, max_attempts)

    Returns:
        dict avec résultat ou None si échec
    """
    scene_id, scenario_path, output_dir, reference_images, max_attempts = args_tuple

    try:
        # Créer un générateur pour cette scène uniquement
        generator = ImageGeneratorGeminiNative(
            scenario_path=scenario_path,
            output_dir=output_dir,
            reference_images=reference_images
        )

        # Générer avec validation
        result = generator.generate_with_validation(
            scene_id=scene_id,
            keyframe_type="start",
            max_attempts=max_attempts
        )

        return result

    except Exception as e:
        print(f"\n   ❌ Erreur scène {scene_id} : {e}")
        return None


def generate_single_video(args_tuple):
    """
    Fonction wrapper pour générer une vidéo (à exécuter dans un process séparé).

    Args:
        args_tuple: (scene_id, scenario_path, images_dir, output_dir, duration)

    Returns:
        dict avec résultat ou None si échec
    """
    scene_id, scenario_path, images_dir, output_dir, duration = args_tuple

    try:
        # Créer un générateur pour cette vidéo uniquement
        generator = VideoGeneratorMinimax(
            scenario_path=scenario_path,
            images_dir=images_dir,
            output_dir=output_dir
        )

        # Trouver l'image de départ
        start_image = Path(images_dir) / f"scene_{scene_id:02d}_start.png"

        if not start_image.exists():
            print(f"\n   ⚠️  Scène {scene_id} : image introuvable ({start_image.name})")
            return None

        # Générer la vidéo
        result = generator.generate_video(
            scene_id=scene_id,
            start_image_path=str(start_image),
            duration=duration
        )

        return result

    except Exception as e:
        print(f"\n   ❌ Erreur vidéo scène {scene_id} : {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Pipeline complet PARALLÈLE : Images Gemini + Vidéos MiniMax")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("--scenes", nargs="+", type=int, required=True,
                        help="IDs de scènes à générer (ex: 1 2 3 4 5)")
    parser.add_argument("--reference-images", required=True,
                        help="Image(s) de référence : fichier unique ou dossier")
    parser.add_argument("--images-output", default="generated_images_gemini_native",
                        help="Dossier de sortie images (défaut: generated_images_gemini_native)")
    parser.add_argument("--videos-output", default="generated_videos_final",
                        help="Dossier de sortie vidéos (défaut: generated_videos_final)")
    parser.add_argument("--max-attempts", type=int, default=7,
                        help="Nombre max de tentatives par image (défaut: 7)")
    parser.add_argument("--skip-images", action="store_true",
                        help="Sauter la génération d'images (utiliser images existantes)")
    parser.add_argument("--skip-videos", action="store_true",
                        help="Sauter la génération de vidéos (images seulement)")
    parser.add_argument("--max-workers", type=int, default=5,
                        help="Nombre max de workers parallèles (défaut: 5)")

    args = parser.parse_args()

    # Vérifications
    if not Path(args.scenario).exists():
        print(f"❌ Fichier introuvable : {args.scenario}")
        sys.exit(1)

    if not Path(args.reference_images).exists():
        print(f"❌ Images de référence introuvables : {args.reference_images}")
        sys.exit(1)

    print("\n" + "="*70)
    print("  🚀 PIPELINE COMPLET PARALLÈLE — SUBLYM")
    print("="*70)
    print(f"   Scénario: {args.scenario}")
    print(f"   Scènes: {args.scenes}")
    print(f"   Référence: {args.reference_images}")
    print(f"   Max tentatives: {args.max_attempts}")
    print(f"   Workers parallèles: {args.max_workers}")
    print("="*70)
    sys.stdout.flush()

    pipeline_start = time.time()

    # =========================================================================
    # ÉTAPE 1 : GÉNÉRATION IMAGES (PARALLÈLE)
    # =========================================================================

    images_results = []

    if not args.skip_images:
        print("\n\n" + "🎨 ÉTAPE 1/2 : GÉNÉRATION IMAGES PARALLÈLE (GEMINI NATIVE)".center(70, "="))
        print()
        sys.stdout.flush()

        # Créer le dossier de sortie
        Path(args.images_output).mkdir(parents=True, exist_ok=True)

        try:
            images_start = time.time()

            # Préparer les arguments pour chaque scène
            image_tasks = [
                (scene_id, args.scenario, args.images_output, args.reference_images, args.max_attempts)
                for scene_id in args.scenes
            ]

            print(f"   🔥 Lancement de {len(image_tasks)} générations en parallèle...")
            sys.stdout.flush()

            # Exécuter en parallèle
            with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
                futures = {executor.submit(generate_single_image_with_validation, task): task[0]
                          for task in image_tasks}

                for future in as_completed(futures):
                    scene_id = futures[future]
                    try:
                        result = future.result()
                        if result:
                            images_results.append(result)
                            print(f"\n   ✅ Scène {scene_id} terminée")
                        else:
                            print(f"\n   ⚠️  Scène {scene_id} échouée")
                    except Exception as e:
                        print(f"\n   ❌ Scène {scene_id} erreur : {e}")
                    sys.stdout.flush()

            images_duration = time.time() - images_start

            if not images_results:
                print("\n❌ Aucune image générée. Arrêt du pipeline.")
                sys.exit(1)

            print(f"\n✅ {len(images_results)} images générées en {images_duration:.1f}s")
            print(f"   Temps moyen: {images_duration/len(images_results):.1f}s/image")
            print(f"   Gain vs séquentiel: ~{len(images_results)*65 - images_duration:.0f}s économisés")

        except Exception as e:
            print(f"\n❌ Erreur génération images : {e}")
            sys.exit(1)

    else:
        print("\n\n⏩ ÉTAPE 1/2 SAUTÉE : Utilisation images existantes\n")

    # Vérifier que les images existent
    images_dir = Path(args.images_output)
    if not images_dir.exists():
        print(f"\n❌ Dossier images introuvable : {images_dir}")
        sys.exit(1)

    # =========================================================================
    # ÉTAPE 2 : GÉNÉRATION VIDÉOS (PARALLÈLE)
    # =========================================================================

    videos_results = []

    if not args.skip_videos:
        print("\n\n" + "🎥 ÉTAPE 2/2 : GÉNÉRATION VIDÉOS PARALLÈLE (MINIMAX)".center(70, "="))
        print()
        sys.stdout.flush()

        # Créer le dossier de sortie
        Path(args.videos_output).mkdir(parents=True, exist_ok=True)

        try:
            videos_start = time.time()

            # Charger le scénario pour récupérer les durées
            import json
            with open(args.scenario, "r", encoding="utf-8") as f:
                scenario = json.load(f)

            durees = {}
            rythme_data = scenario.get("rythme", {})
            if isinstance(rythme_data, dict):
                scenes_rythme = rythme_data.get("scenes", [])
            else:
                scenes_rythme = rythme_data if isinstance(rythme_data, list) else []

            for scene_rythme in scenes_rythme:
                durees[scene_rythme.get("scene_id")] = scene_rythme.get("duree", 6)

            # Préparer les arguments pour chaque vidéo
            video_tasks = [
                (scene_id, args.scenario, str(images_dir), args.videos_output, durees.get(scene_id, 6))
                for scene_id in args.scenes
            ]

            print(f"   🔥 Lancement de {len(video_tasks)} générations vidéo en parallèle...")
            sys.stdout.flush()

            # Exécuter en parallèle
            with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
                futures = {executor.submit(generate_single_video, task): task[0]
                          for task in video_tasks}

                for future in as_completed(futures):
                    scene_id = futures[future]
                    try:
                        result = future.result()
                        if result:
                            videos_results.append(result)
                            print(f"\n   ✅ Vidéo scène {scene_id} terminée")
                        else:
                            print(f"\n   ⚠️  Vidéo scène {scene_id} échouée")
                    except Exception as e:
                        print(f"\n   ❌ Vidéo scène {scene_id} erreur : {e}")
                    sys.stdout.flush()

            videos_duration = time.time() - videos_start

            if videos_results:
                print(f"\n✅ {len(videos_results)} vidéos générées en {videos_duration:.1f}s")
                print(f"   Temps moyen: {videos_duration/len(videos_results):.1f}s/vidéo")
                print(f"   Gain vs séquentiel: ~{len(videos_results)*240 - videos_duration:.0f}s économisés")
            else:
                print("\n⚠️  Aucune vidéo générée (images manquantes ?)")

        except Exception as e:
            print(f"\n❌ Erreur génération vidéos : {e}")
            # Ne pas exit ici, les images sont déjà générées
            print("⚠️  Les images ont été générées avec succès malgré l'erreur vidéos")

    else:
        print("\n\n⏩ ÉTAPE 2/2 SAUTÉE : Pas de génération vidéos\n")

    # =========================================================================
    # RÉSUMÉ FINAL
    # =========================================================================

    pipeline_duration = time.time() - pipeline_start

    print("\n\n" + "="*70)
    print("  ✅ PIPELINE PARALLÈLE TERMINÉ".center(70))
    print("="*70)
    print(f"   Durée totale: {pipeline_duration:.0f}s ({pipeline_duration/60:.1f}min)")
    print(f"   Images générées: {len(images_results)}")
    print(f"   Vidéos générées: {len(videos_results)}")
    print(f"   Images: {args.images_output}/")
    if not args.skip_videos:
        print(f"   Vidéos: {args.videos_output}/")
    print("="*70)
    print()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
