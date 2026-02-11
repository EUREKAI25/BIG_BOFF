"""
SCENARIO AGENT v8 - BATCH OPTIMIZED
- 9 appels LLM au lieu de 168 (réduction 95%)
- Consolidation par batch (toutes scènes traitées ensemble)
- Validation Pydantic (schémas stricts)
- Temps : 1-2min au lieu de 10-15min
- Coût : ~0.15€ au lieu de ~2.70€ (GPT-4o)
"""

import json
import os
import urllib.request
import time
from datetime import datetime
from typing import Any, Optional, List, Dict, Type
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

DEFAULT_CONFIG = {
    "nb_scenes": 5,
    "duree_scene": 6,  # secondes
    "model": "gpt-4o",
    "api_endpoint": "https://api.openai.com/v1/chat/completions",  # Configurable
    "temperature": 0.3,  # Plus bas que v7 (0.7) pour cohérence
    "max_tokens": 8000,  # Plus haut que v7 (4000) pour batch
    "max_retries": 7,
}

# =============================================================================
# RÈGLES DE PRODUCTION
# =============================================================================

PRODUCTION_RULES = """
RÈGLES DE PRODUCTION VIDÉO (à respecter TOUJOURS):

## RÈGLES TECHNIQUES (contraintes IA)
- Mouvements lents à modérés (l'IA génère des artefacts sur mouvements rapides)
- Pas de rotation caméra rapide
- Éviter les foules denses
- Max 2 personnages principaux par plan
- Pas de texte lisible dans le cadre
- Éviter reflets complexes (miroirs, eau agitée)
- Préférer éclairage naturel diffus

## RÈGLES PERSONNAGES
- Pas de demi-tour des personnages
- Expressions positives uniquement (sérénité,joie, tendresse, émerveillement, complicité)
- JAMAIS d'air triste, inquiet, effrayé, en colère
- Figurants floutés / hors focus (seuls protagonistes nets)
- Pas de gros plan visage (révèle l'artifice IA)
- Vue de dos = brève uniquement, jamais scène entière
- Pas de dos prolongé à la caméra
- Expressions faciales naturelles, pas exagérées
- Contact visuel entre personnages = connexion
- Gestes cohérents avec l'émotion
- Proximité physique progressive (en cas de romance et sauf contre-ordre explicite)

## RÈGLES CADRAGE
Options autorisées (ALL IN ENGLISH):
- extreme wide shot: établir le lieu
- wide shot: action dans l'environnement
- medium shot: dialogue, interaction
- cowboy shot: personnage en action
- medium close-up: émotion sans gros plan visage
- PAS de close-up visage, PAS de extreme close-up

Mouvements caméra autorisés (ALL IN ENGLISH):
- static: stabilité, contemplation
- slow push in: entrer dans l'intimité
- slow pull out: révéler le contexte
- slow lateral tracking: accompagner le mouvement
- slow pan: découverte du lieu
- subtle handheld: authenticité

Angles (ALL IN ENGLISH):
- eye level: neutre, identification
- slight high angle: vulnérabilité, tendresse
- slight low angle: puissance, admiration

## RÈGLES NARRATIVES
- **SCÈNE 1 OBLIGATOIRE : PRÉPARATIFS / MOMENT DE BASCULE**
  - C'est le moment où le rêve commence à se concrétiser
  - Exemples : s'entraîner, s'habiller, préparer sa valise, être à l'aéroport, acheter quelque chose en ligne etc
  - Action concrète qui marque le passage de l'intention à la réalisation
  - Cette scène montre la DÉCISION et le DÉBUT de l'aventure
- **SCÈNES 2-N : ACCOMPLISSEMENT DU RÊVE**
  - L'utilisateur est DÉJÀ dans le lieu/situation du rêve dès la scène 2
  - L'ACCOMPLISSEMENT du rêve doit arriver AU MAXIMUM à la MOITIÉ du scénario (règle absolue)
  - Pas de voyage progressif (pas de scènes aéroport/avion/trajet sauf si c'est le rêve lui-même)
  - Exemple : Scène 1 = réservation, Scène 2 = DÉJÀ aux Maldives, vivant le rêve
- Chaque scène a un objectif émotionnel clair
- Progression d'intensité émotionnelle
- Pas de scène sans lien avec l'objectif du rêve
- **RESSENTIS CONCRETS** : traduire les émotions en actions physiques visibles
  - PAS "feeling excited" MAIS "jumps with joy, claps hands"
  - PAS "feeling nervous" MAIS "fidgets with hands, takes deep breath"
  - PAS "feeling awe" MAIS "stops walking, mouth opens, eyes widen"

## RÈGLES COHÉRENCE VISUELLE
- Palette couleurs cohérente sur toute la vidéo
- Tenues vestimentaires cohérentes dans le temps
- Éclairage cohérent avec l'heure indiquée
- Météo constante sauf indication contraire

## RÈGLES RYTHME
- DURÉES AUTORISÉES : UNIQUEMENT 6s ou 10s (contrainte MiniMax)
- Combinaisons possibles pour durée totale souhaitée :
  * 30s = 5×6s ou 3×10s
  * 60s = 10×6s ou 6×10s ou mix (ex: 4×6s + 2×10s + 1×6s)
- Choisir durées selon intensité de la scène (6s=action rapide, 10s=contemplation)
- Pas de scène < 6s
- Pas d'action statique > 8s

## RÈGLES FORMAT RÉPONSE
- Format instruction impératif pour mise en scène
- "Put this man/woman at [location]..."
- "This person is [action]..."
- JAMAIS de "vous", "Visualisez-vous", "Imaginez"
- Descriptions factuelles et précises
- Pas de répétition entre scènes
"""

PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.010},  # $0.0025/1K input, $0.010/1K output
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # $0.00015/1K input, $0.0006/1K output
    # Autres modèles (hors pipeline) :
    # Gemini 3 Pro: $0.04/image (fal-ai/gemini-3-pro-image-preview)
    # MiniMax video-01: $0.10/vidéo
}

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class BlocagesEmotionnels(BaseModel):
    blocages: List[str] = Field(..., min_items=3, max_items=5)
    affirmations: List[str] = Field(..., min_items=3, max_items=5)

class Scene(BaseModel):
    id: int = Field(..., ge=1, le=10)
    titre: str = Field(..., min_length=5, max_length=100)
    de: str = Field(..., min_length=5, max_length=200, description="État émotionnel initial")
    vers: str = Field(..., min_length=5, max_length=200, description="État émotionnel final")
    action: str = Field(..., min_length=10, max_length=300)

class Tenue(BaseModel):
    """Structure détaillée d'une tenue vestimentaire."""
    vetements: Dict[str, str] = Field(..., description="Ex: {'haut': 'white linen shirt', 'bas': 'beige shorts', 'chaussures': 'sandals'}")
    accessories: Dict[str, str] = Field(default_factory=dict, description="Ex: {'lunettes': 'sunglasses', 'chapeau': 'straw hat'}")

class SceneParams(BaseModel):
    scene_id: int
    lieu_precis: str = Field(..., min_length=10, max_length=200)
    moment: str = Field(..., pattern=r"(morning|midday|afternoon|evening|night)", description="Time of day in English")
    action: str = Field(..., min_length=20, max_length=300)
    tenue_protagoniste: Tenue
    tenue_partenaire: Optional[Tenue] = Field(default=None, description="None si scène solo")

class Keyframe(BaseModel):
    position_protagoniste: str
    position_partenaire: str
    emotion: str
    geste: str
    interaction: str

class SceneKeyframes(BaseModel):
    scene_id: int
    start: Keyframe
    end: Keyframe

class ScenePitch(BaseModel):
    scene_id: int
    pitch: str = Field(..., min_length=50, max_length=500)
    attitude_protagoniste: str
    attitude_partenaire: str
    deplacement: str
    interaction_continue: str

class Palette(BaseModel):
    dominante: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    lumiere: str = Field(..., pattern=r"(chaude|froide|neutre)")
    saturation: str = Field(..., pattern=r"(haute|moyenne|basse)")

class PaletteGlobale(BaseModel):
    """Palette globale limitée à 4 couleurs maximum."""
    principale: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    secondaire: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    neutre: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")

class SceneCadrage(BaseModel):
    scene_id: int
    type_plan: str
    justification_plan: str
    mouvement_camera: str
    justification_mouvement: str
    angle: str
    justification_angle: str

class SceneDuree(BaseModel):
    scene_id: int
    duree: int = Field(..., description="UNIQUEMENT 6 ou 10 (contrainte MiniMax)")
    justification: str

    @validator('duree')
    def validate_duree(cls, v):
        if v not in [6, 10]:
            raise ValueError("Durée doit être UNIQUEMENT 6s ou 10s (contrainte MiniMax)")
        return v

class Rythme(BaseModel):
    duree_totale: int
    scenes: List[SceneDuree]

class PromptVideo(BaseModel):
    scene_id: int
    prompt: str = Field(..., min_length=100, max_length=2000)

# =============================================================================
# AUDIT LOG
# =============================================================================

class AuditLog:
    def __init__(self):
        self.entries: List[str] = []
        self.start_time = datetime.now()

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.entries.append(entry)
        print(entry)

    def section(self, title: str):
        separator = "═" * 70
        self.entries.append("")
        self.entries.append(separator)
        self.entries.append(f"  {title}")
        self.entries.append(separator)
        print(f"\n{separator}")
        print(f"  {title}")
        print(separator)

    def subsection(self, title: str):
        separator = "━" * 70
        self.entries.append("")
        self.entries.append(separator)
        self.entries.append(f"📌 {title}")
        self.entries.append(separator)
        print(f"\n{separator}")
        print(f"📌 {title}")
        print(separator)

    def detail(self, key: str, value: Any):
        value_str = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
        entry = f"   {key}: {value_str}"
        self.entries.append(entry)
        print(entry)

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"SCENARIO AGENT v8 - BATCH OPTIMIZED - AUDIT LOG\n")
            f.write(f"Généré le: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Durée: {(datetime.now() - self.start_time).seconds}s\n")
            f.write("=" * 80 + "\n\n")
            f.write("\n".join(self.entries))


# =============================================================================
# LLM CLIENT
# =============================================================================

class LLM:
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.3, max_tokens: int = 8000, api_endpoint: str = "https://api.openai.com/v1/chat/completions"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.api_endpoint = api_endpoint
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.calls = 0
        self.tokens_in = 0
        self.tokens_out = 0
        self.max_retries = 3

    def _call(self, system: str, user: str) -> dict:
        self.calls += 1
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"}
        }

        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(
                    self.api_endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                )

                with urllib.request.urlopen(req, timeout=180) as resp:  # 180s au lieu de 120s
                    result = json.loads(resp.read().decode("utf-8"))

                usage = result.get("usage", {})
                self.tokens_in += usage.get("prompt_tokens", 0)
                self.tokens_out += usage.get("completion_tokens", 0)

                return json.loads(result["choices"][0]["message"]["content"])

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def get_cost(self) -> float:
        pricing = PRICING.get(self.model, PRICING["gpt-4o"])
        return (self.tokens_in / 1000) * pricing["input"] + (self.tokens_out / 1000) * pricing["output"]


# =============================================================================
# SCENARIO GENERATOR BATCH
# =============================================================================

class ScenarioGeneratorBatch:
    def __init__(self, v6_data: dict, config: dict, audit: AuditLog):
        self.v6 = v6_data
        self.config = {**DEFAULT_CONFIG, **config}
        self.audit = audit
        self.llm = LLM(
            self.config.get("model", "gpt-4o"),
            self.config.get("temperature", 0.3),
            self.config.get("max_tokens", 8000),
            self.config.get("api_endpoint", "https://api.openai.com/v1/chat/completions")
        )
        self.scenario = {}

        # Extraire profil utilisateur
        self.user_profile = self._extract_user_profile()

    def _extract_user_profile(self) -> dict:
        """Extrait profil utilisateur depuis session, détecte genre/âge via Vision si nécessaire."""
        user = self.v6.get('user', {})
        profile = {
            'gender': user.get('gender', None),
            'age': user.get('age', None),
            'name': user.get('name', None)
        }

        # Si genre ou âge manquant ET image de référence fournie
        reference_image = self.v6.get('reference_image', None)
        if reference_image and (not profile['gender'] or not profile['age']):
            self.audit.log("🔍 Détection genre/âge depuis photo de référence...")
            detected = self._detect_user_from_image(reference_image)
            if not profile['gender']:
                profile['gender'] = detected.get('gender')
            if not profile['age']:
                profile['age'] = detected.get('age')

        # Normaliser le genre en anglais (male/female) pour cohérence avec le reste
        if profile['gender'] in ['homme', 'male', 'm']:
            profile['gender'] = 'male'
        elif profile['gender'] in ['femme', 'female', 'f']:
            profile['gender'] = 'female'
        else:
            profile['gender'] = 'person'

        # Construire description protagoniste (en anglais)
        if profile['gender'] == 'male':
            desc = f"this {profile['age']}-year-old man" if profile['age'] else "this man"
        elif profile['gender'] == 'female':
            desc = f"this {profile['age']}-year-old woman" if profile['age'] else "this woman"
        else:
            desc = f"this {profile['age']}-year-old person" if profile['age'] else "this person"

        if profile['name']:
            desc += f" named {profile['name']}"

        profile['description'] = desc
        return profile

    def _detect_user_from_image(self, image_path: str) -> dict:
        """Détecte genre et âge depuis photo de référence avec GPT-4o Vision."""
        import base64

        try:
            # Charger et encoder image
            with open(image_path, "rb") as img_file:
                image_b64 = base64.b64encode(img_file.read()).decode('utf-8')

            # Appel GPT-4o Vision
            payload = {
                "model": "gpt-4o",
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyse cette photo et retourne un JSON avec: gender (homme/femme), age (estimation en années). Sois précis."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                        }
                    ]
                }],
                "max_tokens": 100,
                "response_format": {"type": "json_object"}
            }

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.llm.api_key}", "Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                detected = json.loads(result["choices"][0]["message"]["content"])
                self.audit.log(f"   ✅ Détecté: {detected}")
                return detected

        except Exception as e:
            self.audit.log(f"   ⚠️ Erreur détection: {e}")
            return {"gender": None, "age": None}

    def _get_context(self) -> str:
        """Construit le contexte cumulatif."""
        # Extraire rêve (compatibilité ancien/nouveau format)
        dream_text = self.v6.get('dream_input', {}).get('raw', self.v6.get('dream', ''))

        ctx = f"RÊVE: {dream_text}\n\n"
        ctx += f"PROTAGONISTE: {self.user_profile['description']}\n\n"

        if self.scenario.get("blocages_emotionnels"):
            ctx += f"BLOCAGES:\n{json.dumps(self.scenario['blocages_emotionnels'], indent=2, ensure_ascii=False)}\n\n"

        if self.scenario.get("pitch_global"):
            ctx += f"PITCH GLOBAL:\n{self.scenario['pitch_global']}\n\n"

        if self.scenario.get("decoupage"):
            ctx += f"SCÈNES:\n{json.dumps(self.scenario['decoupage'], indent=2, ensure_ascii=False)}\n\n"

        if self.scenario.get("parametres_scenes"):
            ctx += f"PARAMÈTRES:\n{json.dumps(self.scenario['parametres_scenes'], indent=2, ensure_ascii=False)}\n\n"

        if self.scenario.get("keyframes"):
            ctx += f"KEYFRAMES:\n{json.dumps(self.scenario['keyframes'], indent=2, ensure_ascii=False)}\n\n"

        return ctx

    def _ask_batch(self, step: str, user_prompt: str, schema: Type[BaseModel]) -> dict:
        """Question batch avec validation Pydantic."""
        self.audit.subsection(step)
        self.audit.log(f"❓ Génération batch...")

        system = f"""{PRODUCTION_RULES}

Réponds UNIQUEMENT avec un JSON structuré valide.
SCHÉMA ATTENDU : {schema.schema_json(indent=2)}

IMPORTANT :
- Respecte EXACTEMENT le schéma (tous les champs requis)
- Use instruction format: "Put this man/woman at...", "This person is..."
- NEVER use "you", "Visualize yourself", "Imagine"
- Precise and factual descriptions
- Maintain consistency with provided context
- ALL OUTPUT IN ENGLISH (descriptions, locations, actions, emotions, everything)
"""

        max_retries = self.config.get("max_retries", 7)

        for attempt in range(max_retries):
            try:
                self.audit.log(f"🔄 Tentative {attempt + 1}/{max_retries}...")

                response = self.llm._call(system, user_prompt)

                # Validation Pydantic
                validated = schema(**response)

                self.audit.log(f"✅ Validation réussie")
                self.audit.detail("Réponse", validated.dict())

                return validated.dict()

            except Exception as e:
                self.audit.log(f"❌ Erreur : {str(e)[:200]}")

                if attempt < max_retries - 1:
                    # Retry avec feedback
                    user_prompt += f"\n\nERREURS DÉTECTÉES:\n{str(e)}\n\nCORRIGE et régénère un JSON valide."
                else:
                    self.audit.log(f"🚨 ÉCHEC après {max_retries} tentatives")
                    raise

    # =========================================================================
    # ÉTAPES DE GÉNÉRATION BATCH
    # =========================================================================

    def step1_blocages_pitch(self):
        """Génère blocages + affirmations + pitch global (1 appel)."""
        self.audit.section("ÉTAPE 1: BLOCAGES + PITCH GLOBAL")

        prompt = f"""
CONTEXTE:
{self._get_context()}

TÂCHE 1 : BLOCAGES ÉMOTIONNELS
Identifie 3-5 BLOCAGES ÉMOTIONNELS que ce rêve pourrait soulever.
Exemples : "pas assez belle", "je ne mérite pas", "peur de l'abandon"

Pour chaque blocage, génère l'AFFIRMATION POSITIVE opposée (20 caractères maximum).
Exemples : "je mérite l'amour", "je suis prête", "je suis belle"

TÂCHE 2 : PITCH GLOBAL
Écris un PITCH GLOBAL narratif détaillé du scénario en {self.config['nb_scenes']} scènes.
Description complète de l'arc narratif, du début à l'accomplissement du rêve.
Use instruction format: "Put this person at...", "This person is...", NEVER "you".

GÉNÈRE un JSON avec :
{{
    "blocages": ["blocage 1", "blocage 2", ...],
    "affirmations": ["affirmation 1", "affirmation 2", ...],
    "pitch_global": "Le pitch narratif complet..."
}}
"""

        class BlocagesPitch(BaseModel):
            blocages: List[str] = Field(..., min_items=3, max_items=5)
            affirmations: List[str] = Field(..., min_items=3, max_items=5)
            pitch_global: str = Field(..., min_length=100, max_length=1000)

        result = self._ask_batch("1. Blocages + Pitch", prompt, BlocagesPitch)

        self.scenario["blocages_emotionnels"] = {
            "blocages": result["blocages"],
            "affirmations": result["affirmations"]
        }
        self.scenario["pitch_global"] = result["pitch_global"]

    def step1b_imaginaire_collectif(self):
        """Génère l'imaginaire collectif / représentation archétypale du rêve (1 appel)."""
        self.audit.section("ÉTAPE 1B: IMAGINAIRE COLLECTIF")

        # Extraire le rêve brut
        dream_text = self.v6.get('dream_input', {}).get('raw', self.v6.get('dream', ''))

        prompt = f"""
CONTEXTE:
RÊVE: {dream_text}
PROTAGONISTE: {self.user_profile['description']}

TÂCHE : IMAGINAIRE COLLECTIF

Quelle est la REPRÉSENTATION ARCHÉTYPALE, CARTE POSTALE, IDÉALE de ce rêve ?

Décris l'imaginaire collectif que ce rêve évoque :

1. VISUEL ICONIQUE :
   - Quelles sont les images, couleurs, éléments visuels qui viennent immédiatement à l'esprit ?
   - Quelle est la "carte postale parfaite" de ce rêve ?

2. ÉLÉMENTS CLÉS :
   - Liste 5-8 éléments visuels essentiels qui DOIVENT apparaître
   - Ce qui rend cette représentation immédiatement reconnaissable

3. ATMOSPHÈRE :
   - L'émotion, l'ambiance, le "feeling" recherché
   - Les adjectifs qui définissent ce paradis

Exemples :
- Maldives → eau turquoise cristalline, sable blanc immaculé, palmiers, ciel bleu parfait, maison sur pilotis luxueuse
- Paris romantique → Tour Eiffel au coucher du soleil, Seine scintillante, café avec terrasse, lumières dorées
- New York → gratte-ciels illuminés, taxis jaunes, Times Square, skyline majestueux

GÉNÈRE un JSON avec :
{{
    "imaginaire": "Description riche et détaillée de la représentation parfaite (200-400 caractères)",
    "elements_cles": ["élément 1", "élément 2", ..., "élément 5-8"],
    "atmosphere": "Liste d'adjectifs séparés par des virgules"
}}
"""

        class ImaginaireCollectif(BaseModel):
            imaginaire: str = Field(..., min_length=200, max_length=400)
            elements_cles: List[str] = Field(..., min_items=5, max_items=8)
            atmosphere: str = Field(..., min_length=20, max_length=200)

        result = self._ask_batch("1b. Imaginaire collectif", prompt, ImaginaireCollectif)

        self.scenario["imaginaire_collectif"] = result

    def step2_decoupage(self):
        """Découpe en scènes (1 appel)."""
        self.audit.section("ÉTAPE 2: DÉCOUPAGE EN SCÈNES")

        nb = self.config["nb_scenes"]

        prompt = f"""
CONTEXTE:
{self._get_context()}

Découpe le scénario en exactement {nb} scènes.

Pour chaque scène, définis :
- id : numéro de scène (1 à {nb})
- titre : titre court de la scène
- de : état émotionnel/situation de départ
- vers : état émotionnel/situation d'arrivée
- action : que se passe-t-il concrètement

IMPORTANT :
- **SCÈNE 1 OBLIGATOIRE = PRÉPARATIFS / MOMENT DE BASCULE**
  - La scène 1 DOIT montrer le moment où le rêve commence à se concrétiser
  - Exemples : s'entraîner, s'habiller, réserver un billet (avion/train), préparer sa valise, être à l'aéroport/gare,
    acheter quelque chose en ligne, faire une démarche administrative, s'inscrire à quelque chose
  - C'est l'ACTION CONCRÈTE qui marque le passage de l'intention à la réalisation
  - Cette scène montre la DÉCISION et le DÉBUT de l'aventure
- Chronologie respectée
- Progression émotionnelle claire
- Chaque scène a un lien avec l'objectif du rêve
- Transitions logiques entre scènes
- PAS de détails de décor (ce sera fait à l'étape suivante)

EXEMPLE pour "Je rêve d'aller à Rio" :
{{
    "scenes": [
        {{
            "id": 1,
            "titre": "Réservation du voyage",
            "de": "Hésitation, rêve lointain",
            "vers": "Excitation, décision prise",
            "action": "Protagoniste devant son ordinateur, clique sur 'Réserver' pour un billet d'avion vers Rio. Sourire d'émerveillement en validant le paiement."
        }},
        {{
            "id": 2,
            "titre": "À l'aéroport",
            "de": "Excitation nerveuse",
            "vers": "Aventure commence",
            "action": "Protagoniste à l'aéroport avec sa valise, regarde le panneau d'affichage 'Vol Rio de Janeiro', sourire confiant."
        }},
        ...
    ]
}}

GÉNÈRE un JSON avec :
{{
    "scenes": [
        {{
            "id": 1,
            "titre": "Titre scène 1 (PRÉPARATIFS/BASCULE)",
            "de": "État initial",
            "vers": "État suivant",
            "action": "Action concrète de préparation/décision"
        }},
        ...
    ]
}}
"""

        class Decoupage(BaseModel):
            scenes: List[Scene]

        result = self._ask_batch("2. Découpage", prompt, Decoupage)
        self.scenario["decoupage"] = result["scenes"]

    def step3_parametres_batch(self):
        """Paramètres de TOUTES les scènes (1 appel)."""
        self.audit.section("ÉTAPE 3: PARAMÈTRES TOUTES SCÈNES")

        scenes = self.scenario["decoupage"]

        prompt = f"""
CONTEXTE:
{self._get_context()}

Pour CHAQUE scène du découpage, définis les PARAMÈTRES précis :
- lieu_precis : description exacte du lieu (pas juste "Paris", mais "Terrasse café Montmartre, à Paris, table d'angle")
- moment : time of day in ENGLISH (morning/midday/afternoon/evening/night)
- action : description précise de l'action qui se déroule, pertinente avec l'objectif de la scène (lien direct)
- tenue_protagoniste : OBJET structuré avec vetements (dict) et accessories (dict)
- tenue_partenaire : OBJET structuré avec vetements (dict) et accessories (dict), ou null si scène solo

IMPORTANT :
- Cohérence temporelle : si 2 scènes se suivent immédiatement, tenues identiques
- Cohérence spatiale : transitions géographiques logiques
- Cohérence avec le pitch global
- Tenues DOIVENT être des objets avec vetements et accessories

GÉNÈRE un JSON avec :
{{
    "scenes": [
        {{
            "scene_id": 1,
            "lieu_precis": "...",
            "moment": "afternoon",
            "action": "...",
            "tenue_protagoniste": {{
                "vetements": {{"haut": "white linen shirt", "bas": "beige shorts", "chaussures": "sandals"}},
                "accessories": {{"lunettes": "sunglasses", "chapeau": "straw hat"}}
            }},
            "tenue_partenaire": null
        }},
        ...
    ]
}}
"""

        class AllScenesParams(BaseModel):
            scenes: List[SceneParams]

        result = self._ask_batch("3. Paramètres batch", prompt, AllScenesParams)
        self.scenario["parametres_scenes"] = result["scenes"]

    def step4_keyframes_batch(self):
        """Keyframes de TOUTES les scènes (1 appel)."""
        self.audit.section("ÉTAPE 4: KEYFRAMES TOUTES SCÈNES")

        prompt = f"""
CONTEXTE:
{self._get_context()}

Pour CHAQUE scène, définis les KEYFRAMES de début et de fin :
- start : position initiale des personnages, émotion, geste, interaction
- end : position finale des personnages, émotion, geste, interaction

IMPORTANT :
- Positions PHOTOGRAPHIABLES (concrètes et précises)
- Émotions POSITIVES uniquement (joie, tendresse, émerveillement, complicité)
- Pas de gros plan visage
- Transitions cohérentes (end de scène N peut influencer start de scène N+1)
- pas de changement de décor impliquant des déplaements compliqués de la part des personnages

GÉNÈRE un JSON avec :
{{
    "scenes": [
        {{
            "scene_id": 1,
            "start": {{
                "position_protagoniste": "...",
                "position_partenaire": "...",
                "emotion": "...",
                "geste": "...",
                "interaction": "..."
            }},
            "end": {{
                "position_protagoniste": "...",
                "position_partenaire": "...",
                "emotion": "...",
                "geste": "...",
                "interaction": "..."
            }}
        }},
        ...
    ]
}}
"""

        class AllKeyframes(BaseModel):
            scenes: List[SceneKeyframes]

        result = self._ask_batch("4. Keyframes batch", prompt, AllKeyframes)
        self.scenario["keyframes"] = result["scenes"]

    def step5_pitchs_attitudes_batch(self):
        """Pitchs + attitudes de TOUTES les scènes (1 appel)."""
        self.audit.section("ÉTAPE 5: PITCHS + ATTITUDES TOUTES SCÈNES")

        prompt = f"""
CONTEXTE:
{self._get_context()}

Pour CHAQUE scène, génère :
- pitch : narration fluide de la scène (50-500 caractères, style neutre, 3ème personne)
- attitude_protagoniste : attitude corporelle pendant la scène
- attitude_partenaire : attitude corporelle pendant la scène
- deplacement : mouvement dans l'espace (du keyframe start au keyframe end)
- interaction_continue : interaction entre les personnages pendant la scène

IMPORTANT :
- Mouvements LENTS (l'IA vidéo ne gère pas les mouvements rapides)
- PAS de demi-tour
- PAS de "vous" ou "imaginez"
- Cohérence avec les keyframes

GÉNÈRE un JSON avec :
{{
    "scenes": [
        {{
            "scene_id": 1,
            "pitch": "Description narrative de la scène...",
            "attitude_protagoniste": "...",
            "attitude_partenaire": "...",
            "deplacement": "...",
            "interaction_continue": "..."
        }},
        ...
    ]
}}
"""

        class AllPitchs(BaseModel):
            scenes: List[ScenePitch]

        result = self._ask_batch("5. Pitchs + Attitudes batch", prompt, AllPitchs)
        self.scenario["pitchs_attitudes"] = result["scenes"]

    def step6_palettes_batch(self):
        """Palette globale + palettes par scène (1 appel)."""
        self.audit.section("ÉTAPE 6: PALETTES GLOBALE + PAR SCÈNE")

        prompt = f"""
CONTEXTE:
{self._get_context()}

TÂCHE 1 : PALETTE GLOBALE
Définis une PALETTE DE COULEURS GLOBALE pour cette vidéo (5 couleurs en hexa) :
- principale
- secondaire
- accent
- neutre_clair
- neutre_fonce

Cohérente avec : lieu, ambiance, heure de la journée.

TÂCHE 2 : PALETTES PAR SCÈNE
Pour CHAQUE scène, décline la palette globale en ajustant selon :
- Moment de la scène (matin/soir/nuit)
- Lieu spécifique
- Ambiance émotionnelle

Pour chaque scène :
- dominante : couleur hexa
- accent : couleur hexa
- lumiere : chaude/froide/neutre
- saturation : haute/moyenne/basse

GÉNÈRE un JSON avec :
{{
    "palette_globale": {{
        "principale": "#RRGGBB",
        "secondaire": "#RRGGBB",
        "accent": "#RRGGBB",
        "neutre_clair": "#RRGGBB",
        "neutre_fonce": "#RRGGBB"
    }},
    "scenes": [
        {{
            "scene_id": 1,
            "dominante": "#RRGGBB",
            "accent": "#RRGGBB",
            "lumiere": "chaude",
            "saturation": "moyenne"
        }},
        ...
    ]
}}
"""

        class AllPalettes(BaseModel):
            palette_globale: PaletteGlobale
            scenes: List[Palette]

            @validator('scenes')
            def add_scene_ids(cls, v):
                for i, pal in enumerate(v):
                    if not hasattr(pal, 'scene_id'):
                        v[i] = {**pal.dict(), 'scene_id': i + 1}
                return v

        # Schéma modifié pour accepter scene_id optionnel
        class ScenePalette(Palette):
            scene_id: int = Field(default=0)

        class AllPalettesWithIds(BaseModel):
            palette_globale: PaletteGlobale
            scenes: List[ScenePalette]

        result = self._ask_batch("6. Palettes batch", prompt, AllPalettesWithIds)

        self.scenario["palette_globale"] = result["palette_globale"]
        self.scenario["palettes_scenes"] = result["scenes"]

    def step7_cadrages_batch(self):
        """Cadrages de TOUTES les scènes (1 appel)."""
        self.audit.section("ÉTAPE 7: CADRAGES TOUTES SCÈNES")

        prompt = f"""
CONTEXTE:
{self._get_context()}

Pour CHAQUE scène, définis le CADRAGE avec JUSTIFICATIONS cinématographiques :
- type_plan : plan large/moyen/américain/rapproché poitrine (PAS de gros plan visage)
- justification_plan : argument cinématographique professionnel
- mouvement_camera : fixe/travelling/panoramique (lent uniquement)
- justification_mouvement : argument cinématographique professionnel
- angle : niveau yeux/plongée/contre-plongée
- justification_angle : argument cinématographique professionnel

IMPORTANT :
- Choix justifiés avec des arguments professionnels
- PAS de gros plan visage (révèle artifice IA)
- Mouvements LENTS uniquement

GÉNÈRE un JSON avec :
{{
    "scenes": [
        {{
            "scene_id": 1,
            "type_plan": "plan moyen",
            "justification_plan": "Permet de voir l'interaction...",
            "mouvement_camera": "travelling avant lent",
            "justification_mouvement": "Renforce l'intimité...",
            "angle": "niveau des yeux",
            "justification_angle": "Identification du spectateur..."
        }},
        ...
    ]
}}
"""

        class AllCadrages(BaseModel):
            scenes: List[SceneCadrage]

        result = self._ask_batch("7. Cadrages batch", prompt, AllCadrages)
        self.scenario["cadrages"] = result["scenes"]

    def step8_rythme(self):
        """Rythme et durée par scène (1 appel)."""
        self.audit.section("ÉTAPE 8: RYTHME")

        duree_totale = self.config["nb_scenes"] * self.config["duree_scene"]
        duree_moy = self.config["duree_scene"]

        prompt = f"""
CONTEXTE:
{self._get_context()}

Répartis la durée totale ({duree_totale}s) entre les {self.config['nb_scenes']} scènes.

Durée moyenne : {duree_moy}s par scène.
Tu peux ajuster ±20% par scène selon l'importance narrative.

Pour chaque scène :
- duree : en secondes (minimum 4s, maximum 20s)
- justification : argument professionnel (pourquoi cette durée)

IMPORTANT :
- La somme DOIT faire exactement {duree_totale}s
- Scène d'ouverture peut être plus longue (immersion)
- Scène finale peut être plus longue (impact)
- Pas de scène < 4s
- Justifications professionnelles

GÉNÈRE un JSON avec :
{{
    "duree_totale": {duree_totale},
    "scenes": [
        {{
            "scene_id": 1,
            "duree": 7,
            "justification": "Scène d'ouverture, immersion nécessaire..."
        }},
        ...
    ]
}}
"""

        result = self._ask_batch("8. Rythme", prompt, Rythme)
        self.scenario["rythme"] = result

    def step9_prompts_finaux_batch(self):
        """Prompts vidéo de TOUTES les scènes + prompt audio (1 appel)."""
        self.audit.section("ÉTAPE 9: PROMPTS FINAUX TOUTES SCÈNES")

        # Déterminer le pronom selon le genre
        if self.user_profile['gender'] == 'male':
            person_ref = "this man"
            pronoun = "he"
            possessive = "his"
        elif self.user_profile['gender'] == 'female':
            person_ref = "this woman"
            pronoun = "she"
            possessive = "her"
        else:
            person_ref = "this person"
            pronoun = "they"
            possessive = "their"

        prompt = f"""
CONTEXTE COMPLET:
{self._get_context()}

Génère les PROMPTS FINAUX optimisés pour génération vidéo IA.

Pour CHAQUE scène, génère un prompt vidéo de 100-2000 caractères intégrant :
- Paramètres (lieu, moment, action, tenues)
- Keyframes (positions start/end, émotions, gestes)
- Attitudes (déplacements, interactions)
- Palette (couleurs dominantes)
- Cadrage (plan, mouvement, angle)

RÈGLES DE STRUCTURE IMPÉRATIVES :
1. **Format de mise en scène** : Use instruction format
   - Start with: "Put {person_ref} at [location]..." or "Put {person_ref} in [environment]..."
   - For scenes 2+: Use concise environment description (e.g., "an iconic villa in the Maldives" instead of long descriptions)

2. **Pronoms cohérents** :
   - Use "{person_ref}" to introduce the person
   - Then use "{pronoun}" (e.g., "{pronoun} wears...", "{possessive} expression shows...")
   - NEVER mix pronouns (no "this man... they...")

3. **Pas de répétition** :
   - NEVER mention "dream", "ideal", or similar words
   - Keep environment descriptions SHORT and CONCISE

4. **Tout en anglais** : All output in English

GÉNÈRE AUSSI un prompt pour la bande son cohérent avec le lieu l'action, le type de rêve (musique d'ambiance).

GÉNÈRE un JSON avec :
{{
    "scenes": [
        {{
            "scene_id": 1,
            "prompt": "Prompt vidéo complet pour scène 1..."
        }},
        ...
    ],
    "prompt_bande_son": "Prompt audio complet..."
}}
"""

        class AllPrompts(BaseModel):
            scenes: List[PromptVideo]
            prompt_bande_son: str = Field(..., min_length=50, max_length=1000)

        result = self._ask_batch("9. Prompts finaux batch", prompt, AllPrompts)

        self.scenario["prompts_video"] = result["scenes"]
        self.scenario["prompt_bande_son"] = result["prompt_bande_son"]

    def generate(self) -> dict:
        """Exécute toutes les étapes de génération batch."""
        self.audit.section("🎬 SCENARIO AGENT v8 - BATCH OPTIMIZED")
        self.audit.detail("Config", self.config)
        self.audit.detail("Rêve", self.v6.get("dream", ""))

        self.step1_blocages_pitch()
        self.step1b_imaginaire_collectif()
        self.step2_decoupage()
        self.step3_parametres_batch()
        self.step4_keyframes_batch()
        self.step5_pitchs_attitudes_batch()
        self.step6_palettes_batch()
        self.step7_cadrages_batch()
        self.step8_rythme()
        self.step9_prompts_finaux_batch()

        # Métadonnées
        self.scenario["metadata"] = {
            "dream": self.v6.get("dream", ""),
            "user_profile": self.user_profile,  # Sauvegarder profil utilisateur (genre, âge, nom)
            "nb_scenes": self.config["nb_scenes"],
            "duree_scene": self.config["duree_scene"],
            "duree_totale": self.config["nb_scenes"] * self.config["duree_scene"],
            "generated_at": datetime.now().isoformat(),
            "version": "v8_batch",
            "cost_usd": self.llm.get_cost(),
            "llm_calls": self.llm.calls,
            "tokens_total": self.llm.tokens_in + self.llm.tokens_out
        }

        self.audit.section("💰 COÛT")
        self.audit.detail("Appels LLM", self.llm.calls)
        self.audit.detail("Tokens", f"{self.llm.tokens_in + self.llm.tokens_out:,}")
        self.audit.detail("Coût USD", f"${self.llm.get_cost():.2f}")

        return self.scenario


# =============================================================================
# MAIN
# =============================================================================

def run(v6_json_path: str, config: dict = None):
    """Exécute la génération de scénario batch."""

    # Charger données v6
    with open(v6_json_path, "r", encoding="utf-8") as f:
        v6_data = json.load(f)

    # Config
    config = config or {}
    if "nb_scenes" not in config:
        config["nb_scenes"] = int(os.getenv("NB_SCENES", "5"))
    if "duree_scene" not in config:
        config["duree_scene"] = int(os.getenv("DUREE_SCENE", "6"))

    # Audit
    audit = AuditLog()

    # Génération
    generator = ScenarioGeneratorBatch(v6_data, config, audit)
    scenario = generator.generate()

    # Sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON
    json_path = f"scenario_v8_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)

    # Audit log
    audit_path = f"scenario_v8_{timestamp}_audit.txt"
    audit.save(audit_path)

    audit.section("✅ TERMINÉ")
    audit.detail("JSON", json_path)
    audit.detail("Audit", audit_path)

    return scenario, json_path, audit_path


if __name__ == "__main__":
    import sys

    # Par défaut, utilise session.json de v6
    v6_path = sys.argv[1] if len(sys.argv) > 1 else "session.json"

    config = {}
    if len(sys.argv) > 2:
        config["nb_scenes"] = int(sys.argv[2])
    if len(sys.argv) > 3:
        config["duree_scene"] = int(sys.argv[3])

    run(v6_path, config)
