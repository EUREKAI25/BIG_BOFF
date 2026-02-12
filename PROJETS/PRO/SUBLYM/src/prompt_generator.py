"""
PROMPT GENERATOR — Génère des prompts narratifs pour Gemini
Transforme les données structurées du scénario en texte narratif en anglais
"""

PROMPT_RULES = """
RÈGLES DE GÉNÉRATION DE PROMPT :

1. STRUCTURE NARRATIVE (pas de liste !)
   - Raconter une scène, pas énumérer des critères
   - Phrases fluides et naturelles en anglais

2. ORDRE DE PRÉSENTATION
   a) DÉCOR : Décrire l'environnement d'abord
   b) PERSONNAGE : Ce qu'il fait, porte, ressent
   c) STYLE VISUEL : Cadrage, lumière, couleurs
   d) INSTRUCTIONS TECHNIQUES : Qualité photo, contraintes

3. CENTRÉ SUR LE PERSONNAGE
   - "This person is at [location]..."
   - "They are [action]..."
   - "They wear [outfit]..."

4. PAS DE MENTION DU RÊVE
   - Ne JAMAIS écrire "dream", "ideal representation", "rêve"
   - Décrire directement comment on met en scène l'utilisateur 

5. TOUT EN ANGLAIS
   - Traduire tous les éléments français
   - Utiliser un vocabulaire naturel

6. DÉCOR VISUEL DÉTAILLÉ
   - Décrire l'environnement de manière visuelle et concrète
   - Intégrer les éléments de l'imaginaire collectif naturellement sans jamais tomber dans la caricature
"""


# translate_simple() supprimée - inutile car toutes les données sont déjà en anglais


def generate_scene_description(lieu: str, imaginaire: str, moment: str, atmosphere: str, scene_id: int, gender: str = "person", keyframe_type: str = "start") -> str:
    """
    Génère la description narrative du décor.

    Règle : Décrire l'environnement de manière visuelle, sans mentionner le "rêve".
    Format instruction : "Put this man/woman at..."
    Les données sont déjà en anglais (générées par le pipeline).

    Args:
        gender: "male" → "this man", "female" → "this woman", autre → "this person"
    """
    # Déterminer le pronom selon le genre
    if gender == "male":
        person_ref = "this man"
    elif gender == "female":
        person_ref = "this woman"
    else:
        person_ref = "this person"

    if scene_id == 1:
        # Scène 1 : Préparatifs (pas encore dans le lieu de rêve)
        if keyframe_type == "end":
            # Keyframe END : même décor, on ne répète pas
            return f"Same environment."
        else:
            return f"Put {person_ref} at {lieu}. It is {moment}."

    # Scènes suivantes : Extraire l'essentiel de l'imaginaire
    # Règle : Simplifier au maximum, juste le concept principal

    # Déterminer le lieu principal depuis l'imaginaire ou le lieu_precis
    if "Maldives" in imaginaire or "Maldives" in lieu:
        location_essence = "an iconic villa in the Maldives"
    elif "overwater villa" in imaginaire.lower():
        location_essence = "a luxurious overwater villa"
    elif "Paris" in imaginaire or "Paris" in lieu:
        location_essence = "a romantic location in Paris"
    elif "beach" in imaginaire.lower() or "plage" in imaginaire.lower():
        location_essence = "a beautiful beach"
    else:
        # Générique : prendre juste le premier segment avant le point
        first_sentence = imaginaire.split(".")[0] if "." in imaginaire else imaginaire
        # Nettoyer les formules d'introduction
        for intro in ["The iconic image of ", "The quintessential vision of ", "The ideal representation of "]:
            if first_sentence.startswith(intro):
                first_sentence = first_sentence[len(intro):]
                break
        location_essence = first_sentence.strip()

    clean_imaginaire = location_essence

    # Keyframe END : si même décor, ne pas répéter
    if keyframe_type == "end":
        return f"Same environment."

    # Keyframe START : description complète
    return f"""Put {person_ref} in this environment: {clean_imaginaire}.

Specifically, {person_ref} is at {lieu}. It is {moment}. The atmosphere is {atmosphere}."""


def generate_person_description(tenue: dict, position: str, geste: str, emotion: str, interaction: str, gender: str = "person") -> str:
    """
    Génère la description narrative de ce que fait/porte le personnage.

    Règle : Phrases fluides, pas de liste. Action + tenue + émotion intégrées.
    Les données sont déjà en anglais (générées par le pipeline).

    Args:
        tenue: Dict avec 'vetements' et 'accessories' (objets Tenue du pipeline)
    """
    # Construire description de la tenue depuis l'objet structuré
    vetements_parts = []
    if isinstance(tenue, dict):
        # Nouveau format : objet Tenue avec vetements/accessories
        vetements = tenue.get('vetements', {})
        accessories = tenue.get('accessories', {})

        vetements_parts = list(vetements.values())
        if accessories:
            vetements_parts.extend(accessories.values())

        tenue_str = ", ".join(vetements_parts) if vetements_parts else "casual clothing"
    else:
        # Ancien format : string directe (rétrocompatibilité)
        tenue_str = str(tenue)

    # Déterminer le pronom selon le genre
    if gender == "male":
        person_ref = "This man"
        pronoun = "He"
        possessive = "His"
    elif gender == "female":
        person_ref = "This woman"
        pronoun = "She"
        possessive = "Her"
    else:
        person_ref = "This person"
        pronoun = "They"
        possessive = "Their"

    # Composer le texte narratif (données déjà en anglais)
    description = f"{person_ref} is {position}. {geste.capitalize()}. {pronoun} wears {tenue_str}."

    # Ajouter émotion si présente
    if emotion and emotion not in ['N/A', 'None', '']:
        description += f" {possessive} expression shows {emotion}."

    # Ajouter interaction si présente
    if interaction and interaction not in ['N/A', 'None', '']:
        description += f" {interaction.capitalize()}."

    return description


def generate_visual_style(cadrage: dict, palette: dict, palette_globale: dict = None) -> str:
    """Génère la description du style visuel avec palette complète (au moins 4 couleurs)."""
    lighting_map = {
        'chaude': 'warm',
        'froide': 'cold',
        'neutre': 'neutral',
        'warm': 'warm',
        'cold': 'cold',
        'neutral': 'neutral',
    }

    saturation_map = {
        'haute': 'high',
        'moyenne': 'medium',
        'basse': 'low',
        'high': 'high',
        'medium': 'medium',
        'low': 'low',
    }

    lighting = lighting_map.get(palette['lumiere'], palette['lumiere'])
    saturation = saturation_map.get(palette['saturation'], palette['saturation'])

    # Construire palette de couleurs (minimum 4)
    colors = [palette['dominante'], palette['accent']]

    # Ajouter couleurs de la palette globale si disponible
    if palette_globale:
        for color_key in ['principale', 'secondaire', 'neutre']:
            color = palette_globale.get(color_key)
            if color and color not in colors:
                colors.append(color)

    # Limiter à 4 couleurs max pour le prompt
    colors = colors[:4]

    # Formater la palette
    if len(colors) >= 4:
        color_desc = f"primary {colors[0]}, secondary {colors[1]}, accent {colors[2]}, neutral {colors[3]}"
    elif len(colors) == 3:
        color_desc = f"primary {colors[0]}, secondary {colors[1]}, accent {colors[2]}"
    else:
        color_desc = f"dominated by {colors[0]}, accent color {colors[1]}"

    return f"{cadrage['type_plan']}, {cadrage['angle']} angle. {lighting} lighting with {saturation} saturation. Color palette: {color_desc}."


def generate_technical_instructions() -> str:
    """Génère les instructions techniques pour Gemini."""
    return """Photo-realistic, cinematic quality, professional photography.
FACE CLEARLY VISIBLE (not from behind, not obscured).
CRITICAL RULES (MANDATORY):
- MOUTH COMPLETELY CLOSED. NO TEETH VISIBLE AT ALL. Teeth showing is ABSOLUTELY FORBIDDEN.
- NEVER looking at camera. Eyes must look away, to the side, at the horizon, or down. NO eye contact with viewer.
- Serene, peaceful, relaxed expression.
- Natural candid moment, not posed for camera.
Cinematic composition, depth of field, paradise atmosphere."""


def generate_prompt(scene_id: int, params: dict, kf_data: dict, palette: dict, cadrage: dict, imaginaire: dict, gender: str = "person", palette_globale: dict = None, keyframe_type: str = "start") -> str:
    """
    Génère un prompt narratif complet pour Gemini.

    Applique les règles de génération pour créer un texte fluide en anglais,
    centré sur le personnage, qui raconte la scène.

    Args:
        scene_id: ID de la scène
        params: Paramètres de la scène (lieu, moment, tenue_protagoniste)
        kf_data: Données du keyframe (position, émotion, geste, interaction)
        palette: Palette de couleurs
        cadrage: Type de plan et angle
        imaginaire: Données imaginaire collectif (pour scènes 2+)
        gender: Genre utilisateur ("male", "female", ou autre)

    Returns:
        Prompt narratif en anglais
    """
    # 1. DÉCOR
    scene_desc = generate_scene_description(
        lieu=params['lieu_precis'],
        imaginaire=imaginaire.get('imaginaire', '') if scene_id > 1 else '',
        moment=params['moment'],
        atmosphere=imaginaire.get('atmosphere', '') if scene_id > 1 else '',
        scene_id=scene_id,
        gender=gender,
        keyframe_type=keyframe_type
    )

    # 2. PERSONNAGE
    person_desc = generate_person_description(
        tenue=params['tenue_protagoniste'],
        position=kf_data['position_protagoniste'],
        geste=kf_data['geste'],
        emotion=kf_data['emotion'],
        interaction=kf_data['interaction'],
        gender=gender
    )

    # 3. STYLE VISUEL
    visual_style = generate_visual_style(cadrage, palette, palette_globale)

    # 4. INSTRUCTIONS TECHNIQUES
    technical = generate_technical_instructions()

    # ASSEMBLER LE PROMPT
    prompt = f"""{scene_desc}

{person_desc}

{visual_style}

{technical}"""

    return prompt.strip()


def validate_prompt_rules(prompt: str) -> dict:
    """
    Valide qu'un prompt respecte les règles de génération avec scoring.

    Returns:
        {
            "score": float (0-100),
            "criteria": {
                "narrative_structure": {"passed": bool, "weight": int},
                "no_dream_mention": {"passed": bool, "weight": int},
                "person_centered": {"passed": bool, "weight": int},
                "technical_instructions": {"passed": bool, "weight": int}
            },
            "valid": bool
        }
    """
    criteria = {}

    # Critère 1 : Structure narrative (pas de listes) - poids 25%
    has_lists = prompt.count('\n-') > 2 or prompt.count('\n  -') > 2
    criteria["narrative_structure"] = {
        "passed": not has_lists,
        "weight": 25
    }

    # Critère 2 : Pas de mention du rêve - poids 20%
    dream_words = ['dream', 'rêve', 'idéal', 'ideal representation']
    has_dream = any(word in prompt.lower() for word in dream_words)
    criteria["no_dream_mention"] = {
        "passed": not has_dream,
        "weight": 20
    }

    # Critère 3 : Centré sur le personnage - poids 30%
    person_centered = ('this person' in prompt.lower() or 'this man' in prompt.lower() or
                      'this woman' in prompt.lower() or 'they' in prompt.lower())
    criteria["person_centered"] = {
        "passed": person_centered,
        "weight": 30
    }

    # Critère 4 : Instructions techniques présentes - poids 25%
    required = ['photo-realistic', 'face clearly visible']
    tech_instructions = all(instr.lower() in prompt.lower() for instr in required)
    criteria["technical_instructions"] = {
        "passed": tech_instructions,
        "weight": 25
    }

    # Calcul du score
    score = sum(c["weight"] for c in criteria.values() if c["passed"])

    return {
        "score": score,
        "criteria": criteria,
        "valid": score >= 80  # Seuil de validation à 80%
    }
