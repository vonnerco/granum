from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from google import genai


@dataclass
class LLMResult:
    enhanced_text: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int


class LLMClient(Protocol):
    def enhance(self, raw_text: str) -> LLMResult:
        ...


class GeminiLLMClient:
    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ValueError('GOOGLE_GENERATIVE_AI_API_KEY is required to call Gemini.')
        self._client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def enhance(self, raw_text: str) -> LLMResult:
        prompt = self._build_prompt(raw_text)
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        usage = getattr(response, 'usage_metadata', None)
        prompt_tokens = int(
            getattr(usage, 'prompt_token_count', None)
            or getattr(usage, 'input_token_count', None)
            or 0
        )
        completion_tokens = int(
            getattr(usage, 'candidates_token_count', None)
            or getattr(usage, 'output_token_count', None)
            or 0
        )
        text = (getattr(response, 'text', None) or '').strip()

        if not text:
            raise RuntimeError('LLM returned an empty response.')

        return LLMResult(
            enhanced_text=text,
            model_used=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    @staticmethod
    def _build_prompt(raw_text: str) -> str:
        return (
            'You are an assistant that rewrites technician notes.\\n'
            'Requirements:\\n'
            '1) Preserve every factual detail from the input.\\n'
            '2) Do not add any new facts, dates, quantities, or assumptions.\\n'
            '3) Improve clarity, grammar, and professionalism.\\n'
            '4) Output in bullet lists with clear sections.\\n'
            '5) Keep concise and actionable.\\n\\n'
            'Use this output format exactly:\\n'
            'Work completed:\\n'
            '- ...\\n'
            'Outcome/Follow-up:\\n'
            '- ...\\n\\n'
            f'Input note:\\n{raw_text}'
        )
