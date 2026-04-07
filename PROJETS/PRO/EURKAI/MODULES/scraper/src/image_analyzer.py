"""
Image Analyzer - Extrait les couleurs dominantes d'un screenshot.
Complète le scraper CSS pour capturer l'harmonie visuelle des médias.
"""
from PIL import Image
import io
import base64
from typing import List, Tuple, Dict
from collections import Counter
import colorsys


class ImageAnalyzer:
    """Analyse les couleurs dominantes d'une image."""

    def analyze_screenshot(self, screenshot_base64: str, num_colors: int = 10) -> Dict:
        """
        Extrait les couleurs dominantes d'un screenshot.

        Args:
            screenshot_base64: Screenshot en base64
            num_colors: Nombre de couleurs à extraire

        Returns:
            {
                "dominant_colors": [(r, g, b), ...],
                "color_percentages": [0.35, 0.22, ...],
                "is_monochrome": bool,
                "color_mood": "warm|cool|neutral|vibrant",
                "zones": {
                    "hero": {"dominant_color": (r, g, b)},
                    "content": {"dominant_color": (r, g, b)}
                }
            }
        """
        # Décoder image
        img_bytes = base64.b64decode(screenshot_base64)
        img = Image.open(io.BytesIO(img_bytes))

        # Réduire la taille pour perf (resize à 400px width)
        ratio = 400 / img.width
        new_size = (400, int(img.height * ratio))
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convertir en RGB
        if img_resized.mode != 'RGB':
            img_resized = img_resized.convert('RGB')

        # Extraire couleurs dominantes
        dominant_colors, percentages = self._extract_dominant_colors(img_resized, num_colors)

        # Analyser zones (hero = top 30%, content = reste)
        zones = self._analyze_zones(img_resized)

        # Déterminer mood
        is_monochrome = self._is_monochrome(dominant_colors)
        color_mood = self._determine_mood(dominant_colors, percentages)

        return {
            "dominant_colors": dominant_colors,
            "color_percentages": percentages,
            "is_monochrome": is_monochrome,
            "color_mood": color_mood,
            "zones": zones,
            "total_pixels": img_resized.width * img_resized.height
        }

    def _extract_dominant_colors(
        self,
        img: Image.Image,
        num_colors: int = 10
    ) -> Tuple[List[Tuple[int, int, int]], List[float]]:
        """
        Extrait les couleurs dominantes par quantization.

        Returns:
            (colors, percentages)
        """
        # Convertir image en liste de pixels
        pixels = list(img.getdata())

        # Quantize avec Pillow (K-means interne)
        img_quant = img.quantize(colors=num_colors)
        palette = img_quant.getpalette()

        # Extraire couleurs de la palette
        colors = []
        for i in range(num_colors):
            r = palette[i*3]
            g = palette[i*3 + 1]
            b = palette[i*3 + 2]
            colors.append((r, g, b))

        # Calculer pourcentages (approximatif)
        # Compter pixels de chaque couleur
        pixel_colors = list(img_quant.getdata())
        total = len(pixel_colors)
        color_counts = Counter(pixel_colors)

        percentages = []
        for i in range(num_colors):
            count = color_counts.get(i, 0)
            percentages.append(count / total)

        # Trier par pourcentage décroissant
        sorted_pairs = sorted(zip(colors, percentages), key=lambda x: x[1], reverse=True)
        colors_sorted = [c for c, _ in sorted_pairs]
        percentages_sorted = [p for _, p in sorted_pairs]

        return colors_sorted, percentages_sorted

    def _analyze_zones(self, img: Image.Image) -> Dict:
        """Analyse les couleurs par zone (hero vs content)."""
        width, height = img.size

        # Hero = top 30%
        hero_zone = img.crop((0, 0, width, int(height * 0.3)))
        hero_color, _ = self._extract_dominant_colors(hero_zone, num_colors=1)

        # Content = middle 40%
        content_zone = img.crop((0, int(height * 0.3), width, int(height * 0.7)))
        content_color, _ = self._extract_dominant_colors(content_zone, num_colors=1)

        return {
            "hero": {
                "dominant_color": hero_color[0] if hero_color else (128, 128, 128)
            },
            "content": {
                "dominant_color": content_color[0] if content_color else (128, 128, 128)
            }
        }

    def _is_monochrome(self, colors: List[Tuple[int, int, int]]) -> bool:
        """Détermine si la palette est monochrome (tons de gris)."""
        monochrome_count = 0

        for r, g, b in colors[:5]:  # Top 5 couleurs
            # Vérifier si les 3 composantes sont proches (±20)
            if abs(r - g) < 20 and abs(g - b) < 20 and abs(r - b) < 20:
                monochrome_count += 1

        # Si 4+ des 5 couleurs principales sont grises → monochrome
        return monochrome_count >= 4

    def _determine_mood(
        self,
        colors: List[Tuple[int, int, int]],
        percentages: List[float]
    ) -> str:
        """
        Détermine le mood des couleurs.

        Returns:
            "warm" | "cool" | "neutral" | "vibrant"
        """
        if not colors:
            return "neutral"

        # Analyser les 3 couleurs principales (weighted)
        total_hue = 0
        total_sat = 0
        total_weight = 0

        for i, (r, g, b) in enumerate(colors[:3]):
            weight = percentages[i] if i < len(percentages) else 0

            # Convertir en HSV
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

            total_hue += h * weight
            total_sat += s * weight
            total_weight += weight

        if total_weight == 0:
            return "neutral"

        avg_hue = total_hue / total_weight
        avg_sat = total_sat / total_weight

        # Faible saturation → neutral
        if avg_sat < 0.2:
            return "neutral"

        # Haute saturation → vibrant
        if avg_sat > 0.6:
            return "vibrant"

        # Hue : warm (rouge/orange/jaune) vs cool (bleu/vert)
        # Hue : 0-60 = rouge/orange, 60-180 = jaune/vert, 180-300 = cyan/bleu, 300-360 = magenta/rouge
        hue_degrees = avg_hue * 360

        if hue_degrees < 60 or hue_degrees > 300:
            return "warm"  # Rouge, orange, magenta
        elif 60 <= hue_degrees < 180:
            return "warm"  # Jaune, vert chaud
        else:
            return "cool"  # Bleu, cyan, vert froid


if __name__ == "__main__":
    # Test avec screenshot myhealthprac
    import sys
    from pathlib import Path

    screenshot_path = Path("../output_myhealthprac/screenshot.png")
    if not screenshot_path.exists():
        print("❌ Screenshot non trouvé")
        sys.exit(1)

    # Charger screenshot en base64
    screenshot_bytes = screenshot_path.read_bytes()
    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

    # Analyser
    analyzer = ImageAnalyzer()
    result = analyzer.analyze_screenshot(screenshot_b64, num_colors=10)

    print("🎨 Analyse du screenshot myhealthprac.com :")
    print(f"\n   Monochrome : {result['is_monochrome']}")
    print(f"   Mood : {result['color_mood']}")
    print(f"\n   Couleurs dominantes :")

    for i, (color, pct) in enumerate(zip(result['dominant_colors'][:10], result['color_percentages'][:10])):
        r, g, b = color
        print(f"      {i+1}. rgb({r}, {g}, {b}) - {pct*100:.1f}%")

    print(f"\n   Zone Hero : rgb{result['zones']['hero']['dominant_color']}")
    print(f"   Zone Content : rgb{result['zones']['content']['dominant_color']}")
