import os
import json
import logging
from typing import List, Dict, Any, Optional

import httpx
from app.config import config

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        # Get API configuration with OpenRouter support
        api_config = config.get_api_config()
        self.api_base = api_config["api_base"]
        self.api_key = api_config["api_key"]
        self.model = api_config["model"]
        self.headers = api_config.get("headers", {})

        self.temperature = config.TEMPERATURE
        self.max_tokens = config.MAX_TOKENS

        if not self.api_base or not self.api_key:
            logger.warning("API base or key not configured")
            logger.info(
                f"Available API configs: OPENROUTER_API_KEY={'SET' if config.OPENROUTER_API_KEY else 'NOT SET'}, "
                f"OPENAI_API_KEY={'SET' if config.OPENAI_API_KEY else 'NOT SET'}"
            )

    def _build_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Build messages for OpenAI-compatible chat completions API."""
        return messages

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including OpenRouter-specific headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Add OpenRouter specific headers if configured
        if self.headers:
            headers.update(self.headers)

        return headers

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        json_mode: bool = True,
    ) -> Optional[str]:
        """Make a chat completion request to OpenAI-compatible API."""
        try:
            if not self.api_base or not self.api_key:
                raise ValueError("API base or key not configured")

            headers = self._get_headers()

            payload = {
                "model": model or self.model,
                "messages": self._build_messages(messages),
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }

            # Handle JSON mode for different providers
            if json_mode:
                # OpenRouter and some providers don't support response_format
                # We'll handle JSON mode through the prompt instead
                if "openrouter.ai" in self.api_base.lower():
                    # Add JSON instruction to the last message if not already present
                    if messages and not messages[-1]["content"].strip().endswith(
                        "Return JSON only."
                    ):
                        messages[-1]["content"] += (
                            "\n\nIMPORTANT: Return your response as a valid JSON object only."
                        )
                        payload["messages"] = self._build_messages(messages)
                else:
                    # For OpenAI and compatible APIs that support it
                    payload["response_format"] = {"type": "json_object"}

            logger.debug(f"Making API request to: {self.api_base}")
            logger.debug(f"Using model: {payload['model']}")

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                logger.debug(f"LLM response: {content[:100]}...")

                return content

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from LLM API: {e.response.status_code} - {e.response.text}"
            )
            if e.response.status_code == 401:
                logger.error("Authentication failed - check your API key")
            elif e.response.status_code == 404:
                logger.error(
                    "Model or endpoint not found - check model name and API base URL"
                )
            return None
        except Exception as e:
            logger.error(f"Error making LLM request: {e}")
            return None

    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from LLM."""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            import re

            json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Raw response: {response}")
            return None

    def generate_structured_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Generate structured JSON response from LLM."""
        content = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            json_mode=True,
        )

        if content:
            return self.parse_json_response(content)
        return None

    def test_connection(self) -> bool:
        """Test connection to the API endpoint."""
        try:
            test_messages = [
                {
                    "role": "user",
                    "content": "Respond with a simple JSON: {'status': 'ok'}",
                }
            ]

            response = self.chat_completion(
                messages=test_messages, temperature=0.0, max_tokens=50
            )

            if response:
                parsed = self.parse_json_response(response)
                if parsed and parsed.get("status") == "ok":
                    logger.info("API connection test successful")
                    return True

            logger.error("API connection test failed")
            return False

        except Exception as e:
            logger.error(f"API connection test error: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current API configuration."""
        provider = (
            "OpenRouter"
            if "openrouter.ai" in self.api_base.lower()
            else "OpenAI-compatible"
        )

        return {
            "provider": provider,
            "api_base": self.api_base,
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "supports_json_mode": "openrouter.ai" not in self.api_base.lower(),
        }
        
llm_client = LLMClient()
