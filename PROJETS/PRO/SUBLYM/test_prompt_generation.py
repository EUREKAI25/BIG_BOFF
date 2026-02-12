"""Test de génération de prompt pour vérifier la qualité"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from prompt_generator import generate_prompt, validate_prompt_rules

# Charger le scénario
scenario_path = "scenario_v8_20260211_221456.json"
with open(scenario_path, "r", encoding="utf-8") as f:
    scenario = json.load(f)

# Tester la génération pour scène 1
scene_id = 1

# Récupérer les données
params = None
keyframe = None
palette = None
cadrage = None

for p in scenario.get("parametres_scenes", []):
    if p.get("scene_id") == scene_id:
        params = p
        break

for k in scenario.get("keyframes", []):
    if k.get("scene_id") == scene_id:
        keyframe = k
        break

for pal in scenario.get("palettes_scenes", []):
    if pal.get("scene_id") == scene_id:
        palette = pal
        break

for cad in scenario.get("cadrages", []):
    if cad.get("scene_id") == scene_id:
        cadrage = cad
        break

kf_data = keyframe.get("start")
imaginaire = scenario.get('imaginaire_collectif', {})
user_profile = scenario.get('metadata', {}).get('user_profile', {})
gender = user_profile.get('gender', 'person')
palette_globale = scenario.get('palette_globale', {})

# Générer le prompt
print("="*70)
print(f"PROMPT COMPLET GÉNÉRÉ POUR SCÈNE {scene_id}")
print("="*70)

prompt = generate_prompt(
    scene_id=scene_id,
    params=params,
    kf_data=kf_data,
    palette=palette,
    cadrage=cadrage,
    imaginaire=imaginaire,
    gender=gender,
    palette_globale=palette_globale,
    keyframe_type="start"
)

print(prompt)

print("\n" + "="*70)
print("VALIDATION DU PROMPT")
print("="*70)

validation = validate_prompt_rules(prompt)
print(f"Score: {validation['score']}/100")
print(f"Valide: {'✅' if validation['valid'] else '❌'}")
print("\nCritères:")
for criterion, data in validation['criteria'].items():
    status = "✅" if data['passed'] else "❌"
    print(f"  {status} {criterion}: {data['weight']}%")
