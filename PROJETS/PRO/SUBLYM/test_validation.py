#!/usr/bin/env python3
"""Test validation resemblance"""

import sys
import glob
from pathlib import Path
sys.path.insert(0, 'src')
from validation_images_v2 import ImageValidatorV2

# Trouver première image de référence
ref_dir = "/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM_APP_PUB/Avatars/Mickael/photos/"
ref_images = sorted(glob.glob(str(Path(ref_dir) / "*.png")))
if not ref_images:
    print("❌ Aucune image de référence trouvée")
    sys.exit(1)

ref_img = ref_images[0]
test_img = "generated_images_mickael_final/scene_01_start.png"

print(f"Image ref: {ref_img}")
print(f"Existe: {Path(ref_img).exists()}")
print(f"Image test: {test_img}")
print(f"Existe: {Path(test_img).exists()}")
print()

try:
    validator = ImageValidatorV2(reference_image=ref_img)
    result = validator.validate_resemblance(test_img)

    print(f"Score: {result['score']}")
    print(f"Face detected: {result.get('face_detected', False)}")
    print(f"Passed: {result.get('passed', False)}")
    print(f"Comments: {result.get('comments', 'N/A')}")
    print(f"Similarities: {result.get('similarities', [])}")
    print(f"Differences: {result.get('differences', [])}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
