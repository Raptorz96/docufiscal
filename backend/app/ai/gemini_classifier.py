"""
Document classifier implementation using Google Gemini API.
"""
import json
import logging

from google import genai

from app.ai.classifier import BaseClassifier, ClassificationResult
from app.ai.prompts import build_classification_prompt
from app.core.config import settings

logger = logging.getLogger(__name__)

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "tipo_documento": {"type": "string"},
        "tipo_documento_raw": {"type": "string"},
        "confidence": {"type": "number"},
        "cliente_suggerito": {"type": "string"},
        "codice_fiscale": {"type": "string"},
        "partita_iva": {"type": "string"},
        "contratto_suggerito": {"type": "string"},
    },
    "required": ["tipo_documento", "tipo_documento_raw", "confidence"],
}


_DEFAULT_RESULT = ClassificationResult(
    tipo_documento="altro",
    tipo_documento_raw="Classificazione fallita",
    confidence=0.0,
)


class GeminiClassifier(BaseClassifier):
    """Document classifier backed by Google Gemini."""

    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.AI_API_KEY)
        self.model = settings.AI_MODEL
        logger.info("GeminiClassifier initialised with model: %s", self.model)

    def classify(
        self,
        text: str,
        available_types: list[str],
        clienti_context: list[dict] | None = None,
    ) -> ClassificationResult:
        """Classify a document using Gemini structured JSON output.

        Args:
            text: Extracted document text.
            available_types: Valid TipoDocumento enum values.
            clienti_context: Optional list of client dicts for entity matching.

        Returns:
            :class:`ClassificationResult` — falls back to default on any error.
        """
        try:
            prompt = build_classification_prompt(text, available_types, clienti_context)

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": _RESPONSE_SCHEMA,
                },
            )

            data: dict = json.loads(response.text)

            tipo = data.get("tipo_documento", "altro")
            if tipo not in available_types:
                logger.warning(
                    "Gemini returned unknown tipo_documento '%s', falling back to 'altro'", tipo
                )
                tipo = "altro"

            confidence = float(data.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))

            return ClassificationResult(
                tipo_documento=tipo,
                tipo_documento_raw=data.get("tipo_documento_raw", ""),
                confidence=confidence,
                cliente_suggerito=data.get("cliente_suggerito") or None,
                codice_fiscale=data.get("codice_fiscale") or None,
                partita_iva=data.get("partita_iva") or None,
                contratto_suggerito=data.get("contratto_suggerito") or None,
                raw_response=data,
            )

        except Exception:
            logger.exception("Gemini classification failed")
            return _DEFAULT_RESULT
