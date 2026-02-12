"""AIProvider - Adapter for AI API providers."""
from typing import Dict, Any, List, Optional
import re
import os
from openai import OpenAI
from ..object import Object, TestResult


class AIResponse:
    """AI API response wrapper."""
    def __init__(self, raw_text: str, provider: str, model: str):
        self.raw_text = raw_text
        self.provider = provider
        self.model = model
        self.mentions: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "provider": self.provider,
            "model": self.model,
            "mentions": self.mentions,
        }


class AIProvider(Object):
    """
    AI Provider adapter.

    Extends: Object → interface.adapter.APIAdapter

    Handles communication with AI APIs (ChatGPT, Claude, Gemini, Perplexity).
    """

    def __init__(
        self,
        name: str,
        api_endpoint: str,
        model: str,
        api_key: str = "",
        rate_limit: int = 60,
        timeout: int = 30,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.api_endpoint = api_endpoint
        self.model = model
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.timeout = timeout
        self._request_count = 0

    def validate(self) -> bool:
        """Validate provider configuration."""
        if not self.name or self.name not in ["chatgpt", "claude", "gemini", "perplexity"]:
            return False
        if not self.api_endpoint or not self.api_endpoint.startswith("http"):
            return False
        if not self.model:
            return False
        if self.rate_limit <= 0 or self.timeout <= 0:
            return False
        return True

    def test(self) -> TestResult:
        """Test provider configuration."""
        if not self.validate():
            return TestResult(False, "Invalid provider configuration")

        if not self.api_key:
            return TestResult(False, "API key is required for real usage")

        return TestResult(True, f"Provider {self.name} configured correctly")

    def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "fr"
    ) -> AIResponse:
        """
        Query the AI provider.

        Makes real API call to OpenAI.

        Args:
            prompt: User prompt (can be pre-formatted or raw query)
            context: Optional context data
            language: Language code (fr, en, es, de, it) for system prompt

        Returns:
            AIResponse with the model's response
        """
        self._request_count += 1

        try:
            # Import prompts module
            from ..config.prompts import get_system_prompt

            # Initialize OpenAI client (prioritize project-specific key)
            api_key = self.api_key or os.getenv("OPENAI_API_KEY_AI_SEO") or os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)

            # Get system prompt in requested language
            system_prompt = get_system_prompt(language)

            # Make API call
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500,
            )

            # Extract response text
            raw_text = completion.choices[0].message.content

            response = AIResponse(
                raw_text=raw_text,
                provider=self.name,
                model=self.model
            )

            return response

        except Exception as e:
            # Fallback to mock on error
            print(f"⚠️  OpenAI API error: {e}")
            response = AIResponse(
                raw_text=f"Error calling {self.name}: {str(e)}",
                provider=self.name,
                model=self.model
            )
            return response

    def parse_response(self, raw: str) -> Dict[str, Any]:
        """
        Parse raw AI response.

        Extracts structured information from the response text.
        """
        # Basic parsing - will be enhanced in Phase 3
        return {
            "text": raw,
            "length": len(raw),
            "sentences": raw.count('.'),
        }

    def extract_mentions(self, text: str) -> List[str]:
        """
        Extract company/brand mentions from text.

        Uses simple regex patterns. Will be enhanced with NLP in Phase 3.
        """
        # Pattern: Capitalized words (potential company names)
        pattern = r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b'
        mentions = re.findall(pattern, text)

        # Filter out common words
        stop_words = {"The", "This", "That", "These", "Those", "It", "I", "You", "We", "They"}
        mentions = [m for m in mentions if m not in stop_words]

        return list(set(mentions))  # Unique mentions

    def check_rate_limit(self) -> bool:
        """Check if rate limit allows new request."""
        # Simplified check - will use Redis in Phase 3
        return self._request_count < self.rate_limit

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "name": self.name,
            "api_endpoint": self.api_endpoint,
            "model": self.model,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            # Don't include api_key in serialization for security
        })
        return base
