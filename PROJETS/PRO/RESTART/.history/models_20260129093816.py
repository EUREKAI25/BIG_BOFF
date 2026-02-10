# Model.py
# ============================================================================
# Minimal model execution system
# - BaseModel (interface contract)
# - Type models (TextModel, ImageModel, VideoModel, MusicModel)
# - Concrete provider models (Claude, OpenAI, Flux, Runway, Suno…)
# - MODEL_REGISTRY
# - model_execute(type_model, prompt, datas=None)
# ============================================================================


# ----------------------------------------------------------------------------
# Base model interface (contract)
# ----------------------------------------------------------------------------

class BaseModel:
    def __init__(self, name: str, type_model: str):
        self.name = name
        self.type_model = type_model  # "text" | "image" | "video" | "music"

    def execute(self, prompt: str, datas=None):
        raise NotImplementedError("Model must implement execute()")


# ----------------------------------------------------------------------------
# Type models (semantic parents)
# ----------------------------------------------------------------------------

class TextModel(BaseModel):
    def __init__(self, name: str):
        super().__init__(name=name, type_model="text")


class ImageModel(BaseModel):
    def __init__(self, name: str):
        super().__init__(name=name, type_model="image")


class VideoModel(BaseModel):
    def __init__(self, name: str):
        super().__init__(name=name, type_model="video")


class MusicModel(BaseModel):
    def __init__(self, name: str):
        super().__init__(name=name, type_model="music")


# ----------------------------------------------------------------------------
# Concrete provider models (INSTANCES)
# ----------------------------------------------------------------------------

class ClaudeModel(TextModel):
    def __init__(self, name: str, api_key: str, model_id: str):
        super().__init__(name)
        self.api_key = api_key
        self.model_id = model_id

    def execute(self, prompt: str, datas=None):
        # TODO: real Claude API call
        return {
            "ok": True,
            "type_model": self.type_model,
            "model": self.name,
            "provider": "claude",
            "model_id": self.model_id,
            "output": {
                "text": f"[MOCK Claude] {prompt}",
                "datas": datas or {},
            }
        }


class OpenAITextModel(TextModel):
    def __init__(self, name: str, api_key: str, model_id: str):
        super().__init__(name)
        self.api_key = api_key
        self.model_id = model_id

    def execute(self, prompt: str, datas=None):
        return {
            "ok": True,
            "type_model": self.type_model,
            "model": self.name,
            "provider": "openai",
            "model_id": self.model_id,
            "output": {
                "text": f"[MOCK OpenAI] {prompt}",
                "datas": datas or {},
            }
        }


class FluxImageModel(ImageModel):
    def __init__(self, name: str, api_key: str, model_id: str):
        super().__init__(name)
        self.api_key = api_key
        self.model_id = model_id

    def execute(self, prompt: str, datas=None):
        return {
            "ok": True,
            "type_model": self.type_model,
            "model": self.name,
            "provider": "flux",
            "model_id": self.model_id,
            "output": {
                "image_url": "mock://image.png",
                "prompt": prompt,
                "datas": datas or {},
            }
        }


class RunwayVideoModel(VideoModel):
    def __init__(self, name: str, api_key: str, model_id: str):
        super().__init__(name)
        self.api_key = api_key
        self.model_id = model_id

    def execute(self, prompt: str, datas=None):
        return {
            "ok": True,
            "type_model": self.type_model,
            "model": self.name,
            "provider": "runway",
            "model_id": self.model_id,
            "output": {
                "video_url": "mock://video.mp4",
                "prompt": prompt,
                "datas": datas or {},
            }
        }


class SunoMusicModel(MusicModel):
    def __init__(self, name: str, api_key: str, model_id: str):
        super().__init__(name)
        self.api_key = api_key
        self.model_id = model_id

    def execute(self, prompt: str, datas=None):
        return {
            "ok": True,
            "type_model": self.type_model,
            "model": self.name,
            "provider": "suno",
            "model_id": self.model_id,
            "output": {
                "audio_url": "mock://audio.mp3",
                "prompt": prompt,
                "datas": datas or {},
            }
        }


# ----------------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------------

MODEL_REGISTRY = {
    "text": [],
    "image": [],
    "video": [],
    "music": [],
}


def register_model(model: BaseModel):
    t = model.type_model
    if t not in MODEL_REGISTRY:
        MODEL_REGISTRY[t] = []
    MODEL_REGISTRY[t].append(model)


def get_default_model(type_model: str) -> BaseModel:
    models = MODEL_REGISTRY.get(type_model)
    if not models:
        raise ValueError(f"No model registered for type '{type_model}'")
    return models[0]


def get_model(type_model: str, model_name: str) -> BaseModel:
    models = MODEL_REGISTRY.get(type_model, [])
    for m in models:
        if m.name == model_name:
            return m
    raise ValueError(f"Model '{model_name}' not found for type '{type_model}'")


# ----------------------------------------------------------------------------
# Execution entrypoint (YOUR function)
# ----------------------------------------------------------------------------

def model_execute(type_model: str, prompt: str, datas=None, model_name: str = None):
    """
    - Uses first model of the type by default
    - Or a specific model if model_name is provided
    """
    model = (
        get_model(type_model, model_name)
        if model_name
        else get_default_model(type_model)
    )
    return model.execute(prompt, datas=datas)


# ----------------------------------------------------------------------------
# Bootstrap (example)
# ----------------------------------------------------------------------------

def bootstrap_models():
    register_model(
        ClaudeModel(
            name="claude_default",
            api_key="ENV_CLAUDE_KEY",
            model_id="claude-3-5-sonnet"
        )
    )

    register_model(
        OpenAITextModel(
            name="openai_backup",
            api_key="ENV_OPENAI_KEY",
            model_id="gpt-4.1-mini"
        )
    )

    register_model(
        FluxImageModel(
            name="flux_default",
            api_key="ENV_FLUX_KEY",
            model_id="flux-1"
        )
    )

    register_model(
        RunwayVideoModel(
            name="runway_default",
            api_key="ENV_RUNWAY_KEY",
            model_id="gen-3"
        )
    )

    register_model(
        SunoMusicModel(
            name="suno_default",
            api_key="ENV_SUNO_KEY",
            model_id="suno-v3"
        )
    )


# Uncomment if you want auto-registration on import
# bootstrap_models()
