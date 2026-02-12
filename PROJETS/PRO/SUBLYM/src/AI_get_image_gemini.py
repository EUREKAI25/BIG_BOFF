# functions/AI_get_image_gemini.py
"""
Génération d'images avec Google Gemini / Imagen.
Supporte:
- Gemini 3 Pro Image (Nano Banana Pro) - meilleure consistance personnages
- Imagen 3/4 - meilleure qualité photo
- Gemini 2.0 Flash - gratuit
"""

import os
import base64
from typing import Optional, List, Dict, Any
from pathlib import Path

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _load_image_as_base64(image_path: str) -> tuple:
    """Charge une image locale en base64."""
    path = Path(image_path)
    
    # Déterminer le mime type
    ext = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif"
    }
    mime_type = mime_types.get(ext, "image/jpeg")
    
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    
    return data, mime_type


def generate_image_gemini_native(
    prompt: str,
    reference_images: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    model: str = "gemini-2.5-flash-image"
) -> Dict[str, Any]:
    """
    Génère une image avec Gemini natif (génération multimodale).
    
    Avantages:
    - Gratuit/peu cher avec gemini-2.5-flash-image
    - Peut utiliser des images de référence pour le contexte
    - Bon pour l'édition et la transformation
    
    Args:
        prompt: Description de l'image à générer
        reference_images: Liste de chemins/URLs d'images de référence
        aspect_ratio: Ratio ("1:1","2:3","3:2","3:4","4:3","4:5","5:4","9:16","16:9","21:9")
        model: gemini-2.5-flash-image ou gemini-3-pro-image-preview
    
    Returns:
        dict avec 'output' (chemin image) et 'meta'
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("Installez le SDK: pip install google-genai")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY non défini dans .env")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Construire le contenu avec images de référence si fournies
    contents = []
    
    if reference_images:
        for img_path in reference_images[:5]:  # Max 5 images pour consistance personnage
            if img_path.startswith(("http://", "https://")):
                # URL - télécharger d'abord
                import requests
                response = requests.get(img_path)
                img_data = base64.b64encode(response.content).decode("utf-8")
                mime_type = response.headers.get("content-type", "image/jpeg")
            else:
                # Fichier local
                img_data, mime_type = _load_image_as_base64(img_path)
            
            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(img_data),
                    mime_type=mime_type
                )
            )
            print(f"      Ajout référence: {Path(img_path).name if not img_path.startswith('http') else 'URL'}")
    
    # Ajouter le prompt
    contents.append(prompt)
    
    print(f"   [Gemini] Génération image...")
    print(f"   - Modèle: {model}")
    print(f"   - Références: {len(reference_images) if reference_images else 0}")
    
    # Configuration avec aspect ratio pour gemini-2.5-flash-image
    config = types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio
        )
    )
    
    # Générer
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    
    # Vérifier que la réponse est valide
    if not response.candidates:
        raise ValueError("Gemini n'a pas retourné de candidats (possible safety filter)")
    
    candidate = response.candidates[0]
    finish_reason = getattr(candidate, 'finish_reason', None)
    
    if not candidate.content:
        # Debug minimal pour comprendre le refus
        print(f"   [DEBUG] Finish reason: {finish_reason}")
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            print(f"   [DEBUG] Prompt feedback: {response.prompt_feedback}")
        raise ValueError(f"Gemini n'a pas retourné de contenu. Finish reason: {finish_reason}")
    
    if not candidate.content.parts:
        raise ValueError(f"Gemini n'a pas retourné de parts. Finish reason: {finish_reason}")
    
    # Extraire l'image de la réponse
    image_data = None
    text_response = ""
    
    for part in candidate.content.parts:
        if hasattr(part, 'inline_data') and part.inline_data:
            image_data = part.inline_data.data
        elif hasattr(part, 'text') and part.text:
            text_response = part.text
    
    if not image_data:
        raise ValueError(f"Pas d'image dans la réponse. Texte: {text_response}")
    
    # Sauvegarder temporairement
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(image_data)
        output_path = f.name
    
    print(f"   [Gemini] ✓ Image générée: {output_path}")
    
    return {
        "output": output_path,
        "meta": {
            "model": f"google/{model}",
            "cost_eur": 0.0 if "flash" in model else 0.15,  # Flash gratuit
            "text_response": text_response
        }
    }


def generate_image_imagen(
    prompt: str,
    aspect_ratio: str = "16:9",
    number_of_images: int = 1,
    model: str = "imagen-4.0-generate-001"
) -> Dict[str, Any]:
    """
    Génère une image avec Imagen 4 (qualité photo optimale).
    
    Args:
        prompt: Description de l'image
        aspect_ratio: Ratio (16:9, 4:3, 1:1, 3:4, 9:16)
        number_of_images: Nombre d'images à générer (1-4)
        model: imagen-4.0-generate-001
    
    Returns:
        dict avec 'output' (chemin image ou liste) et 'meta'
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("Installez le SDK: pip install google-genai")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY non défini dans .env")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    print(f"   [Imagen] Génération image...")
    print(f"   - Modèle: {model}")
    print(f"   - Nombre: {number_of_images}")
    
    # Utiliser generate_images (avec 's') et GenerateImagesConfig
    result = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=number_of_images,
            output_mime_type="image/png",
            aspect_ratio=aspect_ratio,
            safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            person_generation="ALLOW_ADULT"
        )
    )
    
    # Sauvegarder les images
    import tempfile
    output_paths = []
    
    for i, img in enumerate(result.generated_images):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.image.save(f.name)
            output_paths.append(f.name)
            print(f"   [Imagen] ✓ Image {i+1}: {f.name}")
    
    return {
        "output": output_paths[0] if number_of_images == 1 else output_paths,
        "meta": {
            "model": f"google/{model}",
            "cost_eur": 0.03 * number_of_images,  # $0.03/image
            "images_generated": number_of_images
        }
    }


def generate_image_gemini3_pro(
    prompt: str,
    character_reference_images: Optional[List[str]] = None,
    style_reference_images: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "2K"
) -> Dict[str, Any]:
    """
    Génère une image avec Gemini 3 Pro Image (Nano Banana Pro).
    
    C'est le modèle le plus avancé pour la consistance des personnages!
    Supporte jusqu'à 14 images de référence:
    - 5 images pour consistance personnage
    - 6 images pour objets haute fidélité
    
    Args:
        prompt: Description de l'image
        character_reference_images: Photos du personnage (max 5) pour consistance
        style_reference_images: Images de style/décor (max 6)
        aspect_ratio: Ratio (16:9, 1:1, etc.)
        resolution: "1K", "2K", ou "4K"
    
    Returns:
        dict avec 'output' et 'meta'
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("Installez le SDK: pip install google-genai")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY non défini dans .env")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Construire le prompt avec les références
    contents = []
    
    # Ajouter les images de personnage (pour consistance)
    if character_reference_images:
        contents.append("PRIMARY FACE REFERENCE - CharacterA's face MUST match these photos exactly. Use ONLY these images for CharacterA's facial features, skin tone, and hair:")
        for img_path in character_reference_images[:5]:
            if img_path.startswith(("http://", "https://")):
                import requests
                response = requests.get(img_path)
                img_data = response.content
                mime_type = response.headers.get("content-type", "image/jpeg")
            else:
                with open(img_path, "rb") as f:
                    img_data = f.read()
                _, mime_type = _load_image_as_base64(img_path)
                mime_type = mime_type  # déjà calculé
            
            contents.append(
                types.Part.from_bytes(data=img_data, mime_type=mime_type)
            )
            print(f"      Character ref: {Path(img_path).name if not img_path.startswith('http') else 'URL'}")
    
    # Ajouter les images de style/décor (incluant l'image précédente pour consistance)
    if style_reference_images:
        # La première image est souvent l'image précédente pour la consistance
        contents.append("STYLE/CONTINUITY REFERENCE - Use these for: background, lighting, atmosphere, clothing style, and CharacterB's appearance. WARNING: Do NOT use these for CharacterA's face - use only the PRIMARY FACE REFERENCE above for CharacterA:")
        for img_path in style_reference_images[:6]:
            if img_path.startswith(("http://", "https://")):
                import requests
                response = requests.get(img_path)
                img_data = response.content
                mime_type = response.headers.get("content-type", "image/jpeg")
            else:
                with open(img_path, "rb") as f:
                    img_data = f.read()
                _, mime_type = _load_image_as_base64(img_path)
            
            contents.append(
                types.Part.from_bytes(data=img_data, mime_type=mime_type)
            )
            print(f"      Style ref: {Path(img_path).name if not img_path.startswith('http') else 'URL'}")
    
    # Ajouter le prompt principal
    contents.append(f"Generate this image: {prompt}")
    
    print(f"   [Gemini 3 Pro] Génération image haute qualité...")
    print(f"   - Résolution: {resolution}")
    print(f"   - Character refs: {len(character_reference_images) if character_reference_images else 0}")
    print(f"   - Style refs: {len(style_reference_images) if style_reference_images else 0}")
    
    # Configuration pour Gemini 3 Pro Image
    config = types.GenerateContentConfig(
        response_modalities=['Image', 'Text'],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            # resolution=resolution  # Si supporté
        )
    )
    
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=contents,
        config=config
    )
    
    # Extraire l'image
    image_data = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'inline_data') and part.inline_data:
            image_data = part.inline_data.data
            break
    
    if not image_data:
        raise ValueError("Pas d'image générée")
    
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(image_data)
        output_path = f.name
    
    print(f"   [Gemini 3 Pro] ✓ Image générée: {output_path}")
    
    # Prix approximatif selon résolution
    price_map = {"1K": 0.134, "2K": 0.18, "4K": 0.24}
    
    return {
        "output": output_path,
        "meta": {
            "model": "google/gemini-3-pro-image-preview",
            "cost_eur": price_map.get(resolution, 0.18),
            "resolution": resolution
        }
    }


# =============================================================================
# Fonction principale pour SUBLYM - wrapper intelligent
# =============================================================================

def generate_keyframe_image_gemini(
    prompt: str,
    character_images: Optional[List[str]] = None,
    decor_images: Optional[List[str]] = None,
    previous_image: Optional[str] = None,
    aspect_ratio: str = "16:9",
    provider: str = "gemini-flash"  # "gemini-flash", "imagen", "gemini-3-pro"
) -> Dict[str, Any]:
    """
    Génère une image keyframe avec le provider Gemini choisi.
    
    Args:
        prompt: Le prompt Flux/description de la scène
        character_images: Photos de référence du personnage
        decor_images: Photos de référence du décor
        previous_image: Image précédente pour chaînage
        aspect_ratio: Ratio de l'image
        provider: 
            - "gemini-flash": Gratuit, bon pour tests
            - "imagen": Meilleure qualité photo ($0.03)
            - "gemini-3-pro": Meilleure consistance personnage ($0.18)
    
    Returns:
        dict avec 'output' (chemin image) et 'meta'
    """
    
    print(f"\n   [GEMINI] Génération keyframe avec {provider}")
    
    # Préparer les références
    all_refs = []
    if previous_image:
        all_refs.append(previous_image)
    if character_images:
        all_refs.extend(character_images[:3])
    if decor_images:
        all_refs.extend(decor_images[:2])
    
    if provider == "gemini-flash":
        return generate_image_gemini_native(
            prompt=prompt,
            reference_images=all_refs if all_refs else None,
            aspect_ratio=aspect_ratio,
            model="gemini-2.5-flash-image"
        )
    
    elif provider == "imagen":
        # Imagen ne supporte pas les images de référence directement
        # Mais on peut enrichir le prompt
        return generate_image_imagen(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            number_of_images=1
        )
    
    elif provider == "gemini-3-pro":
        # Pour Gemini 3 Pro, on combine les références:
        # - character_images: photos user pour consistance characterA
        # - previous_image: image précédente pour consistance characterB et décor
        style_refs = list(decor_images) if decor_images else []
        if previous_image:
            style_refs.insert(0, previous_image)  # Previous image en premier pour le contexte
        
        return generate_image_gemini3_pro(
            prompt=prompt,
            character_reference_images=character_images,
            style_reference_images=style_refs if style_refs else None,
            aspect_ratio=aspect_ratio
        )
    
    else:
        raise ValueError(f"Provider inconnu: {provider}")
