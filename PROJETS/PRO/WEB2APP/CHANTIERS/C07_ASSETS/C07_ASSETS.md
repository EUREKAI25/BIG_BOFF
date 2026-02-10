# CHANTIER 07 — ASSETS (Extraction & Optimisation)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**

---

## OBJECTIF
Extraire, télécharger et optimiser tous les assets du site (images, fonts, icons) pour l'app native.

## PRÉREQUIS
- C01 Parser (liste des assets)

## OUTPUTS
```
assets/
├── images/          # Images optimisées
├── fonts/           # Fonts téléchargées
├── icons/           # Icônes SVG → PNG ou composants
└── manifest.json    # Mapping des assets
```

---

## FONCTIONNALITÉS

### 1. Téléchargement des images
- Télécharger toutes les images référencées
- Convertir en formats optimisés (WebP pour Android, HEIC pour iOS optionnel)
- Générer des versions @1x, @2x, @3x

### 2. Extraction des fonts
- Identifier les fonts Google Fonts utilisées
- Télécharger les fichiers TTF/OTF
- Configurer expo-font

### 3. Conversion des icônes
- SVG → Composant react-native-svg
- Ou SVG → PNG multi-résolution
- Mapping vers Lucide/Expo icons si possible

---

## SERVICE

### asset_service.py

```python
import httpx
import asyncio
from pathlib import Path
from PIL import Image
from io import BytesIO
from ..parser.models import Asset, ParsedSite

class AssetService:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "assets" / "images"
        self.fonts_dir = self.output_dir / "assets" / "fonts"
        self.icons_dir = self.output_dir / "assets" / "icons"
        
        # Créer les dossiers
        for d in [self.images_dir, self.fonts_dir, self.icons_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    async def process_assets(self, site: ParsedSite) -> dict:
        """Traite tous les assets du site."""
        manifest = {
            "images": [],
            "fonts": [],
            "icons": [],
        }
        
        async with httpx.AsyncClient() as client:
            # Images
            for asset in site.assets:
                if asset.asset_type == "image":
                    result = await self._process_image(client, asset)
                    if result:
                        manifest["images"].append(result)
                
                elif asset.asset_type == "font":
                    result = await self._process_font(client, asset)
                    if result:
                        manifest["fonts"].append(result)
            
            # Fonts depuis metadata
            for font in site.metadata.fonts_used:
                result = await self._download_google_font(client, font)
                if result and result not in manifest["fonts"]:
                    manifest["fonts"].append(result)
        
        # Sauvegarder le manifest
        self._save_manifest(manifest)
        
        return manifest
    
    async def _process_image(self, client: httpx.AsyncClient, asset: Asset) -> dict:
        """Télécharge et optimise une image."""
        try:
            response = await client.get(asset.url, timeout=30)
            if response.status_code != 200:
                return None
            
            # Ouvrir avec Pillow
            img = Image.open(BytesIO(response.content))
            
            # Générer un nom de fichier
            filename = self._slugify_url(asset.url)
            
            # Sauvegarder en plusieurs résolutions
            saved_files = []
            for scale, suffix in [(1, ""), (2, "@2x"), (3, "@3x")]:
                scaled = img.copy()
                if scale > 1:
                    new_size = (img.width * scale, img.height * scale)
                    scaled = img.resize(new_size, Image.Resampling.LANCZOS)
                
                filepath = self.images_dir / f"{filename}{suffix}.png"
                scaled.save(filepath, "PNG", optimize=True)
                saved_files.append(str(filepath.relative_to(self.output_dir)))
            
            return {
                "original_url": asset.url,
                "local_path": f"assets/images/{filename}.png",
                "files": saved_files,
                "width": img.width,
                "height": img.height,
            }
            
        except Exception as e:
            print(f"Erreur traitement image {asset.url}: {e}")
            return None
    
    async def _process_font(self, client: httpx.AsyncClient, asset: Asset) -> dict:
        """Télécharge une font."""
        try:
            response = await client.get(asset.url, timeout=30)
            if response.status_code != 200:
                return None
            
            # Extraire le nom de la font
            filename = asset.url.split("/")[-1]
            filepath = self.fonts_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            return {
                "name": filename.replace(".ttf", "").replace(".otf", ""),
                "local_path": f"assets/fonts/{filename}",
            }
            
        except Exception as e:
            print(f"Erreur téléchargement font {asset.url}: {e}")
            return None
    
    async def _download_google_font(self, client: httpx.AsyncClient, font_name: str) -> dict:
        """Télécharge une font depuis Google Fonts."""
        # Nettoyer le nom
        clean_name = font_name.strip().replace(" ", "+")
        
        # Skip les fonts système
        system_fonts = ["system-ui", "-apple-system", "sans-serif", "serif", "monospace"]
        if clean_name.lower() in [f.lower() for f in system_fonts]:
            return None
        
        try:
            # API Google Fonts
            url = f"https://fonts.googleapis.com/css2?family={clean_name}:wght@400;500;600;700&display=swap"
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0"  # Nécessaire pour obtenir les TTF
            })
            
            if response.status_code != 200:
                return None
            
            # Extraire les URLs des fonts du CSS
            import re
            font_urls = re.findall(r'url\((https://[^)]+\.ttf)\)', response.text)
            
            for font_url in font_urls[:1]:  # Juste le regular pour simplifier
                font_response = await client.get(font_url)
                if font_response.status_code == 200:
                    filename = f"{clean_name.replace('+', '')}-Regular.ttf"
                    filepath = self.fonts_dir / filename
                    
                    with open(filepath, "wb") as f:
                        f.write(font_response.content)
                    
                    return {
                        "name": clean_name.replace("+", " "),
                        "local_path": f"assets/fonts/{filename}",
                    }
            
            return None
            
        except Exception as e:
            print(f"Erreur téléchargement Google Font {font_name}: {e}")
            return None
    
    def _slugify_url(self, url: str) -> str:
        """Convertit une URL en nom de fichier."""
        import hashlib
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        path = parsed.path.split("/")[-1].split(".")[0] or "image"
        hash_suffix = hashlib.md5(url.encode()).hexdigest()[:6]
        
        return f"{path}_{hash_suffix}"
    
    def _save_manifest(self, manifest: dict):
        """Sauvegarde le manifest des assets."""
        import json
        
        filepath = self.output_dir / "assets" / "manifest.json"
        with open(filepath, "w") as f:
            json.dump(manifest, f, indent=2)
    
    def generate_font_config(self, manifest: dict) -> str:
        """Génère la config pour expo-font."""
        fonts = manifest.get("fonts", [])
        
        if not fonts:
            return ""
        
        font_map = "\n".join([
            f'  "{f["name"]}": require("./{f["local_path"]}"),'
            for f in fonts
        ])
        
        return f'''
import {{ useFonts }} from 'expo-font';

export function useAppFonts() {{
  const [fontsLoaded] = useFonts({{
{font_map}
  }});
  
  return fontsLoaded;
}}
'''
```

---

## LIVRABLES

```
backend/app/assets/
├── __init__.py
├── asset_service.py
├── image_optimizer.py
├── font_downloader.py
└── icon_converter.py

# Output généré
assets/
├── images/
│   ├── hero_abc123.png
│   ├── hero_abc123@2x.png
│   └── hero_abc123@3x.png
├── fonts/
│   └── Inter-Regular.ttf
└── manifest.json
```

## CRITÈRES DE VALIDATION

- [ ] Télécharge les images
- [ ] Génère @1x, @2x, @3x
- [ ] Télécharge les Google Fonts
- [ ] Crée le manifest
- [ ] Génère la config expo-font

## TEMPS ESTIMÉ
2 heures
