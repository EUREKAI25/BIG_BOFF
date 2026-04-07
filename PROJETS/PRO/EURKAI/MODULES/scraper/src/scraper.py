"""
Scraper EURKAI - Extraction des styles réellement appliqués sur un site.
Utilise Playwright + getComputedStyle pour capturer les styles finaux.
"""
from playwright.sync_api import sync_playwright, Page
from typing import Dict, List, Optional
from pydantic import BaseModel
import json
import base64


class RawStyles(BaseModel):
    """Styles bruts extraits d'un site."""
    url: str
    colors: List[str]
    backgrounds: List[str]
    shadows: List[str]
    borders: List[str]
    border_radius: List[str]
    fonts: List[str]
    component_styles: Dict[str, List[Dict]]
    screenshot_base64: Optional[str] = None


class SiteScraper:
    """Scraper de sites web pour extraction de design tokens."""

    EXTRACT_STYLES_SCRIPT = """
    () => {
        const styles = {
            colors: new Set(),
            backgrounds: new Set(),
            shadows: new Set(),
            borders: new Set(),
            borderRadius: new Set(),
            fonts: new Set(),
            componentStyles: {
                buttons: [],
                inputs: [],
                cards: [],
                headings: []
            }
        };

        // Parcourir TOUS les éléments visibles
        const elements = document.querySelectorAll('*');

        elements.forEach(el => {
            // Skip éléments invisibles
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            // Computed style (style final après cascade CSS)
            const computed = window.getComputedStyle(el);

            // === Extraction tokens globaux ===

            // Couleurs
            if (computed.color && computed.color !== 'rgba(0, 0, 0, 0)') {
                styles.colors.add(computed.color);
            }
            if (computed.backgroundColor && computed.backgroundColor !== 'rgba(0, 0, 0, 0)') {
                styles.backgrounds.add(computed.backgroundColor);
            }

            // Shadows
            if (computed.boxShadow && computed.boxShadow !== 'none') {
                styles.shadows.add(computed.boxShadow);
            }

            // Borders
            if (computed.border && computed.border !== '0px none rgb(0, 0, 0)') {
                styles.borders.add(computed.border);
            }
            if (computed.borderRadius && computed.borderRadius !== '0px') {
                styles.borderRadius.add(computed.borderRadius);
            }

            // Fonts
            if (computed.fontFamily) {
                styles.fonts.add(computed.fontFamily);
            }

            // === Analyse par composant ===

            const tagName = el.tagName.toLowerCase();
            const className = el.className?.toString() || '';
            const text = el.textContent?.trim().substring(0, 30) || '';

            // Boutons
            if (tagName === 'button' ||
                (tagName === 'a' && (className.includes('btn') || className.includes('button')))) {
                styles.componentStyles.buttons.push({
                    text: text,
                    tag: tagName,
                    class: className,
                    backgroundColor: computed.backgroundColor,
                    color: computed.color,
                    boxShadow: computed.boxShadow,
                    borderRadius: computed.borderRadius,
                    padding: computed.padding,
                    fontSize: computed.fontSize,
                    fontWeight: computed.fontWeight,
                    border: computed.border,
                    textTransform: computed.textTransform,
                    letterSpacing: computed.letterSpacing
                });
            }

            // Inputs
            if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
                styles.componentStyles.inputs.push({
                    type: el.type || tagName,
                    backgroundColor: computed.backgroundColor,
                    color: computed.color,
                    borderColor: computed.borderColor,
                    borderRadius: computed.borderRadius,
                    padding: computed.padding,
                    fontSize: computed.fontSize,
                    border: computed.border
                });
            }

            // Cards (heuristique: shadow + border-radius + taille min)
            if (computed.boxShadow !== 'none' &&
                computed.borderRadius !== '0px' &&
                rect.width > 150 && rect.height > 100) {
                styles.componentStyles.cards.push({
                    backgroundColor: computed.backgroundColor,
                    boxShadow: computed.boxShadow,
                    borderRadius: computed.borderRadius,
                    padding: computed.padding,
                    border: computed.border,
                    width: rect.width,
                    height: rect.height
                });
            }

            // Headings (h1-h6)
            if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
                styles.componentStyles.headings.push({
                    tag: tagName,
                    text: text,
                    color: computed.color,
                    fontSize: computed.fontSize,
                    fontWeight: computed.fontWeight,
                    fontFamily: computed.fontFamily,
                    lineHeight: computed.lineHeight,
                    letterSpacing: computed.letterSpacing,
                    textTransform: computed.textTransform
                });
            }
        });

        // Convertir Sets en Arrays pour JSON
        return {
            colors: Array.from(styles.colors),
            backgrounds: Array.from(styles.backgrounds),
            shadows: Array.from(styles.shadows),
            borders: Array.from(styles.borders),
            borderRadius: Array.from(styles.borderRadius),
            fonts: Array.from(styles.fonts),
            componentStyles: styles.componentStyles
        };
    }
    """

    def scrape(self, url: str, screenshot: bool = True) -> RawStyles:
        """
        Scrape un site et extrait les styles réellement appliqués.

        Args:
            url: URL du site à scraper
            screenshot: Capturer un screenshot (pour analyse LLM)

        Returns:
            RawStyles avec tous les tokens extraits
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            # Charger la page
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Attendre que le contenu soit visible
            page.wait_for_timeout(2000)

            # Extraire les styles via JavaScript
            raw_data = page.evaluate(self.EXTRACT_STYLES_SCRIPT)

            # Screenshot (optionnel)
            screenshot_b64 = None
            if screenshot:
                screenshot_bytes = page.screenshot(full_page=False)  # Viewport seulement
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            browser.close()

        # Construire RawStyles
        return RawStyles(
            url=url,
            colors=raw_data['colors'],
            backgrounds=raw_data['backgrounds'],
            shadows=raw_data['shadows'],
            borders=raw_data['borders'],
            border_radius=raw_data['borderRadius'],
            fonts=raw_data['fonts'],
            component_styles=raw_data['componentStyles'],
            screenshot_base64=screenshot_b64
        )

    def scrape_to_json(self, url: str, output_path: str):
        """Scrape et sauvegarde en JSON."""
        styles = self.scrape(url)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(styles.model_dump(), f, indent=2, ensure_ascii=False)
        return styles


if __name__ == "__main__":
    # Test
    scraper = SiteScraper()

    print("🔍 Test scraping sur Stripe.com...")
    styles = scraper.scrape("https://stripe.com")

    print(f"\n✅ Extraction terminée :")
    print(f"   - {len(styles.colors)} couleurs")
    print(f"   - {len(styles.backgrounds)} backgrounds")
    print(f"   - {len(styles.shadows)} shadows")
    print(f"   - {len(styles.fonts)} fonts")
    print(f"   - {len(styles.component_styles['buttons'])} boutons")
    print(f"   - {len(styles.component_styles['inputs'])} inputs")
    print(f"   - Screenshot: {'✓' if styles.screenshot_base64 else '✗'}")

    # Sauvegarder
    scraper.scrape_to_json("https://stripe.com", "stripe_styles.json")
    print(f"\n💾 Sauvegardé dans stripe_styles.json")
