"""
Sublym v4 - Face Validator
Validation faciale biométrique : DeepFace + ArcFace uniquement
Gemini n'est PAS utilisé pour le visage (trop généreux, donne toujours 1.0)
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Imports conditionnels pour les dépendances optionnelles
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("⚠️ DeepFace non installé. pip install deepface")

try:
    import insightface
    from insightface.app import FaceAnalysis
    import numpy as np
    ARCFACE_AVAILABLE = True
except ImportError:
    ARCFACE_AVAILABLE = False
    print("⚠️ InsightFace non installé. pip install insightface onnxruntime")


class FaceValidator:
    """
    Validation faciale biométrique (DeepFace + ArcFace).

    Règle de validation:
    - L'écart cumulé des 2 scores par rapport au seuil (0.8) doit être < tolerance
    - Gemini n'est PAS utilisé pour la face (trop généreux)
    """

    DEFAULT_THRESHOLD = 0.8

    def __init__(self, config: Dict, run_dir: str, verbose: bool = False):
        self.config = config
        self.run_dir = Path(run_dir)
        self.verbose = verbose

        # Paramètres de validation
        face_config = config.get("face_validation", {})
        self.tolerance = face_config.get("tolerance", 0.3)
        self.threshold = face_config.get("threshold", self.DEFAULT_THRESHOLD)

        # Répertoire pour les images rejetées
        self.rejected_dir = self.run_dir / "rejected"

        # Initialiser ArcFace si disponible
        self.arcface_app = None
        if ARCFACE_AVAILABLE:
            try:
                self.arcface_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
                self.arcface_app.prepare(ctx_id=0, det_size=(640, 640))
            except Exception as e:
                print(f"⚠️ Erreur init ArcFace: {e}")
                self.arcface_app = None

        # Stats
        self.stats = {
            "total_validations": 0,
            "passed": 0,
            "rejected": 0,
            "rejected_details": []
        }

    def validate(
        self,
        generated_image_path: str,
        reference_image_path: str,
        scene_id: int,
        kf_type: str,
        attempt: int,
        gemini_score: float = 0.0,
        shot_type: str = "medium",
        expected_faces: int = 1,
    ) -> Dict[str, Any]:
        """
        Valide une image générée contre la référence (biométrique uniquement).

        Returns:
            {
                "passed": bool,
                "scores": {"deepface": float, "arcface": float},
                "cumulative_gap": float,
                "reason": str or None
            }
        """
        self.stats["total_validations"] += 1

        # Tolérance adaptée au type de plan
        tolerance_map = self.config.get("face_tolerance_by_shot", {})
        shot_tolerance = tolerance_map.get(shot_type, self.tolerance)

        # Skip face validation si None (dos, visage non visible)
        if shot_tolerance is None:
            print(f"\n      --- FACE VALIDATION SKIPPED (shot_type={shot_type}) ---")
            self.stats["passed"] += 1
            return {
                "passed": True,
                "scores": {},
                "cumulative_gap": 0.0,
                "reason": f"Face validation skipped (shot_type={shot_type})",
                "skipped": True,
            }

        # Doublon intelligent : on ne compte pas les visages, on vérifie que
        # la même personne n'apparaît pas 2 fois (bug fréquent de Gemini).
        # Les figurants en arrière-plan (village, marché, café) sont OK car
        # ce sont des personnes différentes (cosine faible entre elles).
        if ARCFACE_AVAILABLE and self.arcface_app:
            dup_reason = self._check_duplicate_faces(generated_image_path)
            if dup_reason:
                self.stats["rejected"] += 1
                result = {
                    "passed": False,
                    "scores": {},
                    "cumulative_gap": 0.0,
                    "reason": f"Face validation: {dup_reason}",
                }
                print(f"\n      --- FACE VALIDATION REJECTED: {dup_reason} ---")
                self._save_rejected(generated_image_path, {}, 0.0, dup_reason, scene_id, kf_type, attempt)
                return result

        scores = {
            "deepface": 0.0,
            "arcface": 0.0,
        }

        # Score DeepFace
        if DEEPFACE_AVAILABLE:
            scores["deepface"] = self._get_deepface_score(generated_image_path, reference_image_path)
        else:
            scores["deepface"] = 0.5  # Score neutre si indisponible

        # Score ArcFace
        if ARCFACE_AVAILABLE and self.arcface_app:
            scores["arcface"] = self._get_arcface_score(generated_image_path, reference_image_path)
        else:
            scores["arcface"] = 0.5  # Score neutre si indisponible

        # Calcul de l'écart cumulé (2 scores: DeepFace + ArcFace uniquement)
        cumulative_gap = 0.0
        for score in scores.values():
            if score < self.threshold:
                cumulative_gap += (self.threshold - score)

        # Règle de validation : gap biométrique vs tolérance adaptée au shot
        passed = cumulative_gap < shot_tolerance

        # Raison du rejet
        reason = None
        if not passed:
            reason = f"Écart cumulé {cumulative_gap:.2f} >= {shot_tolerance}"

        result = {
            "passed": passed,
            "scores": scores,
            "cumulative_gap": cumulative_gap,
            "reason": reason
        }

        # ===== DEBUG: Toujours afficher les scores face =====
        print(f"\n      --- FACE VALIDATION (DeepFace + ArcFace) ---")
        print(f"      DeepFace:  {scores['deepface']:.4f}  (threshold: {self.threshold})")
        print(f"      ArcFace:   {scores['arcface']:.4f}  (threshold: {self.threshold})")
        print(f"      Cumul gap: {cumulative_gap:.4f}  (tolerance: {shot_tolerance} [shot={shot_type}])")
        print(f"      PASSED: {passed}")
        if reason:
            print(f"      Reason:    {reason}")
        print(f"      ---")

        if self.verbose:
            status = "✅" if passed else "❌"
            print(f"      {status} Face validation: DF={scores['deepface']:.2f} AF={scores['arcface']:.2f} (gap={cumulative_gap:.2f})")

        # Sauvegarder si rejeté
        if not passed:
            self._save_rejected(generated_image_path, scores, cumulative_gap, reason, scene_id, kf_type, attempt)
            self.stats["rejected"] += 1
        else:
            self.stats["passed"] += 1

        return result

    def validate_with_character_b(
        self,
        generated_image_path: str,
        protagonist_reference: str,
        character_b_reference: str = None,
        scene_id: int = 0,
        kf_type: str = "start",
        attempt: int = 1,
        shot_type: str = "medium",
        character_b_references: list = None,
    ) -> Dict[str, Any]:
        """
        Valide une image avec 2 personnes : protagonist + character_b.

        1. Détecte tous les visages dans l'image générée
        2. Compare chaque visage avec protagonist_ref et character_b_refs (multi-angles)
        3. Assigne chaque référence au visage le plus proche
        4. Valide que les 2 personnes sont présentes et différentes

        Args:
            character_b_reference: Single ref (rétrocompat)
            character_b_references: Liste de refs multi-angles (prioritaire)

        Returns:
            {
                "passed": bool,
                "protagonist_scores": {"deepface": float, "arcface": float},
                "character_b_scores": {"arcface": float},
                "character_b_present": bool,
                "two_distinct_people": bool,
                "cumulative_gap": float,
                "reason": str or None
            }
        """
        # Support multi-refs : prendre la liste si fournie, sinon single ref
        cb_refs = character_b_references or ([character_b_reference] if character_b_reference else [])
        self.stats["total_validations"] += 1

        # Config character_b
        char_b_config = self.config.get("character_b_validation", {})
        char_b_threshold = char_b_config.get("threshold", 0.6)
        char_b_tolerance = char_b_config.get("tolerance", 0.5)
        min_faces = char_b_config.get("min_faces_required", 2)
        duplicate_threshold = char_b_config.get("duplicate_threshold", 0.6)

        # Tolérance adaptée au type de plan pour protagonist
        tolerance_map = self.config.get("face_tolerance_by_shot", {})
        shot_tolerance = tolerance_map.get(shot_type, self.tolerance)

        # Skip si plan de dos
        if shot_tolerance is None:
            print(f"\n      --- FACE VALIDATION SKIPPED (shot_type={shot_type}) ---")
            self.stats["passed"] += 1
            return {
                "passed": True,
                "protagonist_scores": {},
                "character_b_scores": {},
                "character_b_present": True,
                "two_distinct_people": True,
                "cumulative_gap": 0.0,
                "reason": f"Face validation skipped (shot_type={shot_type})",
                "skipped": True,
            }

        result = {
            "passed": False,
            "protagonist_scores": {"deepface": 0.0, "arcface": 0.0},
            "character_b_scores": {"arcface": 0.0},
            "character_b_present": False,
            "two_distinct_people": False,
            "cumulative_gap": 0.0,
            "reason": None,
        }

        if not ARCFACE_AVAILABLE or not self.arcface_app:
            result["passed"] = True
            result["reason"] = "ArcFace not available - skipped"
            return result

        try:
            import cv2

            # Charger les images
            img_gen = cv2.imread(generated_image_path)
            img_prot_ref = cv2.imread(protagonist_reference)

            if img_gen is None or img_prot_ref is None:
                result["reason"] = "Failed to load images"
                return result

            # Charger TOUTES les références character_b (multi-angles)
            charb_embeddings = []
            for cb_ref_path in cb_refs:
                img_cb = cv2.imread(cb_ref_path)
                if img_cb is not None:
                    faces_cb = self.arcface_app.get(img_cb)
                    if faces_cb:
                        charb_embeddings.append(faces_cb[0].embedding)

            if not charb_embeddings:
                result["reason"] = "No valid character_b reference images"
                return result

            # Détecter tous les visages
            faces_gen = self.arcface_app.get(img_gen)
            faces_prot = self.arcface_app.get(img_prot_ref)

            print(f"\n      --- CHARACTER B FACE VALIDATION ---")
            print(f"      Faces detected: generated={len(faces_gen)}, protagonist_ref={len(faces_prot)}, charb_refs={len(charb_embeddings)}")

            # Vérifier qu'on a assez de visages
            if len(faces_gen) < min_faces:
                result["reason"] = f"Only {len(faces_gen)} face(s) detected, need {min_faces}"
                result["character_b_present"] = False
                print(f"      ❌ {result['reason']}")
                self._save_rejected(generated_image_path, {}, 0.0, result["reason"], scene_id, kf_type, attempt)
                self.stats["rejected"] += 1
                return result

            if not faces_prot:
                result["reason"] = "No face in protagonist reference"
                return result

            # Embedding protagonist
            emb_prot_ref = faces_prot[0].embedding

            # Pour chaque visage généré, calculer la similarité avec protagonist ET
            # le MEILLEUR score parmi TOUTES les refs character_b
            face_scores = []
            for i, face in enumerate(faces_gen):
                emb = face.embedding
                cos_prot = float(np.dot(emb_prot_ref, emb) / (np.linalg.norm(emb_prot_ref) * np.linalg.norm(emb)))

                # Meilleur score parmi toutes les refs character_b
                best_cos_charb = -1.0
                for emb_charb in charb_embeddings:
                    cos_cb = float(np.dot(emb_charb, emb) / (np.linalg.norm(emb_charb) * np.linalg.norm(emb)))
                    if cos_cb > best_cos_charb:
                        best_cos_charb = cos_cb

                face_scores.append({
                    "face_idx": i,
                    "cosine_protagonist": cos_prot,
                    "cosine_character_b": best_cos_charb,
                    "embedding": emb
                })

            # Assigner protagonist = visage avec meilleur score protagonist
            best_prot = max(face_scores, key=lambda x: x["cosine_protagonist"])
            remaining = [f for f in face_scores if f["face_idx"] != best_prot["face_idx"]]

            # Assigner character_b = meilleur score character_b parmi les restants
            if remaining:
                best_charb = max(remaining, key=lambda x: x["cosine_character_b"])
            else:
                best_charb = None

            # Scores protagonist
            prot_cosine = best_prot["cosine_protagonist"]
            prot_score = (prot_cosine + 1) / 2  # Convert to 0-1

            print(f"      Protagonist: face #{best_prot['face_idx']} cosine={prot_cosine:.4f} score={prot_score:.4f}")

            # Scores character_b
            if best_charb:
                charb_cosine = best_charb["cosine_character_b"]
                charb_score = (charb_cosine + 1) / 2
                result["character_b_present"] = charb_score >= char_b_threshold
                print(f"      Character B: face #{best_charb['face_idx']} cosine={charb_cosine:.4f} score={charb_score:.4f} (threshold={char_b_threshold})")

                # Vérifier que les 2 visages sont différents
                cos_between = float(np.dot(best_prot["embedding"], best_charb["embedding"]) /
                                   (np.linalg.norm(best_prot["embedding"]) * np.linalg.norm(best_charb["embedding"])))
                result["two_distinct_people"] = cos_between < duplicate_threshold
                print(f"      Distinctness: cosine_between={cos_between:.4f} (threshold={duplicate_threshold}) distinct={result['two_distinct_people']}")

                result["character_b_scores"]["arcface"] = charb_score
            else:
                charb_score = 0.0
                result["character_b_present"] = False
                result["two_distinct_people"] = False
                print(f"      Character B: NOT FOUND")

            # DeepFace pour protagonist (plus précis)
            if DEEPFACE_AVAILABLE:
                result["protagonist_scores"]["deepface"] = self._get_deepface_score(
                    generated_image_path, protagonist_reference
                )
            else:
                result["protagonist_scores"]["deepface"] = prot_score

            result["protagonist_scores"]["arcface"] = prot_score

            # Calcul de l'écart cumulé (protagonist only, character_b est plus tolérant)
            cumulative_gap = 0.0
            for score in result["protagonist_scores"].values():
                if score < self.threshold:
                    cumulative_gap += (self.threshold - score)
            result["cumulative_gap"] = cumulative_gap

            # Décision finale
            protagonist_ok = cumulative_gap < shot_tolerance
            character_b_ok = result["character_b_present"] and result["two_distinct_people"]

            result["passed"] = protagonist_ok and character_b_ok

            if not result["passed"]:
                reasons = []
                if not protagonist_ok:
                    reasons.append(f"Protagonist gap {cumulative_gap:.2f} >= {shot_tolerance}")
                if not result["character_b_present"]:
                    reasons.append("Character B missing or score too low")
                if not result["two_distinct_people"]:
                    reasons.append("Same person appears twice (duplicate)")
                result["reason"] = "; ".join(reasons)

            print(f"      PASSED: {result['passed']}")
            if result["reason"]:
                print(f"      Reason: {result['reason']}")
            print(f"      ---")

            # Stats
            if result["passed"]:
                self.stats["passed"] += 1
            else:
                self._save_rejected(generated_image_path, result["protagonist_scores"],
                                   cumulative_gap, result["reason"], scene_id, kf_type, attempt)
                self.stats["rejected"] += 1

            return result

        except Exception as e:
            result["reason"] = f"Error: {str(e)}"
            print(f"      ❌ Character B validation error: {e}")
            return result

    def _check_duplicate_faces(self, image_path: str, cosine_threshold: float = 0.6) -> Optional[str]:
        """Vérifie qu'aucune personne n'apparaît en double dans l'image.

        Compare toutes les faces détectées entre elles (pairwise).
        Si deux faces ont une similarité cosinus > cosine_threshold,
        c'est la même personne dupliquée (bug Gemini fréquent).

        Les figurants (personnes différentes) ont un cosine faible → pas de faux positif.

        Returns:
            Reason string si doublon détecté, None si OK.
        """
        try:
            import cv2

            img_cv = cv2.imread(image_path)
            if img_cv is None:
                return None

            faces = self.arcface_app.get(img_cv)
            if len(faces) < 2:
                return None

            # Comparer chaque paire de visages
            for i in range(len(faces)):
                for j in range(i + 1, len(faces)):
                    emb_i = faces[i].embedding
                    emb_j = faces[j].embedding
                    cos = float(np.dot(emb_i, emb_j) / (np.linalg.norm(emb_i) * np.linalg.norm(emb_j)))
                    if cos > cosine_threshold:
                        print(f"      [Doublon] Faces {i} et {j} : cosine={cos:.4f} > {cosine_threshold} (même personne dupliquée)")
                        return f"Doublon: même personne détectée 2 fois (faces {i},{j} cosine={cos:.2f})"

            if self.verbose:
                print(f"      [Doublon] {len(faces)} faces, aucun doublon (toutes paires < {cosine_threshold})")
            return None

        except Exception as e:
            if self.verbose:
                print(f"      ⚠️ Duplicate check error: {e}")
            return None

    def _get_deepface_score(self, img1: str, img2: str) -> float:
        """Obtient le score DeepFace (converti en 0-1)."""
        try:
            result = DeepFace.verify(
                img1_path=img1,
                img2_path=img2,
                model_name="VGG-Face",
                enforce_detection=False,
                detector_backend="retinaface"
            )

            # DeepFace retourne une distance, on convertit en score
            # Distance typique: 0-1.0, où < 0.4 = même personne
            distance = result.get("distance", 1.0)
            threshold = result.get("threshold", 0.4)

            # Conversion en score 0-1 (1 = identique)
            # Score = 1 - (distance / (threshold * 2))
            score = max(0, min(1, 1 - (distance / (threshold * 2))))

            print(f"      [DeepFace] distance={distance:.4f} threshold={threshold:.4f} → score={score:.4f}")
            return score

        except Exception as e:
            if self.verbose:
                print(f"      ⚠️ DeepFace error: {e}")
            return 0.5  # Score neutre en cas d'erreur

    def _get_arcface_score(self, img1: str, img2: str) -> float:
        """Obtient le score ArcFace (similarité cosinus convertie en 0-1)."""
        try:
            import cv2

            # Charger les images
            img1_cv = cv2.imread(img1)
            img2_cv = cv2.imread(img2)

            if img1_cv is None or img2_cv is None:
                return 0.5

            # Détecter les visages et extraire les embeddings
            faces1 = self.arcface_app.get(img1_cv)
            faces2 = self.arcface_app.get(img2_cv)

            if not faces1 or not faces2:
                if self.verbose:
                    print(f"      ⚠️ ArcFace: visage non détecté")
                return 0.5

            # img1=generated, img2=reference
            # Référence: premier visage de la photo user (1 seul visage)
            emb_ref = faces2[0].embedding

            # Image générée: trouver le visage le plus similaire à la référence
            best_cosine = -1.0
            for face in faces1:
                emb_gen = face.embedding
                cos = float(np.dot(emb_ref, emb_gen) / (np.linalg.norm(emb_ref) * np.linalg.norm(emb_gen)))
                if cos > best_cosine:
                    best_cosine = cos

            cosine_sim = best_cosine

            # Conversion en score 0-1 (cosine_sim est entre -1 et 1)
            score = (cosine_sim + 1) / 2

            print(f"      [ArcFace] cosine_sim={cosine_sim:.4f} faces_detected=({len(faces1)},{len(faces2)}) best_of={len(faces1)} → score={score:.4f}")
            return float(score)

        except Exception as e:
            if self.verbose:
                print(f"      ⚠️ ArcFace error: {e}")
            return 0.5

    def _save_rejected(
        self,
        image_path: str,
        scores: Dict[str, float],
        gap: float,
        reason: str,
        scene_id: int,
        kf_type: str,
        attempt: int
    ):
        """Sauvegarde une image rejetée avec ses métadonnées."""
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

        # Nom du fichier
        timestamp = datetime.now().strftime("%H%M%S")
        sid = f"{scene_id:02d}" if isinstance(scene_id, int) else str(scene_id)
        filename = f"scene{sid}_{kf_type}_att{attempt}_{timestamp}.png"
        dest_path = self.rejected_dir / filename

        # Copier l'image
        try:
            shutil.copy2(image_path, dest_path)
        except Exception as e:
            print(f"      ⚠️ Erreur copie image rejetée: {e}")
            return

        # Sauvegarder les métadonnées
        meta = {
            "original_path": str(image_path),
            "scene_id": scene_id,
            "keyframe_type": kf_type,
            "attempt": attempt,
            "scores": scores,
            "cumulative_gap": gap,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        meta_path = self.rejected_dir / f"{filename}.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # Ajouter aux stats
        self.stats["rejected_details"].append(meta)

        if self.verbose:
            print(f"      📁 Rejetée sauvegardée: {filename}")

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de validation."""
        return self.stats

    def get_summary(self) -> str:
        """Retourne un résumé textuel."""
        total = self.stats["total_validations"]
        if total == 0:
            return "Aucune validation faciale effectuée"

        passed = self.stats["passed"]
        rejected = self.stats["rejected"]
        rate = (passed / total) * 100

        summary = f"Validation faciale: {passed}/{total} ({rate:.0f}%)"
        if rejected > 0:
            summary += f"\n   Images rejetées: {self.rejected_dir}"

        return summary

    def get_data(self) -> Dict[str, Any]:
        """Retourne les données de validation en format JSON-serializable."""
        total = self.stats["total_validations"]
        return {
            "total_validations": total,
            "passed": self.stats["passed"],
            "rejected": self.stats["rejected"],
            "pass_rate": (self.stats["passed"] / total * 100) if total > 0 else 0,
            "rejected_details": self.stats["rejected_details"],
            "config": {
                "threshold": self.threshold,
                "tolerance": self.tolerance,
            }
        }
