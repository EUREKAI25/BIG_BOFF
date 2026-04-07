"""
Tests — MODEL_EXECUTOR
Teste la config, le routing, les providers (mocks) et la fonction model_execute.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ajouter MODULES au path
_MODULES = Path(__file__).parent.parent.parent
if str(_MODULES) not in sys.path:
    sys.path.insert(0, str(_MODULES))

from MODEL_EXECUTOR.src.config import Config
from MODEL_EXECUTOR.src.executor import model_execute, _execute_with_provider
from MODEL_EXECUTOR.src.providers.base import BaseProvider


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _fake_result(text="ok") -> dict:
    return {
        "result": text,
        "metadata": {"provider": "mock", "model": "mock", "cost_usd": 0.0,
                     "tokens_input": 10, "tokens_output": 5}
    }


# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.cfg = Config()

    def test_active_provider_text2text(self):
        p = self.cfg.get_active_provider("text2text")
        self.assertIn(p, ("openai", "anthropic", "gemini"))

    def test_active_provider_text2img(self):
        p = self.cfg.get_active_provider("text2img")
        self.assertIn(p, ("replicate", "openai", "fal"))

    def test_fallback_provider_text2text(self):
        p = self.cfg.get_fallback_provider("text2text")
        self.assertIn(p, ("openai", "anthropic", "gemini", None))

    def test_unknown_model_type_returns_none(self):
        p = self.cfg.get_active_provider("does_not_exist")
        self.assertIsNone(p)

    def test_get_model_name_openai_text2text(self):
        m = self.cfg.get_model_name("openai", "text2text")
        self.assertIsNotNone(m)
        self.assertIn("gpt", m)

    def test_get_model_name_anthropic_text2text(self):
        m = self.cfg.get_model_name("anthropic", "text2text")
        self.assertIsNotNone(m)
        self.assertIn("claude", m)

    def test_get_model_name_replicate_text2img(self):
        m = self.cfg.get_model_name("replicate", "text2img")
        self.assertIsNotNone(m)

    def test_get_model_name_unknown_type_returns_none(self):
        m = self.cfg.get_model_name("openai", "img2video")
        self.assertIsNone(m)

    def test_get_api_key_missing_env_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # Supprimer toutes les clés connues
            for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
                os.environ.pop(var, None)
            with self.assertRaises(ValueError):
                self.cfg.get_api_key("openai")

    def test_pricing_text2text_openai(self):
        p = self.cfg.get_pricing("openai", "text2text")
        self.assertIsInstance(p, dict)


# ─────────────────────────────────────────────────────────────
# BaseProvider
# ─────────────────────────────────────────────────────────────

class TestBaseProvider(unittest.TestCase):

    def test_build_metadata_fields(self):
        class ConcreteProvider(BaseProvider):
            def execute(self, *a, **kw): pass

        p = ConcreteProvider("test", "key")
        meta = p._build_metadata("gpt-4o", 0.05, 100, 50)
        self.assertEqual(meta["provider"], "test")
        self.assertEqual(meta["model"], "gpt-4o")
        self.assertEqual(meta["cost_usd"], 0.05)
        self.assertEqual(meta["tokens_input"], 100)
        self.assertEqual(meta["tokens_output"], 50)

    def test_build_metadata_defaults(self):
        class ConcreteProvider(BaseProvider):
            def execute(self, *a, **kw): pass

        p = ConcreteProvider("x", "key")
        meta = p._build_metadata("m")
        self.assertEqual(meta["cost_usd"], 0.0)
        self.assertEqual(meta["tokens_input"], 0)


# ─────────────────────────────────────────────────────────────
# AnthropicProvider (mock)
# ─────────────────────────────────────────────────────────────

class TestAnthropicProvider(unittest.TestCase):

    def _make_provider(self):
        from MODEL_EXECUTOR.src.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider("fake-key")

    def _mock_response(self, text="réponse"):
        resp = MagicMock()
        resp.content = [MagicMock(text=text)]
        resp.usage.input_tokens  = 20
        resp.usage.output_tokens = 10
        return resp

    def test_text2text_returns_result(self):
        p = self._make_provider()
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = self._mock_response("bonjour")
            result = p.execute("text2text", "claude-haiku-4-5", "Dis bonjour", {})
        self.assertEqual(result["result"], "bonjour")
        self.assertIn("metadata", result)

    def test_text2text_system_prompt(self):
        p = self._make_provider()
        with patch("anthropic.Anthropic") as MockClient:
            mock_create = MockClient.return_value.messages.create
            mock_create.return_value = self._mock_response()
            p.execute("text2text", "claude-haiku-4-5", "Prompt", {"system": "Tu es utile"})
            call_kwargs = mock_create.call_args[1]
            self.assertEqual(call_kwargs["system"], "Tu es utile")

    def test_text2text_metadata_fields(self):
        p = self._make_provider()
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = self._mock_response()
            result = p.execute("text2text", "claude-haiku-4-5", "Test", {})
        meta = result["metadata"]
        self.assertEqual(meta["provider"], "anthropic")
        self.assertIn("tokens_input", meta)
        self.assertGreaterEqual(meta["cost_usd"], 0)

    def test_img2text_image_url(self):
        p = self._make_provider()
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = self._mock_response("image décrite")
            result = p.execute("img2text", "claude-haiku-4-5", "Décris", {"image_url": "https://example.com/img.jpg"})
        self.assertEqual(result["result"], "image décrite")

    def test_img2text_base64(self):
        p = self._make_provider()
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = self._mock_response("desc")
            result = p.execute("img2text", "claude-haiku-4-5", "Décris", {
                "image_base64": "abc123", "media_type": "image/png"
            })
        self.assertEqual(result["result"], "desc")

    def test_img2text_no_image_raises(self):
        p = self._make_provider()
        with patch("anthropic.Anthropic"):
            with self.assertRaises(ValueError):
                p.execute("img2text", "claude-haiku-4-5", "Décris", {})

    def test_unsupported_type_raises(self):
        p = self._make_provider()
        with patch("anthropic.Anthropic"):
            with self.assertRaises(NotImplementedError):
                p.execute("text2img", "claude-haiku-4-5", "gen image", {})


# ─────────────────────────────────────────────────────────────
# OpenAIProvider (mock)
# ─────────────────────────────────────────────────────────────

class TestOpenAIProvider(unittest.TestCase):

    def _make_provider(self):
        from MODEL_EXECUTOR.src.providers.openai_provider import OpenAIProvider
        return OpenAIProvider("fake-key")

    def _mock_chat_response(self, text="réponse"):
        resp = MagicMock()
        resp.choices[0].message.content = text
        resp.usage.prompt_tokens     = 20
        resp.usage.completion_tokens = 10
        return resp

    def test_text2text_returns_result(self):
        p = self._make_provider()
        with patch("openai.OpenAI") as MockClient:
            MockClient.return_value.chat.completions.create.return_value = self._mock_chat_response("hello")
            result = p.execute("text2text", "gpt-4o", "Dis bonjour", {})
        self.assertEqual(result["result"], "hello")

    def test_text2text_with_system(self):
        p = self._make_provider()
        with patch("openai.OpenAI") as MockClient:
            mock_create = MockClient.return_value.chat.completions.create
            mock_create.return_value = self._mock_chat_response()
            p.execute("text2text", "gpt-4o", "Prompt", {"system": "Tu es utile"})
            messages = mock_create.call_args[1]["messages"]
            self.assertEqual(messages[0]["role"], "system")

    def test_text2img_returns_url(self):
        p = self._make_provider()
        with patch("openai.OpenAI") as MockClient:
            resp = MagicMock()
            resp.data = [MagicMock(url="https://example.com/img.jpg")]
            MockClient.return_value.images.generate.return_value = resp
            result = p.execute("text2img", "dall-e-3", "Un coucher de soleil", {})
        self.assertEqual(result["result"], "https://example.com/img.jpg")

    def test_img2text_image_url(self):
        p = self._make_provider()
        with patch("openai.OpenAI") as MockClient:
            MockClient.return_value.chat.completions.create.return_value = self._mock_chat_response("desc")
            result = p.execute("img2text", "gpt-4o", "Décris", {"image_url": "https://x.com/i.jpg"})
        self.assertEqual(result["result"], "desc")

    def test_img2text_no_image_raises(self):
        p = self._make_provider()
        with patch("openai.OpenAI"):
            with self.assertRaises(ValueError):
                p.execute("img2text", "gpt-4o", "Décris", {})

    def test_unsupported_type_raises(self):
        p = self._make_provider()
        with patch("openai.OpenAI"):
            with self.assertRaises(NotImplementedError):
                p.execute("img2video", "gpt-4o", "gen video", {})

    def test_metadata_has_provider(self):
        p = self._make_provider()
        with patch("openai.OpenAI") as MockClient:
            MockClient.return_value.chat.completions.create.return_value = self._mock_chat_response()
            result = p.execute("text2text", "gpt-4o", "Test", {})
        self.assertEqual(result["metadata"]["provider"], "openai")


# ─────────────────────────────────────────────────────────────
# GeminiProvider (mock)
# ─────────────────────────────────────────────────────────────

class TestGeminiProvider(unittest.TestCase):

    def _make_provider(self):
        from MODEL_EXECUTOR.src.providers.gemini_provider import GeminiProvider
        return GeminiProvider("fake-key")

    def test_text2text_returns_result(self):
        p = self._make_provider()
        mock_genai = MagicMock()
        mock_resp  = MagicMock()
        mock_resp.text = "gemini répond"
        mock_resp.usage_metadata.prompt_token_count     = 10
        mock_resp.usage_metadata.candidates_token_count = 5
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            result = p.execute("text2text", "gemini-pro", "Test", {})

        self.assertEqual(result["result"], "gemini répond")

    def test_unsupported_type_raises(self):
        p = self._make_provider()
        mock_genai = MagicMock()
        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            with self.assertRaises(NotImplementedError):
                p.execute("text2img", "gemini-pro", "img", {})

    def test_metadata_provider(self):
        p = self._make_provider()
        mock_genai = MagicMock()
        mock_resp  = MagicMock()
        mock_resp.text = "ok"
        mock_resp.usage_metadata.prompt_token_count     = 5
        mock_resp.usage_metadata.candidates_token_count = 3
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            result = p.execute("text2text", "gemini-pro", "Test", {})

        self.assertEqual(result["metadata"]["provider"], "gemini")


# ─────────────────────────────────────────────────────────────
# ReplicateProvider (mock)
# ─────────────────────────────────────────────────────────────

class TestReplicateProvider(unittest.TestCase):

    def _make_provider(self):
        from MODEL_EXECUTOR.src.providers.replicate_provider import ReplicateProvider
        return ReplicateProvider("fake-token")

    def test_text2img_single_url(self):
        p = self._make_provider()
        mock_rep = MagicMock()
        mock_rep.run.return_value = ["https://example.com/img.jpg"]

        with patch.dict("sys.modules", {"replicate": mock_rep}):
            result = p.execute("text2img", "black-forest-labs/flux-1.1-pro", "Un paysage", {})

        self.assertEqual(result["result"], "https://example.com/img.jpg")

    def test_text2img_extra_params_passed(self):
        p = self._make_provider()
        mock_rep = MagicMock()
        mock_rep.run.return_value = ["https://x.com/1.jpg"]

        with patch.dict("sys.modules", {"replicate": mock_rep}):
            p.execute("text2img", "flux", "Prompt", {"aspect_ratio": "16:9", "num_outputs": 2})

        call_input = mock_rep.run.call_args[1]["input"]
        self.assertEqual(call_input["aspect_ratio"], "16:9")
        self.assertEqual(call_input["num_outputs"], 2)

    def test_unsupported_type_raises(self):
        p = self._make_provider()
        mock_rep = MagicMock()
        with patch.dict("sys.modules", {"replicate": mock_rep}):
            with self.assertRaises(NotImplementedError):
                p.execute("text2text", "flux", "Test", {})

    def test_metadata_provider(self):
        p = self._make_provider()
        mock_rep = MagicMock()
        mock_rep.run.return_value = ["https://x.com/img.jpg"]
        with patch.dict("sys.modules", {"replicate": mock_rep}):
            result = p.execute("text2img", "flux", "Test", {})
        self.assertEqual(result["metadata"]["provider"], "replicate")


# ─────────────────────────────────────────────────────────────
# model_execute (integration routing, mocked providers)
# ─────────────────────────────────────────────────────────────

class TestModelExecute(unittest.TestCase):

    def _patch_provider(self, provider_name: str, result_text: str = "résultat"):
        """Patch _execute_with_provider pour retourner un résultat factice."""
        return patch(
            "MODEL_EXECUTOR.src.executor._execute_with_provider",
            return_value=_fake_result(result_text)
        )

    def test_unknown_model_type_raises(self):
        with self.assertRaises((ValueError, RuntimeError)):
            model_execute("unknown_type", "Test")

    def test_text2text_routes_to_provider(self):
        with patch("MODEL_EXECUTOR.src.executor._execute_with_provider",
                   return_value=_fake_result("ok")) as mock_exec:
            with patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "ANTHROPIC_API_KEY": "fake"}):
                result = model_execute("text2text", "Bonjour")
        self.assertEqual(result["result"], "ok")
        mock_exec.assert_called_once()

    def test_provider_override(self):
        with patch("MODEL_EXECUTOR.src.executor._execute_with_provider",
                   return_value=_fake_result("anthropic_result")) as mock_exec:
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake"}):
                result = model_execute("text2text", "Bonjour", provider="anthropic")
        self.assertEqual(result["result"], "anthropic_result")
        args = mock_exec.call_args[0]
        self.assertEqual(args[0], "anthropic")

    def test_fallback_on_provider_error(self):
        call_count = {"n": 0}

        def side_effect(provider, model_type, prompt, data):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("provider 1 down")
            return _fake_result("fallback ok")

        with patch("MODEL_EXECUTOR.src.executor._execute_with_provider", side_effect=side_effect):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "ANTHROPIC_API_KEY": "fake"}):
                result = model_execute("text2text", "Test")

        self.assertEqual(result["result"], "fallback ok")
        self.assertEqual(call_count["n"], 2)

    def test_both_providers_fail_raises(self):
        with patch("MODEL_EXECUTOR.src.executor._execute_with_provider",
                   side_effect=RuntimeError("down")):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "ANTHROPIC_API_KEY": "fake"}):
                with self.assertRaises(RuntimeError):
                    model_execute("text2text", "Test")

    def test_result_has_duration(self):
        with patch("MODEL_EXECUTOR.src.executor._execute_with_provider",
                   return_value=_fake_result("ok")):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "fake"}):
                result = model_execute("text2text", "Test")
        self.assertIn("duration_seconds", result["metadata"])

    def test_data_defaults_to_empty_dict(self):
        with patch("MODEL_EXECUTOR.src.executor._execute_with_provider",
                   return_value=_fake_result("ok")) as mock_exec:
            with patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "ANTHROPIC_API_KEY": "fake"}):
                model_execute("text2text", "Test")
        # data passé au provider doit être un dict
        args = mock_exec.call_args[0]
        self.assertIsInstance(args[3], dict)


if __name__ == "__main__":
    unittest.main()
