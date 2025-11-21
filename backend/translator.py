"""Translation helpers for communicating with the OpenRouter API."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests

from .config import settings

LOGGER = logging.getLogger(__name__)


class TranslationError(RuntimeError):
    """Raised when the translation provider fails."""


@dataclass
class TranslationConfig:
    api_key: str
    model: str
    source_lang: Optional[str]
    target_lang: str
    temperature: float = 0.0


class OpenRouterTranslator:
    """Wrapper around the OpenRouter chat completion endpoint."""

    def __init__(self, config: TranslationConfig):
        self.config = config
        self.api_base = settings.openrouter_api_base.rstrip("/")

    def translate_texts(self, texts: Iterable[str]) -> List[str]:
        texts = list(texts)
        if not texts:
            return []

        if not self.config.api_key:
            LOGGER.warning("No OpenRouter API key provided; falling back to mock translation.")
            return [self._mock_translate(text) for text in texts]

        payload = self._build_request_payload(texts)
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        endpoint = f"{self.api_base}/chat/completions"
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise TranslationError("Failed to contact OpenRouter API") from exc

        if response.status_code >= 400:
            raise TranslationError(
                f"OpenRouter API returned {response.status_code}: {response.text}"
            )

        data = response.json()
        try:
            message_content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            LOGGER.error("Unexpected response payload: %s", data)
            raise TranslationError("Could not parse translation response from OpenRouter") from exc

        translations = self._extract_translations(message_content, len(texts))
        if len(translations) != len(texts):
            translations = self._reconcile_translation_count(translations, texts)
        if len(translations) != len(texts):
            raise TranslationError("Translation count mismatch between request and response")

        return [str(item) for item in translations]

    def _build_request_payload(self, texts: List[str]) -> dict:
        source = self.config.source_lang or "auto-detect"
        target = self.config.target_lang
        instructions = (
            "You are a professional translation engine. Translate each input string from "
            f"{source} to {target}. Preserve placeholders such as {{variable}} or HTML tags. "
            "Return ONLY a valid JSON array of translated strings matching the input order with no extra text."
        )

        messages = [
            {"role": "system", "content": instructions},
            {"role": "system", "content": "Do not include reasoning, commentary, or code fences. Respond with the JSON array only."},
            {
                "role": "user",
                "content": json.dumps(list(texts), ensure_ascii=False),
            },
        ]

        return {
            "model": self.config.model or settings.default_model,
            "messages": messages,
            "temperature": self.config.temperature,
        }

    def _mock_translate(self, text: str) -> str:
        target = self.config.target_lang or "translated"
        return f"[{target}] {text}"

    def _extract_translations(self, message: str, expected_count: int) -> List[str]:
        try:
            parsed = json.loads(message)
            if isinstance(parsed, list) and (expected_count == len(parsed) or expected_count == 0):
                return parsed
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", message, re.DOTALL)
        if fenced:
            snippet = fenced.group(1)
            try:
                parsed = json.loads(snippet)
                if isinstance(parsed, list) and (expected_count == len(parsed) or expected_count == 0):
                    return parsed
            except json.JSONDecodeError:
                LOGGER.debug("Failed to parse fenced JSON snippet.")

        array_snippet = self._find_json_array(message)
        if array_snippet:
            try:
                parsed = json.loads(array_snippet)
                if isinstance(parsed, list) and (expected_count == len(parsed) or expected_count == 0):
                    return parsed
            except json.JSONDecodeError:
                LOGGER.debug("Failed to parse matched JSON array.")

        LOGGER.error("Unexpected response payload: %s", message)
        raise TranslationError("Could not parse translation response from OpenRouter")

    def _reconcile_translation_count(self, translations: List[str], original_texts: List[str]) -> List[str]:
        expected = len(original_texts)
        current = len(translations)

        if expected == 0 or current == expected:
            return translations

        tolerance = max(3, expected // 5 + 1)
        if abs(current - expected) > tolerance:
            LOGGER.error(
                "Translation count mismatch too large to reconcile (expected %s, received %s)",
                expected,
                current,
            )
            return translations

        adjusted = list(translations)
        if current > expected:
            adjusted = self._merge_extra_items(adjusted, expected)
        if len(adjusted) < expected:
            adjusted = self._pad_missing_items(adjusted, original_texts)

        if len(adjusted) == expected:
            LOGGER.warning(
                "Translation count mismatch corrected (%s -> %s)", current, expected
            )
        return adjusted

    def _merge_extra_items(self, items: List[str], expected: int) -> List[str]:
        merged = list(items)
        while len(merged) > expected and len(merged) > 1:
            idx = self._find_merge_index(merged)
            merged[idx] = self._concat_segments(merged[idx], merged.pop(idx + 1))
        return merged

    def _pad_missing_items(self, items: List[str], originals: List[str]) -> List[str]:
        padded = list(items)
        for idx in range(len(padded), len(originals)):
            padded.append(originals[idx])
        return padded

    @staticmethod
    def _find_merge_index(items: List[str]) -> int:
        for idx in range(1, len(items)):
            segment = items[idx].lstrip()
            if not segment:
                return idx - 1
            first_char = segment[0]
            previous = items[idx - 1]
            if first_char in ",.;:!?)]}":
                return idx - 1
            if previous and not previous.rstrip().endswith((".", "!", "?", "。", "！", "？")):
                return idx - 1
            if first_char.islower():
                return idx - 1
        return max(0, len(items) - 2)

    @staticmethod
    def _concat_segments(left: str, right: str) -> str:
        left = left.rstrip()
        right = right.lstrip()
        if not left:
            return right
        if not right:
            return left
        if right[0] in ",.;:!?)]}":
            return left + right
        return f"{left} {right}"

    def _find_json_array(self, message: str) -> Optional[str]:
        start = message.find('[')
        if start == -1:
            return None
        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(message)):
            char = message[idx]
            if char == '"' and not escape:
                in_string = not in_string
            if in_string:
                if char == '\\' and not escape:
                    escape = True
                else:
                    escape = False
                continue
            escape = char == '\\' and not escape
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    return message[start:idx + 1]
        return None
