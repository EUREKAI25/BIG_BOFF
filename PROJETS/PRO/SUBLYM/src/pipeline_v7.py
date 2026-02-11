"""
SCENARIO AGENT v7
- Blocages émotionnels + affirmations
- Pitch global
- Découpe en scènes
- Paramètres par scène
- Keyframes (start/end)
- Pitch individuel
- Attitude pendant scène
- Palettes couleurs
- Cadrage justifié
- Rythme
- Output JSON + historique complet (audit)
"""

import json
import os
import urllib.request
import time
from datetime import datetime
from typing import Any, Optional, List, Dict
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

DEFAULT_CONFIG = {
    "nb_scenes": 5,
    "duree_scene": 6,  # secondes
    "model": "gpt-4o"
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
- Expressions positives uniquement (joie, tendresse, émerveillement, complicité)
- JAMAIS d'air triste, inquiet, effrayé, en colère
- Figurants floutés / hors focus (seuls protagonistes nets)
- Pas de gros plan visage (révèle l'artifice IA)
- Vue de dos = brève uniquement, jamais scène entière
- Pas de dos prolongé à la caméra
- Expressions faciales naturelles, pas exagérées
- Contact visuel entre personnages = connexion
- Gestes cohérents avec l'émotion
- Proximité physique progressive (romance)

## RÈGLES CADRAGE
Options autorisées:
- Plan d'ensemble (extreme wide): établir le lieu
- Plan large (wide): action dans l'environnement
- Plan moyen (medium): dialogue, interaction
- Plan américain (cowboy): personnage en action
- Plan rapproché poitrine (medium close-up): émotion sans gros plan visage
- PAS de gros plan visage, PAS de très gros plan

Mouvements caméra autorisés:
- Fixe: stabilité, contemplation
- Travelling avant lent: entrer dans l'intimité
- Travelling arrière lent: révéler le contexte
- Travelling latéral lent: accompagner le mouvement
- Panoramique lent: découverte du lieu
- Léger mouvement (handheld subtle): authenticité

Angles:
- Niveau des yeux: neutre, identification
- Légère plongée: vulnérabilité, tendresse
- Légère contre-plongée: puissance, admiration

## RÈGLES NARRATIVES
- Chaque scène a un objectif émotionnel clair
- Progression d'intensité émotionnelle
- Scène finale = accomplissement visible
- Pas de scène sans lien avec l'objectif du rêve
- Transitions logiques (lieu/temps)

## RÈGLES COHÉRENCE VISUELLE
- Palette couleurs cohérente sur toute la vidéo
- Tenues vestimentaires cohérentes dans le temps
- Éclairage cohérent avec l'heure indiquée
- Météo constante sauf indication contraire

## RÈGLES RYTHME
- Répartition durée à discrétion (±20% par scène)
- Scène d'ouverture peut être plus longue (immersion)
- Scène finale peut être plus longue (impact)
- Pas de scène < 4s
- Pas d'action statique > 3s

## RÈGLES FORMAT RÉPONSE
- Style descriptif neutre, 3ème personne
- JAMAIS de "vous", "Visualisez-vous", "Imaginez"
- Descriptions factuelles et précises
- Pas de répétition entre scènes
"""

PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}

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
    
    def detail(self, key: str, value: Any, indent: int = 0):
        prefix = "   " * indent
        if isinstance(value, dict):
            self.entries.append(f"{prefix}{key}:")
            print(f"{prefix}{key}:")
            for k, v in value.items():
                self.detail(k, v, indent + 1)
        elif isinstance(value, list):
            self.entries.append(f"{prefix}{key}: [{len(value)} items]")
            print(f"{prefix}{key}: [{len(value)} items]")
            for i, item in enumerate(value[:5]):  # Max 5 items displayed
                item_str = str(item)[:100] + "..." if len(str(item)) > 100 else str(item)
                self.entries.append(f"{prefix}   [{i+1}] {item_str}")
                print(f"{prefix}   [{i+1}] {item_str}")
            if len(value) > 5:
                self.entries.append(f"{prefix}   ... et {len(value)-5} de plus")
                print(f"{prefix}   ... et {len(value)-5} de plus")
        else:
            value_str = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
            self.entries.append(f"{prefix}{key}: {value_str}")
            print(f"{prefix}{key}: {value_str}")
    
    def validation(self, v1: dict, v2: dict, v3: dict):
        v1_icon = "✅" if v1.get("passed") else "❌"
        v2_icon = "✅" if v2.get("passed") else "❌"
        v3_icon = "✅" if v3.get("final_pass") else "❌"
        
        lines = [
            f"   ┌─ V1: {v1['score']:.0%} {v1_icon} {v1.get('feedback', '')[:60]}",
            f"   ├─ V2: {v2['score']:.0%} {v2_icon} {v2.get('feedback', '')[:60]}",
            f"   └─ V3: {v3_icon} {v3.get('reasoning', '')[:60]}"
        ]
        for line in lines:
            self.entries.append(line)
            print(line)
        
        for s in v3.get('optimization_suggestions', [])[:2]:
            self.entries.append(f"      💡 {s[:70]}")
            print(f"      💡 {s[:70]}")
    
    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"SCENARIO AGENT v7 - AUDIT LOG\n")
            f.write(f"Généré le: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Durée: {(datetime.now() - self.start_time).seconds}s\n")
            f.write("=" * 80 + "\n\n")
            f.write("\n".join(self.entries))


# =============================================================================
# LLM CLIENT
# =============================================================================

class LLM:
    def __init__(self, model: str = "gpt-4o"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.calls = 0
        self.tokens_in = 0
        self.tokens_out = 0
        self.max_retries = 3
    
    def _call(self, system: str, user: str, temp: float = 0.7) -> dict:
        self.calls += 1
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temp,
            "max_tokens": 4000,
            "response_format": {"type": "json_object"}
        }
        
        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(
                    "https://api.openai.com/v1/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                )
                
                with urllib.request.urlopen(req, timeout=120) as resp:
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
# SCENARIO GENERATOR
# =============================================================================

class ScenarioGenerator:
    def __init__(self, v6_data: dict, config: dict, audit: AuditLog):
        self.v6 = v6_data
        self.config = {**DEFAULT_CONFIG, **config}
        self.audit = audit
        self.llm = LLM(self.config.get("model", "gpt-4o"))
        self.scenario = {}
    
    def _get_context(self) -> str:
        """Construit le contexte à partir des données v6."""
        return self.v6.get("context", f"RÊVE: {self.v6.get('dream', '')}")
    
    def _validate(self, answer: str, question: str, criterion: str) -> tuple[dict, dict, dict]:
        """Triple validation V1/V2/V3."""
        context = self._get_context()
        
        # V1
        system_v1 = f"""VALIDATEUR V1 - Critère spécifique
{PRODUCTION_RULES}
Score 0.0-1.0. Minimum 0.8 pour passer.
JSON: {{"score": 0.0-1.0, "passed": true/false, "feedback": "...", "suggestion": "..."}}"""
        
        v1 = self.llm._call(system_v1, f"CONTEXTE:\n{context}\n\nQUESTION: {question}\nRÉPONSE: {answer}\n\nCRITÈRE: {criterion}", 0.2)
        v1["score"] = float(v1.get("score", 0))
        v1["passed"] = v1["score"] >= 0.8
        
        # V2
        system_v2 = f"""VALIDATEUR V2 - Méta-cohérence et règles de production
{PRODUCTION_RULES}
Vérifie la cohérence globale ET le respect des règles de production.
JSON: {{"score": 0.0-1.0, "passed": true/false, "feedback": "...", "suggestion": "..."}}"""
        
        v2 = self.llm._call(system_v2, f"CONTEXTE:\n{context}\n\nRÉPONSE: {answer}\n\nV1: {v1['score']:.0%}", 0.2)
        v2["score"] = float(v2.get("score", 0))
        v2["passed"] = v2["score"] >= 0.8
        
        # V3
        system_v3 = f"""VALIDATEUR V3 - Arbitre final
OBJECTIF: Générer une VIDÉO de réalisation du rêve, de qualité professionnelle.
{PRODUCTION_RULES}
JSON: {{"final_pass": true/false, "reasoning": "...", "optimization_suggestions": ["..."], "confidence": 0.0-1.0}}"""
        
        v3 = self.llm._call(system_v3, f"RÉPONSE: {answer}\n\nV1: {v1['score']:.0%}\nV2: {v2['score']:.0%}", 0.3)
        v3["final_pass"] = v3.get("final_pass", False)
        v3["confidence"] = float(v3.get("confidence", 0.5))
        
        return v1, v2, v3
    
    def _ask(self, step: str, question: str, criterion: str, schema: dict = None) -> Any:
        """Question avec validation."""
        self.audit.subsection(step)
        self.audit.log(f"❓ {question[:100]}...")
        
        context = self._get_context()
        
        if schema:
            schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
            system = f"""Réponds avec un JSON structuré.
{PRODUCTION_RULES}
SCHÉMA ATTENDU: {schema_str}
JSON: {{"data": {{...}}, "reasoning": "..."}}"""
        else:
            system = f"""Réponds de façon précise et complète.
{PRODUCTION_RULES}
JSON: {{"answer": "...", "reasoning": "..."}}"""
        
        result = self.llm._call(system, f"CONTEXTE:\n{context}\n\nQUESTION: {question}", 0.7)
        
        answer = result.get("data") if schema else result.get("answer")
        reasoning = result.get("reasoning", "")
        
        self.audit.detail("Réponse", answer)
        self.audit.detail("Raisonnement", reasoning)
        
        v1, v2, v3 = self._validate(str(answer), question, criterion)
        self.audit.validation(v1, v2, v3)
        
        if v3["final_pass"]:
            self.audit.log("💾 Stocké!")
        else:
            self.audit.log("⚠️ Stocké avec réserve")
        
        return answer
    
    # =========================================================================
    # ÉTAPES DE GÉNÉRATION
    # =========================================================================
    
    def step1_blocages_emotionnels(self):
        """Génère les blocages émotionnels et affirmations positives."""
        self.audit.section("ÉTAPE 1: BLOCAGES ÉMOTIONNELS")
        
        blocages = self._ask(
            "1.1 Blocages potentiels",
            f"Quels BLOCAGES ÉMOTIONNELS ce rêve pourrait soulever chez la personne ? (ex: 'pas assez belle', 'je ne mérite pas', 'peur de l'abandon'). Liste 3-5 blocages typiques pour ce type de rêve.",
            "Les blocages sont réalistes et pertinents pour ce type de rêve",
            schema={"blocages": ["blocage 1", "blocage 2", "..."]}
        )
        
        affirmations = self._ask(
            "1.2 Affirmations positives",
            f"Pour chaque blocage identifié ({blocages}), quelle est l'AFFIRMATION POSITIVE opposée ? (ex: 'je mérite l'amour', 'je suis prête')",
            "Les affirmations sont l'opposé direct des blocages",
            schema={"affirmations": ["affirmation 1", "affirmation 2", "..."]}
        )
        
        self.scenario["blocages_emotionnels"] = {
            "blocages": blocages.get("blocages", []) if isinstance(blocages, dict) else blocages,
            "affirmations": affirmations.get("affirmations", []) if isinstance(affirmations, dict) else affirmations
        }
    
    def step2_pitch_global(self):
        """Génère le pitch global du scénario."""
        self.audit.section("ÉTAPE 2: PITCH GLOBAL")
        
        pitch = self._ask(
            "2.1 Pitch global",
            f"Écris un PITCH GLOBAL détaillé du scénario en {self.config['nb_scenes']} scènes. Description narrative complète de l'histoire, du début à l'accomplissement. Style neutre, 3ème personne, pas de 'vous'.",
            "Le pitch couvre l'arc narratif complet avec progression émotionnelle"
        )
        
        self.scenario["pitch_global"] = pitch
    
    def step3_decoupage_scenes(self):
        """Découpe en scènes avec validation."""
        self.audit.section("ÉTAPE 3: DÉCOUPAGE EN SCÈNES")
        
        nb = self.config["nb_scenes"]
        
        decoupage = self._ask(
            "3.1 Découpage",
            f"Découpe le scénario en exactement {nb} scènes. Pour chaque scène: que se passe-t-il ? D'où part-on, où va-t-on émotionnellement ? PAS de détails de décor à ce stade.",
            "La découpe est cohérente avec l'intention du rêve, chronologie respectée, pas de scène sans rapport",
            schema={
                "scenes": [
                    {"id": 1, "titre": "...", "de": "état initial", "vers": "état suivant", "action": "que se passe-t-il"}
                ]
            }
        )
        
        self.scenario["decoupage"] = decoupage.get("scenes", []) if isinstance(decoupage, dict) else decoupage
    
    def step4_parametres_scenes(self):
        """Définit les paramètres de chaque scène."""
        self.audit.section("ÉTAPE 4: PARAMÈTRES PAR SCÈNE")
        
        scenes = self.scenario.get("decoupage", [])
        params = []
        
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", i+1) if isinstance(scene, dict) else i+1
            scene_titre = scene.get("titre", f"Scène {i+1}") if isinstance(scene, dict) else f"Scène {i+1}"
            
            p = self._ask(
                f"4.{i+1} Paramètres scène {scene_id}: {scene_titre}",
                f"Pour la scène '{scene_titre}' ({scene}), définis: OÙ précisément ? QUAND précisément ? QUELLE ACTION ? QUELLE TENUE pour chaque personnage ?",
                "Les paramètres sont cohérents avec le lieu global et l'action de la scène",
                schema={
                    "lieu_precis": "...",
                    "moment": "heure et lumière",
                    "action": "description action",
                    "tenue_protagoniste": "...",
                    "tenue_partenaire": "..."
                }
            )
            params.append({"scene_id": scene_id, **p} if isinstance(p, dict) else {"scene_id": scene_id, "data": p})
        
        self.scenario["parametres_scenes"] = params
    
    def step5_keyframes(self):
        """Génère les keyframes start/end pour chaque scène."""
        self.audit.section("ÉTAPE 5: KEYFRAMES")
        
        scenes = self.scenario.get("decoupage", [])
        keyframes = []
        
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", i+1) if isinstance(scene, dict) else i+1
            params = self.scenario["parametres_scenes"][i] if i < len(self.scenario.get("parametres_scenes", [])) else {}
            
            kf = self._ask(
                f"5.{i+1} Keyframes scène {scene_id}",
                f"Pour la scène {scene_id} (lieu: {params.get('lieu_precis', '?')}, action: {params.get('action', '?')}), décris le KEYFRAME DE DÉBUT et le KEYFRAME DE FIN. Position précise des personnages, émotion, gestes, interaction. Style neutre, 3ème personne.",
                "Les keyframes sont photographiables, positions précises, émotions positives uniquement",
                schema={
                    "start": {
                        "position_protagoniste": "...",
                        "position_partenaire": "...",
                        "emotion": "...",
                        "geste": "...",
                        "interaction": "..."
                    },
                    "end": {
                        "position_protagoniste": "...",
                        "position_partenaire": "...",
                        "emotion": "...",
                        "geste": "...",
                        "interaction": "..."
                    }
                }
            )
            keyframes.append({"scene_id": scene_id, **kf} if isinstance(kf, dict) else {"scene_id": scene_id, "data": kf})
        
        self.scenario["keyframes"] = keyframes
    
    def step6_pitchs_individuels(self):
        """Génère le pitch narratif de chaque scène."""
        self.audit.section("ÉTAPE 6: PITCHS INDIVIDUELS")
        
        scenes = self.scenario.get("decoupage", [])
        pitchs = []
        
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", i+1) if isinstance(scene, dict) else i+1
            params = self.scenario["parametres_scenes"][i] if i < len(self.scenario.get("parametres_scenes", [])) else {}
            kf = self.scenario["keyframes"][i] if i < len(self.scenario.get("keyframes", [])) else {}
            
            pitch = self._ask(
                f"6.{i+1} Pitch scène {scene_id}",
                f"Écris le PITCH NARRATIF de la scène {scene_id}. Lieu: {params.get('lieu_precis')}. Action: {params.get('action')}. Style neutre, 3ème personne, JAMAIS de 'vous' ou 'imaginez'.",
                "Le pitch est narratif, fluide, style professionnel, pas de 'vous'"
            )
            pitchs.append({"scene_id": scene_id, "pitch": pitch})
        
        self.scenario["pitchs"] = pitchs
    
    def step7_attitudes(self):
        """Définit les attitudes et déplacements pendant chaque scène."""
        self.audit.section("ÉTAPE 7: ATTITUDES ET DÉPLACEMENTS")
        
        scenes = self.scenario.get("decoupage", [])
        attitudes = []
        
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", i+1) if isinstance(scene, dict) else i+1
            kf = self.scenario["keyframes"][i] if i < len(self.scenario.get("keyframes", [])) else {}
            
            att = self._ask(
                f"7.{i+1} Attitude scène {scene_id}",
                f"Pour la scène {scene_id}, décris l'ATTITUDE DES PERSONNAGES PENDANT la scène et leur DÉPLACEMENT dans l'espace. Du keyframe start au keyframe end. Mouvements lents. Pas de demi-tour. Style neutre.",
                "Déplacements réalistes, lents, pas de demi-tour, cohérent avec keyframes",
                schema={
                    "attitude_protagoniste": "...",
                    "attitude_partenaire": "...",
                    "deplacement": "description du mouvement dans l'espace",
                    "interaction_continue": "..."
                }
            )
            attitudes.append({"scene_id": scene_id, **att} if isinstance(att, dict) else {"scene_id": scene_id, "data": att})
        
        self.scenario["attitudes"] = attitudes
    
    def step8_palettes(self):
        """Définit les palettes de couleurs."""
        self.audit.section("ÉTAPE 8: PALETTES COULEURS")
        
        # Palette globale
        palette_globale = self._ask(
            "8.1 Palette globale",
            f"Définis une PALETTE DE COULEURS GLOBALE pour cette vidéo (5 couleurs principales en hexa). Cohérente avec: lieu ({self.v6.get('dream', '')}), ambiance romantique, heure de la journée.",
            "Palette cohérente, harmonieuse, adaptée à l'ambiance",
            schema={
                "principale": "#hex",
                "secondaire": "#hex",
                "accent": "#hex",
                "neutre_clair": "#hex",
                "neutre_fonce": "#hex"
            }
        )
        
        self.scenario["palette_globale"] = palette_globale
        
        # Palettes par scène
        scenes = self.scenario.get("decoupage", [])
        palettes_scenes = []
        
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", i+1) if isinstance(scene, dict) else i+1
            params = self.scenario["parametres_scenes"][i] if i < len(self.scenario.get("parametres_scenes", [])) else {}
            
            pal = self._ask(
                f"8.{i+2} Palette scène {scene_id}",
                f"Décline la palette globale pour la scène {scene_id}. Moment: {params.get('moment', '?')}. Lieu: {params.get('lieu_precis', '?')}. Ajustements selon lumière et ambiance de cette scène spécifique.",
                "Déclinaison cohérente avec palette globale, ajustée à l'heure/lieu",
                schema={
                    "dominante": "#hex",
                    "accent": "#hex",
                    "lumiere": "chaude/froide/neutre",
                    "saturation": "haute/moyenne/basse"
                }
            )
            palettes_scenes.append({"scene_id": scene_id, **pal} if isinstance(pal, dict) else {"scene_id": scene_id, "data": pal})
        
        self.scenario["palettes_scenes"] = palettes_scenes
    
    def step9_cadrage(self):
        """Définit le cadrage pour chaque scène."""
        self.audit.section("ÉTAPE 9: CADRAGE")
        
        scenes = self.scenario.get("decoupage", [])
        cadrages = []
        
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", i+1) if isinstance(scene, dict) else i+1
            params = self.scenario["parametres_scenes"][i] if i < len(self.scenario.get("parametres_scenes", [])) else {}
            
            cad = self._ask(
                f"9.{i+1} Cadrage scène {scene_id}",
                f"Définis le CADRAGE pour la scène {scene_id}. Type de plan, mouvement caméra, angle. JUSTIFIE chaque choix avec des arguments cinématographiques professionnels. Rappel: PAS de gros plan visage.",
                "Choix justifiés professionnellement, pas de gros plan, mouvement lent",
                schema={
                    "type_plan": "plan large/moyen/américain/rapproché poitrine",
                    "justification_plan": "argument cinématographique",
                    "mouvement_camera": "fixe/travelling/panoramique",
                    "justification_mouvement": "argument cinématographique",
                    "angle": "niveau yeux/plongée/contre-plongée",
                    "justification_angle": "argument cinématographique"
                }
            )
            cadrages.append({"scene_id": scene_id, **cad} if isinstance(cad, dict) else {"scene_id": scene_id, "data": cad})
        
        self.scenario["cadrages"] = cadrages
    
    def step10_rythme(self):
        """Définit le rythme et la durée par scène."""
        self.audit.section("ÉTAPE 10: RYTHME")
        
        duree_totale = self.config["nb_scenes"] * self.config["duree_scene"]
        
        rythme = self._ask(
            "10.1 Répartition des durées",
            f"Répartis la durée totale ({duree_totale}s) entre les {self.config['nb_scenes']} scènes. Durée moyenne: {self.config['duree_scene']}s. Tu peux ajuster ±20% par scène. JUSTIFIE la répartition avec des arguments professionnels.",
            "La somme fait exactement la durée totale, justifications professionnelles",
            schema={
                "duree_totale": duree_totale,
                "scenes": [
                    {"scene_id": 1, "duree": 0, "justification": "..."}
                ]
            }
        )
        
        self.scenario["rythme"] = rythme
    
    def step11_prompts_finaux(self):
        """Génère les prompts finaux pour la génération vidéo."""
        self.audit.section("ÉTAPE 11: PROMPTS FINAUX")
        
        scenes = self.scenario.get("decoupage", [])
        prompts_video = []
        
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", i+1) if isinstance(scene, dict) else i+1
            params = self.scenario["parametres_scenes"][i] if i < len(self.scenario.get("parametres_scenes", [])) else {}
            kf = self.scenario["keyframes"][i] if i < len(self.scenario.get("keyframes", [])) else {}
            att = self.scenario["attitudes"][i] if i < len(self.scenario.get("attitudes", [])) else {}
            pal = self.scenario["palettes_scenes"][i] if i < len(self.scenario.get("palettes_scenes", [])) else {}
            cad = self.scenario["cadrages"][i] if i < len(self.scenario.get("cadrages", [])) else {}
            
            prompt = self._ask(
                f"11.{i+1} Prompt vidéo scène {scene_id}",
                f"""Génère le PROMPT FINAL pour la génération vidéo de la scène {scene_id}.
                
Paramètres: {json.dumps(params, ensure_ascii=False)}
Keyframes: {json.dumps(kf, ensure_ascii=False)}
Attitude: {json.dumps(att, ensure_ascii=False)}
Palette: {json.dumps(pal, ensure_ascii=False)}
Cadrage: {json.dumps(cad, ensure_ascii=False)}

Le prompt doit être optimisé pour une IA de génération vidéo. Style neutre, descriptif, précis.""",
                "Prompt complet, précis, optimisé pour génération IA"
            )
            prompts_video.append({"scene_id": scene_id, "prompt": prompt})
        
        self.scenario["prompts_video"] = prompts_video
        
        # Prompt bande son
        prompt_audio = self._ask(
            "11.X Prompt bande son",
            f"Génère le PROMPT FINAL pour la génération de la bande son. Basé sur le brief: {self.v6.get('elements', {}).get('7.1 Brief bande son', {})}",
            "Prompt complet pour génération musicale IA"
        )
        
        self.scenario["prompt_bande_son"] = prompt_audio
    
    def generate(self) -> dict:
        """Exécute toutes les étapes de génération."""
        self.audit.section("🎬 SCENARIO AGENT v7 - GÉNÉRATION")
        self.audit.detail("Config", self.config)
        self.audit.detail("Rêve", self.v6.get("dream", ""))
        
        self.step1_blocages_emotionnels()
        self.step2_pitch_global()
        self.step3_decoupage_scenes()
        self.step4_parametres_scenes()
        self.step5_keyframes()
        self.step6_pitchs_individuels()
        self.step7_attitudes()
        self.step8_palettes()
        self.step9_cadrage()
        self.step10_rythme()
        self.step11_prompts_finaux()
        
        # Métadonnées
        self.scenario["metadata"] = {
            "dream": self.v6.get("dream", ""),
            "nb_scenes": self.config["nb_scenes"],
            "duree_scene": self.config["duree_scene"],
            "duree_totale": self.config["nb_scenes"] * self.config["duree_scene"],
            "generated_at": datetime.now().isoformat(),
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
    """Exécute la génération de scénario."""
    
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
    generator = ScenarioGenerator(v6_data, config, audit)
    scenario = generator.generate()
    
    # Sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON
    json_path = f"scenario_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)
    
    # Audit log
    audit_path = f"scenario_{timestamp}_audit.txt"
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
