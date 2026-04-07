"""
OpenAIProvider — OpenAI (text2text, text2img, img2text, text2audio, audio2text)
"""

from typing import Dict, Any
from .base import BaseProvider


class OpenAIProvider(BaseProvider):

    def __init__(self, api_key: str):
        super().__init__("openai", api_key)

    def execute(self, model_type: str, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import openai
        except ImportError:
            raise ImportError("pip install openai")

        client = openai.OpenAI(api_key=self.api_key)

        dispatch = {
            "text2text":  self._text2text,
            "text2img":   self._text2img,
            "img2text":   self._img2text,
            "text2audio": self._text2audio,
            "audio2text": self._audio2text,
        }
        if model_type not in dispatch:
            raise NotImplementedError(f"OpenAIProvider ne supporte pas {model_type}")

        return dispatch[model_type](client, model, prompt, data)

    def _text2text(self, client, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        system   = data.get("system", "")
        max_tok  = data.get("max_tokens", 2048)
        temp     = data.get("temperature", 0)
        messages = data.get("messages") or []

        if not messages:
            if system:
                messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
            else:
                messages = [{"role": "user", "content": prompt}]

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tok,
            temperature=temp
        )
        text  = resp.choices[0].message.content
        tin   = resp.usage.prompt_tokens
        tout  = resp.usage.completion_tokens
        cost  = (tin / 1000 * 0.005) + (tout / 1000 * 0.015)

        return {
            "result": text,
            "metadata": self._build_metadata(model, cost, tin, tout)
        }

    def _text2img(self, client, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        size    = f"{data.get('width', 1024)}x{data.get('height', 1024)}"
        n       = data.get("n", 1)
        quality = data.get("quality", "standard")

        resp = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n
        )
        urls = [img.url for img in resp.data]
        result = urls[0] if len(urls) == 1 else urls
        cost   = 0.040 * n  # estimation dall-e-3

        return {
            "result": result,
            "metadata": self._build_metadata(model, cost)
        }

    def _img2text(self, client, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        max_tok = data.get("max_tokens", 1024)

        if "image_url" in data:
            content = [
                {"type": "image_url", "image_url": {"url": data["image_url"]}},
                {"type": "text", "text": prompt}
            ]
        elif "image_base64" in data:
            media_type = data.get("media_type", "image/jpeg")
            content = [
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{data['image_base64']}"}},
                {"type": "text", "text": prompt}
            ]
        else:
            raise ValueError("img2text requiert 'image_url' ou 'image_base64' dans data")

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tok
        )
        text = resp.choices[0].message.content
        tin  = resp.usage.prompt_tokens
        tout = resp.usage.completion_tokens
        cost = (tin / 1000 * 0.005)

        return {
            "result": text,
            "metadata": self._build_metadata(model, cost, tin, tout)
        }

    def _text2audio(self, client, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        voice       = data.get("voice", "alloy")
        output_path = data.get("output_path")

        resp = client.audio.speech.create(model=model, voice=voice, input=prompt)
        cost = len(prompt) / 1000 * 0.015

        if output_path:
            resp.stream_to_file(output_path)
            return {
                "result": output_path,
                "metadata": self._build_metadata(model, cost)
            }
        else:
            return {
                "result": resp.content,
                "metadata": self._build_metadata(model, cost)
            }

    def _audio2text(self, client, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        audio_file = data.get("audio_file")
        if not audio_file:
            raise ValueError("audio2text requiert 'audio_file' dans data")

        language = data.get("language")
        kwargs   = {"model": model, "file": open(audio_file, "rb")}
        if language:
            kwargs["language"] = language

        resp = client.audio.transcriptions.create(**kwargs)
        return {
            "result": resp.text,
            "metadata": self._build_metadata(model, 0.0)
        }
