"""
ReplicateProvider — Replicate (text2img, img2img)
"""

import os
from typing import Dict, Any
from .base import BaseProvider


class ReplicateProvider(BaseProvider):

    def __init__(self, api_key: str):
        super().__init__("replicate", api_key)

    def execute(self, model_type: str, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import replicate
        except ImportError:
            raise ImportError("pip install replicate")

        # Replicate utilise la variable d'env REPLICATE_API_TOKEN
        os.environ["REPLICATE_API_TOKEN"] = self.api_key

        if model_type == "text2img":
            return self._text2img(replicate, model, prompt, data)
        elif model_type == "img2img":
            return self._img2img(replicate, model, prompt, data)
        else:
            raise NotImplementedError(f"ReplicateProvider ne supporte pas {model_type}")

    def _text2img(self, replicate, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        model_id = data.get("model_id", model)

        inp: Dict[str, Any] = {"prompt": prompt}
        for key in ("width", "height", "aspect_ratio", "num_outputs", "num_inference_steps",
                    "guidance_scale", "output_format", "output_quality", "negative_prompt"):
            if key in data:
                inp[key] = data[key]

        output = replicate.run(model_id, input=inp)

        # Replicate retourne une liste d'URLs ou un itérable
        if hasattr(output, "__iter__") and not isinstance(output, str):
            urls = list(output)
        else:
            urls = [output]

        result = urls[0] if len(urls) == 1 else urls

        return {
            "result": result,
            "metadata": self._build_metadata(model, 0.05)
        }

    def _img2img(self, replicate, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        model_id = data.get("model_id", model)

        inp: Dict[str, Any] = {"prompt": prompt}
        for key in ("image", "mask", "strength", "guidance_scale", "num_outputs",
                    "num_inference_steps", "negative_prompt"):
            if key in data:
                inp[key] = data[key]

        output = replicate.run(model_id, input=inp)

        if hasattr(output, "__iter__") and not isinstance(output, str):
            urls = list(output)
        else:
            urls = [output]

        result = urls[0] if len(urls) == 1 else urls

        return {
            "result": result,
            "metadata": self._build_metadata(model, 0.02)
        }
