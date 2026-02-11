"""
TEST VALIDATION DEBUG — Génère 1 image et capture tous les détails de validation
"""

import json
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from image_generator_gemini import ImageGeneratorGemini
from validation_images_v2 import ImageValidatorV2

# Config
SCENARIO = "scenario_v8_20260210_230531.json"
REFERENCE_IMG = "generated_images_mickael_final/scene_01_start.png"  # Utiliser une image Flux comme ref
OUTPUT_DIR = "test_validation_debug_output"

print("="*70)
print("TEST VALIDATION DEBUG")
print("="*70)

# Vérifier que les fichiers existent
if not Path(SCENARIO).exists():
    print(f"❌ Scénario introuvable : {SCENARIO}")
    sys.exit(1)

if not Path(REFERENCE_IMG).exists():
    print(f"❌ Image de référence introuvable : {REFERENCE_IMG}")
    sys.exit(1)

# Créer output dir
Path(OUTPUT_DIR).mkdir(exist_ok=True)

print(f"\n📋 Configuration :")
print(f"   Scénario : {SCENARIO}")
print(f"   Référence : {REFERENCE_IMG}")
print(f"   Output : {OUTPUT_DIR}")

# Charger scénario
with open(SCENARIO, "r", encoding="utf-8") as f:
    scenario = json.load(f)

# Générer UNE image (scène 2)
print(f"\n{'='*70}")
print("ÉTAPE 1 : GÉNÉRATION IMAGE")
print("="*70)

generator = ImageGeneratorGemini(
    scenario_path=SCENARIO,
    output_dir=OUTPUT_DIR,
    reference_images=[REFERENCE_IMG]
)

# Capturer le prompt de génération
positive_prompt = generator._build_positive_prompt(scene_id=2, keyframe_type="start")

print("\n📝 PROMPT DE GÉNÉRATION GEMINI :")
print("-"*70)
print(positive_prompt)
print("-"*70)

# Sauvegarder le prompt
with open(f"{OUTPUT_DIR}/prompt_generation.txt", "w", encoding="utf-8") as f:
    f.write(positive_prompt)

# Générer l'image
result = generator.generate_image(scene_id=2, keyframe_type="start")

print(f"\n✅ Image générée : {result['filepath']}")

# VALIDATION DÉTAILLÉE
print(f"\n{'='*70}")
print("ÉTAPE 2 : VALIDATION DÉTAILLÉE")
print("="*70)

validator = ImageValidatorV2(reference_image=REFERENCE_IMG)

# 1. QUALITÉ
print("\n🔍 TEST 1 : QUALITÉ TECHNIQUE")
print("-"*70)

quality_prompt = f"""
Analyse cette image et évalue sa qualité technique sur une échelle de 0.0 à 1.0.

Critères :
- Netteté et résolution
- Artefacts IA (mains déformées, texte illisible, distorsions)
- Éclairage et cohérence visuelle
- Composition et cadrage
- Qualité générale (réalisme photo)
- VISAGE VISIBLE (pas de dos, pas masqué)

Retourne un JSON :
{{
    "score": 0.85,
    "face_visible": true/false,
    "issues": ["liste des problèmes"],
    "comments": "brève analyse"
}}

Score minimum acceptable : 0.7
"""

print("📝 PROMPT QUALITÉ :")
print(quality_prompt)
print()

quality = validator.validate_quality(result['filepath'])
print("📊 RÉSULTAT QUALITÉ :")
print(json.dumps(quality, indent=2, ensure_ascii=False))

# 2. RESSEMBLANCE
print(f"\n{'='*70}")
print("🔍 TEST 2 : RESSEMBLANCE FACIALE")
print("-"*70)

resemblance_prompt = f"""
Compare ces deux images et vérifie que c'est la MÊME PERSONNE.

Image 1 = Photo de référence (la vraie personne)
Image 2 = Image générée (à valider)

VÉRIFICATIONS CRITIQUES (la personne DOIT être identique) :
1. COULEUR DE PEAU : même teinte (noir/blanc/asiatique/etc.)
2. CHEVEUX : même style, longueur, couleur
3. TRAITS DU VISAGE : forme, proportions, nez, bouche, yeux
4. ACCESSOIRES : lunettes, bijoux, piercings (présence/absence)
5. BARBE/MOUSTACHE : même style ou absence

RÈGLE ABSOLUE : Si la couleur de peau est DIFFÉRENTE → score 0.0
RÈGLE ABSOLUE : Si les accessoires principaux (lunettes) sont différents → score max 0.3
RÈGLE ABSOLUE : Si le style de cheveux est très différent → score max 0.5

Score minimum requis : 0.8

Retourne un JSON :
{{
    "score": 0.85,
    "face_detected": true/false,
    "skin_tone_match": true/false,
    "hair_match": true/false,
    "accessories_match": true/false,
    "facial_features_match": true/false,
    "similarities": ["points communs détaillés"],
    "differences": ["différences détaillées"],
    "critical_failures": ["raisons bloquantes si score < 0.8"],
    "comments": "analyse détaillée"
}}
"""

print("📝 PROMPT RESSEMBLANCE :")
print(resemblance_prompt)
print()

resemblance = validator.validate_resemblance(result['filepath'])
print("📊 RÉSULTAT RESSEMBLANCE :")
print(json.dumps(resemblance, indent=2, ensure_ascii=False))

# 3. COPIE RÉFÉRENCE
print(f"\n{'='*70}")
print("🔍 TEST 3 : DÉTECTION COPIE RÉFÉRENCE")
print("-"*70)

ref_copy = validator.check_reference_copy(result['filepath'])
print("📊 RÉSULTAT COPIE REF :")
print(json.dumps(ref_copy, indent=2, ensure_ascii=False))

# 4. NOMBRE PERSONNES
print(f"\n{'='*70}")
print("🔍 TEST 4 : NOMBRE DE PERSONNES")
print("-"*70)

people = validator.check_people_count(result['filepath'], expected_count=1)
print("📊 RÉSULTAT NB PERSONNES :")
print(json.dumps(people, indent=2, ensure_ascii=False))

# RÉSUMÉ FINAL
print(f"\n{'='*70}")
print("RÉSUMÉ FINAL")
print("="*70)

validation_overall = validator.validate_image_v2(
    image_path=result['filepath'],
    scene_id=2,
    scenario=scenario
)

print(f"\n✅ Qualité : {quality['score']:.2f} {'PASS' if quality['passed'] else 'FAIL'}")
print(f"✅ Ressemblance : {resemblance['score']:.2f} {'PASS' if resemblance['passed'] else 'FAIL'}")
print(f"✅ Pas copie ref : {'PASS' if not ref_copy['is_copy'] else 'FAIL'}")
print(f"✅ Nb personnes : {people['detected']}/{people['expected']} {'PASS' if people['valid'] else 'FAIL'}")
print(f"\n🎯 VALIDATION GLOBALE : {'✅ PASS' if validation_overall['overall_passed'] else '❌ FAIL'}")

# Sauvegarder tous les résultats
with open(f"{OUTPUT_DIR}/validation_results.json", "w", encoding="utf-8") as f:
    json.dump({
        "generation_prompt": positive_prompt,
        "quality": quality,
        "resemblance": resemblance,
        "ref_copy": ref_copy,
        "people": people,
        "overall": validation_overall
    }, f, indent=2, ensure_ascii=False)

print(f"\n💾 Résultats sauvegardés dans {OUTPUT_DIR}/validation_results.json")
print(f"💾 Prompt de génération dans {OUTPUT_DIR}/prompt_generation.txt")
print(f"💾 Image générée : {result['filepath']}")
