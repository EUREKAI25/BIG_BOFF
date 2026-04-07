"""Test simple du scraper seul."""
from scraper import SiteScraper
import json
from pathlib import Path

output_dir = Path("output_myhealthprac")
output_dir.mkdir(exist_ok=True)

print("="*60)
print("  TEST SCRAPER - myhealthprac.com")
print("="*60)

print("\n🔍 Scraping...")
scraper = SiteScraper()

try:
    raw_styles = scraper.scrape("https://www.myhealthprac.com/", screenshot=True)

    print(f"\n✅ Extraction réussie :")
    print(f"   - {len(raw_styles.colors)} couleurs")
    print(f"   - {len(raw_styles.backgrounds)} backgrounds")
    print(f"   - {len(raw_styles.shadows)} shadows")
    print(f"   - {len(raw_styles.fonts)} fonts")
    print(f"   - {len(raw_styles.component_styles['buttons'])} boutons")
    print(f"   - Screenshot: {'✓' if raw_styles.screenshot_base64 else '✗'}")

    # Sauvegarder
    raw_path = output_dir / "raw_styles.json"
    with open(raw_path, 'w') as f:
        json.dump(raw_styles.model_dump(exclude={'screenshot_base64'}), f, indent=2)

    print(f"\n💾 Sauvegardé : {raw_path}")

    # Afficher couleurs
    print(f"\n🎨 Couleurs :")
    for i, color in enumerate(raw_styles.colors[:10]):
        print(f"   {i+1}. {color}")

    # Afficher fonts
    print(f"\n📝 Fonts :")
    for i, font in enumerate(raw_styles.fonts[:5]):
        print(f"   {i+1}. {font}")

    print(f"\n✅ Test réussi ! Fichier : {raw_path}")

except Exception as e:
    print(f"\n❌ Erreur : {e}")
    import traceback
    traceback.print_exc()
