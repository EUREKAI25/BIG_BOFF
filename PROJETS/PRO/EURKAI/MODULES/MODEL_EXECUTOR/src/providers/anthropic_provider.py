"""
AnthropicProvider — Anthropic Claude (text2text, img2text)
"""

from typing import Dict, Any
from .base import BaseProvider


class AnthropicProvider(BaseProvider):

    def __init__(self, api_key: str):
        super().__init__("anthropic", api_key)

    def execute(self, model_type: str, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        if model_type == "text2text":
            return self._text2text(client, model, prompt, data)
        elif model_type == "img2text":
            return self._img2text(client, model, prompt, data)
        else:
            raise NotImplementedError(f"AnthropicProvider ne supporte pas {model_type}")

    def _text2text(self, client, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        system    = data.get("system", "")
        max_tok   = data.get("max_tokens", 2048)
        temp      = data.get("temperature", 0)
        messages  = data.get("messages") or [{"role": "user", "content": prompt}]

        kwargs = dict(model=model, max_tokens=max_tok, messages=messages)
        if system:
            kwargs["system"] = system
        if temp != 0:
            kwargs["temperature"] = temp

        resp = client.messages.create(**kwargs)
        text = resp.content[0].text
        tin  = resp.usage.input_tokens
        tout = resp.usage.output_tokens
        cost = self._calc_cost("text2text", tin, tout)

        return {
            "result": text,
            "metadata": self._build_metadata(model, cost, tin, tout)
        }

    def _img2text(self, client, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        max_tok = data.get("max_tokens", 1024)

        # Construire le content image
        if "image_url" in data:
            image_block = {
                "type": "image",
                "source": {"type": "url", "url": data["image_url"]}
            }
        elif "image_base64" in data:
            media_type = data.get("media_type", "image/jpeg")
            image_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": data["image_base64"]
                }
            }
        else:
            raise ValueError("img2text requiert 'image_url' ou 'image_base64' dans data")

        messages = [{"role": "user", "content": [image_block, {"type": "text", "text": prompt}]}]
        resp = client.messages.create(model=model, max_tokens=max_tok, messages=messages)

        text = resp.content[0].text
        tin  = resp.usage.input_tokens
        tout = resp.usage.output_tokens
        cost = self._calc_cost("img2text", tin, tout)

        return {
            "result": text,
            "metadata": self._build_metadata(model, cost, tin, tout)
        }

    def _calc_cost(self, model_type: str, tokens_in: int, tokens_out: int) -> float:
        rates = {
            "text2text": (0.015, 0.075),
            "img2text":  (0.015, 0.075),
        }
        r_in, r_out = rates.get(model_type, (0, 0))
        return (tokens_in / 1000 * r_in) + (tokens_out / 1000 * r_out)
