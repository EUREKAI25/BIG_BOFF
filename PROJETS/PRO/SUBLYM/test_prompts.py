"""
TEST PROMPTS — Génère un scénario et affiche tous les prompts sans générer d'images

Usage:
    python test_prompts.py session_mickael.json
"""

import sys
import json
from pathlib import Path
from src.pipeline_v8_batch import run as generate_scenario
from src.prompt_generator import generate_prompt, validate_prompt_rules, PROMPT_RULES

def display_prompt_validation(scene_id: int, prompt: str, validation: dict):
    """Affiche le prompt et sa validation de manière lisible."""
    print(f"\n{'='*80}")
    print(f"SCÈNE {scene_id} — PROMPT GÉNÉRÉ")
    print(f"{'='*80}")
    print(prompt)
    print(f"\n{'-'*80}")
    print(f"VALIDATION — Score: {validation['score']}/100 {'✅ VALIDE' if validation['valid'] else '❌ INVALIDE'}")
    print(f"{'-'*80}")

    for criterion, data in validation['criteria'].items():
        status = "✅" if data['passed'] else "❌"
        print(f"  {status} {criterion}: {data['weight']}% {'(PASS)' if data['passed'] else '(FAIL)'}")

    print(f"{'='*80}\n")


def test_prompts_from_dream(session_path: str):
    """Teste la génération de prompts à partir d'un rêve."""

    print("\n" + "🎬" * 40)
    print("TEST GÉNÉRATION PROMPTS — TOUTES LES ÉTAPES")
    print("🎬" * 40 + "\n")

    # ÉTAPE 1 : Générer le scénario complet
    print("\n📝 ÉTAPE 1 : GÉNÉRATION DU SCÉNARIO COMPLET")
    print("=" * 80)
    print(f"Session: {session_path}")
    print("Lancement pipeline_v8_batch.py...\n")

    scenario_obj, scenario_path, audit_path = generate_scenario(session_path)
    print(f"\n✅ Scénario généré : {scenario_path}")
    print(f"✅ Audit log : {audit_path}")

    # ÉTAPE 2 : Charger le scénario
    print("\n📖 ÉTAPE 2 : LECTURE DU SCÉNARIO GÉNÉRÉ")
    print("=" * 80)

    with open(scenario_path, 'r', encoding='utf-8') as f:
        scenario = json.load(f)

    # Afficher les métadonnées
    metadata = scenario.get('metadata', {})
    user_profile = metadata.get('user_profile', {})

    print(f"Rêve: {metadata.get('dream', 'N/A')}")
    print(f"Utilisateur: {user_profile.get('description', 'N/A')}")
    print(f"Genre: {user_profile.get('gender', 'N/A')}")
    print(f"Nombre de scènes: {metadata.get('nb_scenes', 'N/A')}")
    print(f"Durée totale: {metadata.get('duree_totale', 'N/A')}s")

    # ÉTAPE 3 : Afficher les règles de génération de prompts
    print("\n📋 ÉTAPE 3 : RÈGLES DE GÉNÉRATION DE PROMPTS")
    print("=" * 80)
    print(PROMPT_RULES)

    # ÉTAPE 4 : Générer et valider tous les prompts
    print("\n🎨 ÉTAPE 4 : GÉNÉRATION DES PROMPTS (START & END)")
    print("=" * 80)

    nb_scenes = len(scenario.get('parametres_scenes', []))
    gender = user_profile.get('gender', 'person')

    all_valid = True
    prompts_data = []

    for scene_id in range(1, nb_scenes + 1):
        # Récupérer les données de la scène
        params = next((p for p in scenario.get('parametres_scenes', []) if p['scene_id'] == scene_id), None)
        keyframes = next((k for k in scenario.get('keyframes', []) if k['scene_id'] == scene_id), None)
        palette = next((p for p in scenario.get('palettes_scenes', []) if p['scene_id'] == scene_id), None)
        cadrage = next((c for c in scenario.get('cadrages', []) if c['scene_id'] == scene_id), None)
        imaginaire = scenario.get('imaginaire_collectif', {})

        if not all([params, keyframes, palette, cadrage]):
            print(f"⚠️  Scène {scene_id} : Données incomplètes")
            continue

        # Récupérer palette globale
        palette_globale = scenario.get('palette_globale', {})

        # Générer prompt START
        for keyframe_type in ['start', 'end']:
            kf_data = keyframes[keyframe_type]

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

            validation = validate_prompt_rules(prompt)

            display_prompt_validation(f"{scene_id} ({keyframe_type.upper()})", prompt, validation)

            prompts_data.append({
                'scene_id': scene_id,
                'keyframe_type': keyframe_type,
                'prompt': prompt,
                'validation': validation
            })

            if not validation['valid']:
                all_valid = False

    # ÉTAPE 5 : Résumé final
    print("\n📊 ÉTAPE 5 : RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"Nombre de prompts générés: {len(prompts_data)}")
    print(f"Tous valides: {'✅ OUI' if all_valid else '❌ NON'}")

    # Statistiques de validation
    scores = [p['validation']['score'] for p in prompts_data]
    avg_score = sum(scores) / len(scores) if scores else 0

    print(f"Score moyen: {avg_score:.1f}/100")
    print(f"Score min: {min(scores)}/100")
    print(f"Score max: {max(scores)}/100")

    # Critères les plus problématiques
    failed_criteria = {}
    for p in prompts_data:
        for criterion, data in p['validation']['criteria'].items():
            if not data['passed']:
                failed_criteria[criterion] = failed_criteria.get(criterion, 0) + 1

    if failed_criteria:
        print("\n⚠️  Critères échoués:")
        for criterion, count in sorted(failed_criteria.items(), key=lambda x: -x[1]):
            print(f"  - {criterion}: {count} fois")

    print("\n" + "=" * 80)
    print("✅ TEST TERMINÉ")
    print("=" * 80 + "\n")

    return all_valid


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_prompts.py session_mickael.json")
        sys.exit(1)

    session_path = sys.argv[1]

    if not Path(session_path).exists():
        print(f"❌ Fichier introuvable: {session_path}")
        sys.exit(1)

    success = test_prompts_from_dream(session_path)
    sys.exit(0 if success else 1)
