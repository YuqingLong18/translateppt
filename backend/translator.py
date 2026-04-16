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

    def __init__(
        self,
        message: str,
        *,
        provider_status: Optional[int] = None,
        response_preview: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.provider_status = provider_status
        self.response_preview = response_preview


@dataclass
class TranslationConfig:
    api_key: str
    model: str
    source_lang: Optional[str]
    target_lang: str
    temperature: float = 0.0


class OpenRouterTranslator:
    """Wrapper around the OpenRouter chat completion endpoint."""

    MAX_BATCH_ITEMS = 40
    MAX_BATCH_CHARS = 12000

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

        translations: List[str] = []
        for batch_index, batch in enumerate(self._chunk_texts(texts), start=1):
            LOGGER.info(
                "Submitting translation batch %s with %s segments and %s characters",
                batch_index,
                len(batch),
                sum(len(item) for item in batch),
            )
            translations.extend(self._translate_batch(batch))

        return translations

    def _translate_batch(self, texts: List[str]) -> List[str]:
        payload = self._build_request_payload(texts)
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        endpoint = f"{self.api_base}/chat/completions"
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=300)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            LOGGER.exception(
                "Failed to contact OpenRouter API. endpoint=%s model=%s",
                endpoint,
                self.config.model or settings.default_model,
            )
            raise TranslationError("Failed to contact OpenRouter API") from exc

        if response.status_code >= 400:
            error_preview = response.text[:500] if len(response.text) > 500 else response.text
            LOGGER.error(
                "OpenRouter API returned an error. endpoint=%s model=%s status=%s response=%s",
                endpoint,
                self.config.model or settings.default_model,
                response.status_code,
                error_preview,
            )
            raise TranslationError(
                f"OpenRouter API returned {response.status_code}: {error_preview}",
                provider_status=response.status_code,
                response_preview=error_preview,
            )

        data = self._decode_response_json(response)
        try:
            message_content = self._extract_message_content(data)
        except (KeyError, IndexError) as exc:
            LOGGER.error(
                "Unexpected OpenRouter response structure. model=%s response=%s",
                self.config.model or settings.default_model,
                data,
            )
            raise TranslationError(
                "Could not parse translation response from OpenRouter - invalid response structure"
            ) from exc

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

    def _chunk_texts(self, texts: List[str]) -> List[List[str]]:
        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_chars = 0

        for text in texts:
            text_length = len(text)
            would_exceed_items = len(current_batch) >= self.MAX_BATCH_ITEMS
            would_exceed_chars = current_batch and current_chars + text_length > self.MAX_BATCH_CHARS

            if current_batch and (would_exceed_items or would_exceed_chars):
                batches.append(current_batch)
                current_batch = []
                current_chars = 0

            current_batch.append(text)
            current_chars += text_length

        if current_batch:
            batches.append(current_batch)

        return batches

    def _decode_response_json(self, response: requests.Response) -> dict:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as exc:
            preview = response.text[:1000] if response.text else ""
            LOGGER.error(
                "Failed to decode provider JSON response. status=%s preview=%s",
                response.status_code,
                preview,
            )
            raise TranslationError(
                "Could not parse provider response from OpenRouter. The response was not valid JSON.",
                provider_status=response.status_code,
                response_preview=preview,
            ) from exc

    @staticmethod
    def _extract_message_content(data: dict) -> str:
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(part for part in parts if part).strip()
        raise KeyError("Unsupported message content format")

    def _extract_translations(self, message: str, expected_count: int) -> List[str]:
        candidates = []

        # 1. Try parsing the whole message as JSON
        try:
            parsed = json.loads(message)
            if isinstance(parsed, list):
                if expected_count == 0 or len(parsed) == expected_count:
                    return parsed
                candidates.append(parsed)
        except json.JSONDecodeError:
            pass

        # 2. Try parsing fenced code blocks
        fenced = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", message, re.DOTALL)
        if fenced:
            snippet = fenced.group(1)
            try:
                parsed = json.loads(snippet)
                if isinstance(parsed, list):
                    if expected_count == 0 or len(parsed) == expected_count:
                        return parsed
                    candidates.append(parsed)
            except json.JSONDecodeError:
                LOGGER.debug("Failed to parse fenced JSON snippet.")

        # 3. Try finding a JSON array in the text
        array_snippet = self._find_json_array(message)
        if array_snippet:
            try:
                parsed = json.loads(array_snippet)
                if isinstance(parsed, list):
                    if expected_count == 0 or len(parsed) == expected_count:
                        return parsed
                    candidates.append(parsed)
            except json.JSONDecodeError:
                LOGGER.debug("Failed to parse matched JSON array.")

        # If we found any candidates (even with mismatched length), return the first one
        # The reconciliation logic will handle the count mismatch
        if candidates:
            LOGGER.warning(
                "Translation count mismatch (expected %s, got %s). Will attempt reconciliation.",
                expected_count,
                len(candidates[0])
            )
            return candidates[0]

        # Only raise an error if we couldn't parse any valid JSON array at all
        LOGGER.error("Could not parse any valid JSON array from response. Response preview: %s", message[:500])
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
