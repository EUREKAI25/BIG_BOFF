"""
GeminiProvider — Google Gemini (text2text, img2text)
"""

from typing import Dict, Any
from .base import BaseProvider


class GeminiProvider(BaseProvider):

    def __init__(self, api_key: str):
        super().__init__("gemini", api_key)

    def execute(self, model_type: str, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("pip install google-generativeai")

        genai.configure(api_key=self.api_key)

        if model_type == "text2text":
            return self._text2text(genai, model, prompt, data)
        elif model_type == "img2text":
            return self._img2text(genai, model, prompt, data)
        else:
            raise NotImplementedError(f"GeminiProvider ne supporte pas {model_type}")

    def _text2text(self, genai, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        system  = data.get("system", "")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        m    = genai.GenerativeModel(model)
        resp = m.generate_content(full_prompt)
        text = resp.text

        tin  = getattr(resp.usage_metadata, "prompt_token_count", 0) or 0
        tout = getattr(resp.usage_metadata, "candidates_token_count", 0) or 0
        cost = (tin / 1000 * 0.00025) + (tout / 1000 * 0.0005)

        return {
            "result": text,
            "metadata": self._build_metadata(model, cost, tin, tout)
        }

    def _img2text(self, genai, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        import base64

        m = genai.GenerativeModel(model)

        if "image_url" in data:
            import urllib.request
            with urllib.request.urlopen(data["image_url"]) as r:
                img_bytes = r.read()
            media_type = data.get("media_type", "image/jpeg")
            img_part   = {"mime_type": media_type, "data": base64.b64encode(img_bytes).decode()}
        elif "image_base64" in data:
            media_type = data.get("media_type", "image/jpeg")
            img_part   = {"mime_type": media_type, "data": data["image_base64"]}
        else:
            raise ValueError("img2text requiert 'image_url' ou 'image_base64' dans data")

        resp = m.generate_content([img_part, prompt])
        text = resp.text

        tin  = getattr(resp.usage_metadata, "prompt_token_count", 0) or 0
        tout = getattr(resp.usage_metadata, "candidates_token_count", 0) or 0
        cost = (tin / 1000 * 0.00025) + (tout / 1000 * 0.0005)

        return {
            "result": text,
            "metadata": self._build_metadata(model, cost, tin, tout)
        }
