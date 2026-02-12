"""
VALIDATION IMAGES V2 — Qualité + Ressemblance + Détection copie ref + Nombre personnes
"""

import json
import os
import base64
import urllib.request
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

RESEMBLANCE_MIN_SCORE = 0.8
QUALITY_MIN_SCORE = 0.7
REF_COPY_THRESHOLD = 0.95  # Si similarité > 95%, c'est une copie
TEETH_VISIBLE_FORBIDDEN = True  # Dents visibles = échec automatique

class ImageValidatorV2:
    def __init__(self, reference_image: str = None):
        self.reference_image = reference_image
        self.openai_key = os.getenv("OPENAI_API_TOKEN") or os.getenv("OPENAI_API_KEY")

        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY manquant dans .env")

    def _call_gpt4o_vision(self, image_paths: list, prompt: str) -> dict:
        """Appel GPT-4o Vision pour analyse d'une ou plusieurs images."""

        content = [{"type": "text", "text": prompt}]

        for img_path in image_paths:
            with open(img_path, "rb") as img_file:
                image_b64 = base64.b64encode(img_file.read()).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                })

        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            return json.loads(result["choices"][0]["message"]["content"])

    def check_reference_copy(self, generated_image: str) -> Dict:
        """Vérifie si l'image générée est une copie de la photo de référence."""

        if not self.reference_image:
            return {"is_copy": False, "similarity": 0.0}

        prompt = """
Compare ces deux images et évalue leur SIMILARITÉ GLOBALE sur une échelle de 0.0 à 1.0.

Image 1 = Photo de référence originale
Image 2 = Image générée

Analyse :
- La composition est-elle identique ? (cadrage, angle, pose)
- L'arrière-plan est-il identique ?
- Les vêtements sont-ils identiques ?
- La pose du corps est-elle identique ?

Si Image 2 est une COPIE quasi-identique d'Image 1 (juste la photo ref collée), score > 0.95
Si Image 2 est une NOUVELLE scène avec la même personne, score < 0.5

Retourne un JSON :
{
    "similarity_score": 0.85,
    "is_copy": true/false,
    "reasons": ["liste des similarités détectées"]
}
"""

        result = self._call_gpt4o_vision([self.reference_image, generated_image], prompt)

        is_copy = result.get("similarity_score", 0) > REF_COPY_THRESHOLD

        return {
            "is_copy": is_copy,
            "similarity": result.get("similarity_score", 0),
            "reasons": result.get("reasons", [])
        }

    def check_people_count(self, image_path: str, expected_count: int) -> Dict:
        """Vérifie le nombre de personnes dans l'image."""

        prompt = f"""
Analyse cette image et compte le nombre de PERSONNES VISIBLES (visages ou corps complets).

Nombre attendu : {expected_count}

Retourne un JSON :
{{
    "people_detected": 2,
    "faces_visible": 1,
    "is_correct_count": true/false,
    "issues": ["liste des problèmes détectés"]
}}
"""

        result = self._call_gpt4o_vision([image_path], prompt)

        detected = result.get("people_detected", 0)
        is_correct = detected == expected_count

        return {
            "expected": expected_count,
            "detected": detected,
            "faces_visible": result.get("faces_visible", 0),
            "valid": is_correct,
            "issues": result.get("issues", [])
        }

    def check_teeth_visible(self, image_path: str) -> Dict:
        """Vérifie si des dents sont visibles (RÉDHIBITOIRE)."""

        prompt = """
Analyse cette image et vérifie si des DENTS sont VISIBLES.

RÈGLE STRICTE : Les dents visibles sont INTERDITES.

Vérifie :
- Bouche fermée = OK
- Sourire léger lèvres closes = OK
- Sourire montrant les dents même partiellement = ÉCHEC
- Sourire avec dents visibles = ÉCHEC

Retourne un JSON :
{
    "teeth_visible": true/false,
    "confidence": 0.95,
    "mouth_description": "description de l'état de la bouche",
    "verdict": "PASS/FAIL"
}
"""

        result = self._call_gpt4o_vision([image_path], prompt)

        teeth_visible = result.get("teeth_visible", False)
        verdict = result.get("verdict", "FAIL" if teeth_visible else "PASS")

        return {
            "teeth_visible": teeth_visible,
            "confidence": result.get("confidence", 0.0),
            "mouth_description": result.get("mouth_description", ""),
            "passed": not teeth_visible,
            "verdict": verdict
        }

    def check_eye_contact(self, image_path: str) -> Dict:
        """Vérifie si la personne regarde la caméra (RÉDHIBITOIRE)."""

        prompt = """
Analyse cette image et vérifie si la personne REGARDE LA CAMÉRA.

RÈGLE STRICTE : Regarder la caméra est INTERDIT.

Vérifie la direction du regard :
- Regard vers le côté, l'horizon, vers le bas = OK
- Regard détourné, pensif, contemplatif = OK
- Regard direct vers la caméra/spectateur = ÉCHEC
- Contact visuel avec le spectateur = ÉCHEC

Retourne un JSON :
{
    "looking_at_camera": true/false,
    "confidence": 0.95,
    "gaze_direction": "description de la direction du regard",
    "verdict": "PASS/FAIL"
}
"""

        result = self._call_gpt4o_vision([image_path], prompt)

        looking_at_camera = result.get("looking_at_camera", False)
        verdict = result.get("verdict", "FAIL" if looking_at_camera else "PASS")

        return {
            "looking_at_camera": looking_at_camera,
            "confidence": result.get("confidence", 0.0),
            "gaze_direction": result.get("gaze_direction", ""),
            "passed": not looking_at_camera,
            "verdict": verdict
        }

    def validate_quality(self, image_path: str) -> Dict:
        """Valide la qualité technique de l'image."""

        prompt = f"""
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

Score minimum acceptable : {QUALITY_MIN_SCORE}
"""

        result = self._call_gpt4o_vision([image_path], prompt)
        result["passed"] = result.get("score", 0) >= QUALITY_MIN_SCORE and result.get("face_visible", False)
        return result

    def validate_resemblance(self, generated_image: str) -> Dict:
        """Valide la ressemblance entre image générée et référence avec vérification détaillée des attributs."""

        if not self.reference_image:
            return {"score": 1.0, "passed": True, "comments": "Pas d'image de référence"}

        prompt = f"""
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

Score minimum requis : {RESEMBLANCE_MIN_SCORE}

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

        result = self._call_gpt4o_vision([self.reference_image, generated_image], prompt)

        # Validation stricte
        skin_match = result.get("skin_tone_match", False)
        face_detected = result.get("face_detected", False)
        score = result.get("score", 0)

        # Si couleur de peau différente, échec automatique
        if not skin_match:
            result["score"] = 0.0
            result["passed"] = False
            if "critical_failures" not in result:
                result["critical_failures"] = []
            result["critical_failures"].append("Couleur de peau différente - ÉCHEC AUTOMATIQUE")
        else:
            result["passed"] = score >= RESEMBLANCE_MIN_SCORE and face_detected

        return result

    def validate_image_v2(self, image_path: str, scene_id: int, scenario: dict) -> Dict:
        """
        Validation complète V2 d'une image.

        Vérifie :
        - Qualité technique
        - Ressemblance faciale
        - Pas une copie de la ref
        - Nombre de personnes attendues
        """

        print(f"\n🔍 Validation V2: {Path(image_path).name}")

        # 1. Qualité
        quality = self.validate_quality(image_path)
        print(f"   Qualité: {quality['score']:.2f} {'✅' if quality['passed'] else '❌'}")

        # 2. Ressemblance
        resemblance = self.validate_resemblance(image_path)
        print(f"   Ressemblance: {resemblance['score']:.2f} {'✅' if resemblance['passed'] else '❌'}")

        # 3. Vérifier si c'est une copie de la ref
        ref_copy_check = self.check_reference_copy(image_path)
        is_ref_copy = ref_copy_check['is_copy']
        print(f"   Copie ref: {'❌ OUI' if is_ref_copy else '✅ NON'} (similarité: {ref_copy_check['similarity']:.2f})")

        # 4. Vérifier nombre de personnes attendues
        # Détecter si la scène a un partenaire
        params = None
        for p in scenario.get("parametres_scenes", []):
            if p.get("scene_id") == scene_id:
                params = p
                break

        # Détecter si partenaire présent (None, null, "Aucun", etc. = pas de partenaire)
        tenue_partenaire = params.get('tenue_partenaire') if params else None
        has_partner = tenue_partenaire not in [None, 'Aucun', 'N/A', 'None', '']
        expected_people = 2 if has_partner else 1

        people_check = self.check_people_count(image_path, expected_people)
        print(f"   Nb personnes: {people_check['detected']}/{people_check['expected']} {'✅' if people_check['valid'] else '❌'}")

        # 5. Vérifier dents visibles (RÉDHIBITOIRE)
        teeth_check = self.check_teeth_visible(image_path)
        print(f"   Dents visibles: {'❌ OUI - ÉCHEC' if teeth_check['teeth_visible'] else '✅ NON'} ({teeth_check['mouth_description']})")

        # 6. Vérifier regard caméra (RÉDHIBITOIRE)
        eye_contact_check = self.check_eye_contact(image_path)
        print(f"   Regard caméra: {'❌ OUI - ÉCHEC' if eye_contact_check['looking_at_camera'] else '✅ NON'} ({eye_contact_check['gaze_direction']})")

        # Validation globale
        overall_passed = (
            quality["passed"] and
            resemblance["passed"] and
            not is_ref_copy and
            people_check["valid"] and
            teeth_check["passed"] and  # RÉDHIBITOIRE
            eye_contact_check["passed"]  # RÉDHIBITOIRE
        )

        return {
            "image": str(image_path),
            "quality": quality,
            "resemblance": resemblance,
            "is_reference_copy": is_ref_copy,
            "ref_copy_details": ref_copy_check,
            "people_count_check": people_check,
            "teeth_check": teeth_check,
            "eye_contact_check": eye_contact_check,
            "overall_passed": overall_passed
        }
