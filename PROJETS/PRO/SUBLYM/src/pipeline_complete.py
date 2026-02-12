"""
PIPELINE COMPLET — Images Flux Kontext + Vidéos MiniMax
Génère automatiquement images validées puis vidéos
"""

import sys
import time
import argparse
from pathlib import Path
from image_generator_flux_kontext import ImageGeneratorFluxKontext
from image_generator_gemini import ImageGeneratorGemini
from image_generator_gemini_native import ImageGeneratorGeminiNative
from video_generator_minimax import VideoGeneratorMinimax


def main():
    parser = argparse.ArgumentParser(description="Pipeline complet : Images Flux Kontext + Vidéos MiniMax")
    parser.add_argument("scenario", help="Chemin vers scenario_v8_*.json")
    parser.add_argument("--scenes", nargs="+", type=int, required=True,
                        help="IDs de scènes à générer (ex: 1 2 3 4 5)")
    parser.add_argument("--reference-images", required=True,
                        help="Image(s) de référence : fichier unique ou dossier")
    parser.add_argument("--images-output", default="generated_images_flux_final",
                        help="Dossier de sortie images (défaut: generated_images_flux_final)")
    parser.add_argument("--videos-output", default="generated_videos_final",
                        help="Dossier de sortie vidéos (défaut: generated_videos_final)")
    parser.add_argument("--max-attempts", type=int, default=7,
                        help="Nombre max de tentatives par image (défaut: 7)")
    parser.add_argument("--skip-images", action="store_true",
                        help="Sauter la génération d'images (utiliser images existantes)")
    parser.add_argument("--skip-videos", action="store_true",
                        help="Sauter la génération de vidéos (images seulement)")
    parser.add_argument("--image-generator", choices=["flux", "gemini", "gemini-native"], default="flux",
                        help="Générateur d'images : flux (Flux Kontext Pro), gemini (Gemini via Fal), ou gemini-native (Gemini SDK direct)")

    args = parser.parse_args()

    # Vérifications
    if not Path(args.scenario).exists():
        print(f"❌ Fichier introuvable : {args.scenario}")
        sys.exit(1)

    if not Path(args.reference_images).exists():
        print(f"❌ Images de référence introuvables : {args.reference_images}")
        sys.exit(1)

    print("\n" + "="*70)
    print("  🎬 PIPELINE COMPLET — SUBLYM")
    print("="*70)
    print(f"   Scénario: {args.scenario}")
    print(f"   Scènes: {args.scenes}")
    print(f"   Référence: {args.reference_images}")
    print(f"   Max tentatives: {args.max_attempts}")
    print("="*70)
    sys.stdout.flush()

    pipeline_start = time.time()

    # =========================================================================
    # ÉTAPE 1 : GÉNÉRATION IMAGES (Flux Kontext + Validation)
    # =========================================================================

    if not args.skip_images:
        if args.image_generator == "gemini":
            generator_name = "GEMINI 3 PRO (Fal.ai)"
        elif args.image_generator == "gemini-native":
            generator_name = "GEMINI NATIVE (SDK Direct)"
        else:
            generator_name = "FLUX KONTEXT"

        print("\n\n" + f"🎨 ÉTAPE 1/2 : GÉNÉRATION IMAGES {generator_name}".center(70, "="))
        print()
        sys.stdout.flush()

        try:
            if args.image_generator == "gemini":
                generator_images = ImageGeneratorGemini(
                    scenario_path=args.scenario,
                    output_dir=args.images_output,
                    reference_images=args.reference_images
                )
            elif args.image_generator == "gemini-native":
                generator_images = ImageGeneratorGeminiNative(
                    scenario_path=args.scenario,
                    output_dir=args.images_output,
                    reference_images=args.reference_images
                )
            else:
                generator_images = ImageGeneratorFluxKontext(
                    scenario_path=args.scenario,
                    output_dir=args.images_output,
                    reference_images=args.reference_images
                )

            results_images = generator_images.generate_scenes(
                scene_ids=args.scenes,
                validate=True,
                max_attempts=args.max_attempts
            )

            if not results_images:
                print("\n❌ Aucune image générée. Arrêt du pipeline.")
                sys.exit(1)

            print(f"\n✅ {len(results_images)} images générées avec succès")

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
    # ÉTAPE 2 : GÉNÉRATION VIDÉOS (MiniMax)
    # =========================================================================

    if not args.skip_videos:
        print("\n\n" + "🎥 ÉTAPE 2/2 : GÉNÉRATION VIDÉOS MINIMAX".center(70, "="))
        print()
        sys.stdout.flush()

        try:
            generator_videos = VideoGeneratorMinimax(
                scenario_path=args.scenario,
                images_dir=str(images_dir),
                output_dir=args.videos_output
            )

            results_videos = generator_videos.generate_scenes(args.scenes)

            if not results_videos:
                print("\n⚠️  Aucune vidéo générée (images manquantes ?)")
            else:
                print(f"\n✅ {len(results_videos)} vidéos générées avec succès")

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
    print("  ✅ PIPELINE TERMINÉ".center(70))
    print("="*70)
    print(f"   Durée totale: {pipeline_duration:.0f}s ({pipeline_duration/60:.1f}min)")
    print(f"   Images: {args.images_output}/")
    if not args.skip_videos:
        print(f"   Vidéos: {args.videos_output}/")
    print("="*70)
    print()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
