"""
Document classifier implementation using Anthropic Claude API.
"""
import json
import logging

import anthropic

from app.ai.classifier import BaseClassifier, ClassificationResult
from app.ai.prompts import build_classification_prompt
from app.core.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_RESULT = ClassificationResult(
    tipo_documento="altro",
    tipo_documento_raw="Classificazione fallita",
    confidence=0.0,
)


class ClaudeClassifier(BaseClassifier):
    """Document classifier backed by Anthropic Claude."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.AI_API_KEY)
        self.model = settings.AI_MODEL
        logger.info("ClaudeClassifier initialised with model: %s", self.model)

    def classify(
        self,
        text: str,
        available_types: list[str],
        clienti_context: list[dict] | None = None,
    ) -> ClassificationResult:
        """Classify a document using Claude with JSON-only system prompt.

        Args:
            text: Extracted document text.
            available_types: Valid TipoDocumento enum values.
            clienti_context: Optional list of client dicts for entity matching.

        Returns:
            :class:`ClassificationResult` — falls back to default on any error.
        """
        try:
            prompt = build_classification_prompt(text, available_types, clienti_context)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system="Rispondi SOLO con un JSON valido, senza testo aggiuntivo.",
                messages=[{"role": "user", "content": prompt}],
            )

            data: dict = json.loads(response.content[0].text)

            tipo = data.get("tipo_documento", "altro")
            if tipo not in available_types:
                logger.warning(
                    "Claude returned unknown tipo_documento '%s', falling back to 'altro'", tipo
                )
                tipo = "altro"

            confidence = float(data.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))

            return ClassificationResult(
                tipo_documento=tipo,
                tipo_documento_raw=data.get("tipo_documento_raw", ""),
                confidence=confidence,
                cliente_suggerito=data.get("cliente_suggerito") or None,
                contratto_suggerito=data.get("contratto_suggerito") or None,
                raw_response=data,
            )

        except anthropic.AuthenticationError:
            logger.error("Invalid Claude API key")
            return _DEFAULT_RESULT
        except anthropic.RateLimitError:
            logger.error("Claude rate limit exceeded")
            return _DEFAULT_RESULT
        except Exception:
            logger.exception("Claude classification failed")
            return _DEFAULT_RESULT
