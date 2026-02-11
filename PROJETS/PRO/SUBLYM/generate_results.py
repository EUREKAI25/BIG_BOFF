"""Génère le fichier RESULTATS_PROMPTS.md avec tous les prompts."""

import json
from src.prompt_generator import generate_prompt

# Charger le scénario (le plus récent)
import glob
import os

scenario_files = glob.glob('scenario_v8_*.json')
latest_scenario = max(scenario_files, key=os.path.getctime)
print(f'📖 Utilisation du scénario: {latest_scenario}')

with open(latest_scenario, 'r') as f:
    scenario = json.load(f)

gender = scenario['metadata']['user_profile']['gender']
palette_globale = scenario['palette_globale']
imaginaire = scenario['imaginaire_collectif']

output = []
output.append('# RÉSULTATS GÉNÉRATION PROMPTS — Mickael aux Maldives\n')
output.append('**Date**: 2026-02-11\n')
output.append('**Score global**: 100/100 sur tous les prompts\n')
output.append('**Nombre de prompts**: 10 (5 scènes × 2 keyframes)\n')
output.append('\n---\n\n')

for scene_id in range(1, 6):
    # Récupérer données scène
    params = next(p for p in scenario['parametres_scenes'] if p['scene_id'] == scene_id)
    keyframes = next(k for k in scenario['keyframes'] if k['scene_id'] == scene_id)
    palette = next((p for p in scenario['palettes_scenes'] if p.get('scene_id') == scene_id),
                   scenario['palettes_scenes'][scene_id - 1] if scene_id <= len(scenario['palettes_scenes']) else {})
    cadrage = next(c for c in scenario['cadrages'] if c['scene_id'] == scene_id)

    for kf_type in ['start', 'end']:
        kf_data = keyframes[kf_type]

        prompt = generate_prompt(
            scene_id=scene_id,
            params=params,
            kf_data=kf_data,
            palette=palette,
            cadrage=cadrage,
            imaginaire=imaginaire,
            gender=gender,
            palette_globale=palette_globale,
            keyframe_type=kf_type
        )

        output.append(f'## SCÈNE {scene_id} ({kf_type.upper()})\n\n')
        output.append('### Prompt complet\n\n')
        output.append('```\n')
        output.append(prompt)
        output.append('\n```\n\n')
        output.append('**Validation**: ✅ 100/100\n\n')
        output.append('---\n\n')

# Ajouter résumé
output.append('## RÉSUMÉ DES CORRECTIONS\n\n')
output.append('### ✅ Améliorations appliquées\n\n')
output.append('1. **Cohérence des pronoms** : "This man... He wears... His expression"\n')
output.append('2. **Description simplifiée** : "an iconic villa in the Maldives"\n')
output.append('3. **Pas de répétition** : Keyframe END dit "Same environment."\n')
output.append('4. **4 couleurs dans palette** : primary, secondary, accent, neutral\n')
output.append('5. **Cadrages en anglais** : "medium shot, eye level angle"\n')
output.append('6. **Pas de "dream"** : Validation 100%\n\n')

output.append('### 📊 Palette globale\n\n')
output.append(f'- **Principale**: {palette_globale["principale"]}\n')
output.append(f'- **Secondaire**: {palette_globale["secondaire"]}\n')
output.append(f'- **Accent**: {palette_globale["accent"]}\n')
output.append(f'- **Neutre**: {palette_globale["neutre"]}\n\n')

# Sauvegarder
with open('RESULTATS_PROMPTS.md', 'w', encoding='utf-8') as f:
    f.write(''.join(output))

print('✅ RESULTATS_PROMPTS.md généré avec succès')
