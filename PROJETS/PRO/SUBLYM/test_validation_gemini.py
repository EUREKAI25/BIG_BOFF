"""
Test de validation de l'image Gemini 3 Pro
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from validation_images_v2 import ImageValidatorV2

# Image de test générée
test_image = "outputs/test_gemini_direct.png"

# Image de référence - utiliser Path pour gérer correctement les noms de fichiers avec accents
photos_dir = Path("/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM_APP_PUB/Avatars/Mickael/photos")
ref_images = sorted(photos_dir.glob("*.png"))
if not ref_images:
    print("❌ Aucune image de référence trouvée")
    sys.exit(1)
ref_image = str(ref_images[0])

print("🔍 TEST VALIDATION GEMINI 3 PRO")
print("="*70)
print(f"Image générée: {test_image}")
print(f"Image référence: {ref_image}")
print("="*70)

# Créer le validateur
validator = ImageValidatorV2(reference_image=ref_image)

# Test 1: Qualité
print("\n1. QUALITÉ TECHNIQUE")
quality = validator.validate_quality(test_image)
print(f"   Score: {quality['score']:.2f}")
print(f"   Visage visible: {quality.get('face_visible', False)}")
print(f"   Validé: {'✅' if quality['passed'] else '❌'}")
if quality.get('issues'):
    print(f"   Issues: {quality['issues']}")

# Test 2: Ressemblance
print("\n2. RESSEMBLANCE FACIALE")
resemblance = validator.validate_resemblance(test_image)
print(f"   Score: {resemblance['score']:.2f}")
print(f"   Visage détecté: {resemblance.get('face_detected', False)}")
print(f"   Couleur peau match: {resemblance.get('skin_tone_match', False)}")
print(f"   Cheveux match: {resemblance.get('hair_match', False)}")
print(f"   Accessoires match: {resemblance.get('accessories_match', False)}")
print(f"   Traits match: {resemblance.get('facial_features_match', False)}")
print(f"   Validé: {'✅' if resemblance['passed'] else '❌'}")
print(f"   Commentaire: {resemblance.get('comments', '')}")
if resemblance.get('differences'):
    print(f"   Différences: {resemblance['differences']}")
if resemblance.get('critical_failures'):
    print(f"   ⚠️  Échecs critiques: {resemblance['critical_failures']}")

# Test 3: Copie de référence
print("\n3. VÉRIFICATION COPIE RÉFÉRENCE")
ref_copy = validator.check_reference_copy(test_image)
print(f"   Similarité: {ref_copy['similarity']:.2f}")
print(f"   Est une copie: {'❌ OUI' if ref_copy['is_copy'] else '✅ NON'}")
if ref_copy.get('reasons'):
    print(f"   Raisons: {ref_copy['reasons']}")

# Test 4: Dents visibles
print("\n4. DENTS VISIBLES (RÉDHIBITOIRE)")
teeth = validator.check_teeth_visible(test_image)
print(f"   Dents visibles: {'❌ OUI' if teeth['teeth_visible'] else '✅ NON'}")
print(f"   Confiance: {teeth['confidence']:.2f}")
print(f"   Description bouche: {teeth['mouth_description']}")
print(f"   Verdict: {teeth['verdict']}")

# Test 5: Regard caméra
print("\n5. REGARD CAMÉRA (RÉDHIBITOIRE)")
eye = validator.check_eye_contact(test_image)
print(f"   Regarde caméra: {'❌ OUI' if eye['looking_at_camera'] else '✅ NON'}")
print(f"   Confiance: {eye['confidence']:.2f}")
print(f"   Direction regard: {eye['gaze_direction']}")
print(f"   Verdict: {eye['verdict']}")

# Résumé
print("\n" + "="*70)
print("RÉSUMÉ VALIDATION")
print("="*70)
validation_passed = (
    quality['passed'] and
    resemblance['passed'] and
    not ref_copy['is_copy'] and
    teeth['passed'] and
    eye['passed']
)
print(f"✅ Qualité: {quality['passed']}")
print(f"✅ Ressemblance: {resemblance['passed']} (score: {resemblance['score']:.2f})")
print(f"✅ Pas copie: {not ref_copy['is_copy']}")
print(f"✅ Dents: {teeth['passed']}")
print(f"✅ Regard: {eye['passed']}")
print("="*70)
print(f"VALIDATION GLOBALE: {'✅ PASSÉ' if validation_passed else '❌ ÉCHOUÉ'}")
print("="*70)
