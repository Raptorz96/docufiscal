"""
Base classifier interface and factory for AI document classification.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import re

logger = logging.getLogger(__name__)

# Singleton cache
_classifier_instance: "BaseClassifier | None" = None


@dataclass
class ClassificationResult:
    """Result of an AI document classification."""

    tipo_documento: str
    """Enum value from TipoDocumento (e.g. 'fattura', 'f24')."""

    tipo_documento_raw: str
    """Free-form description returned by the model."""

    confidence: float
    """Confidence score in the range [0.0, 1.0]."""

    macro_categoria: str = "altro"
    """Enum value from MacroCategoria (e.g. 'fiscale', 'lavoro')."""

    anno_competenza: int | None = None
    """Reference year for the document."""

    cliente_suggerito: str | None = None
    """Client name recognised in the document text, if any."""

    codice_fiscale: str | None = None
    """Italian tax code (CF) extracted from the document."""

    partita_iva: str | None = None
    """Italian VAT number (PI) extracted from the document."""

    contratto_suggerito: str | None = None
    """Contract type recognised in the document text, if any."""

    raw_response: dict = field(default_factory=dict)
    """Full model response, preserved for debugging."""


def extract_short_id(filename: str) -> int | None:
    """Extract numeric short ID from filename if it follows the #ID_ pattern.
    
    Example: "#105_fattura.pdf" -> 105
    """
    match = re.search(r"^#?(\d+)[_\s-]", filename)
    if match:
        return int(match.group(1))
    return None


class BaseClassifier(ABC):
    """Abstract base class for document classifiers."""

    @abstractmethod
    def classify(
        self,
        text: str,
        available_types: list[str],
        clienti_context: list[dict] | None = None,
        skip_client_id: bool = False,
    ) -> ClassificationResult:
        """Classify a document based on its extracted text."""

    @abstractmethod
    async def aclassify(
        self,
        text: str,
        available_types: list[str],
        clienti_context: list[dict] | None = None,
        skip_client_id: bool = False,
    ) -> ClassificationResult:
        """Asynchronous version of classify."""

    @abstractmethod
    def raw_json_call(self, prompt: str) -> dict:
        """Send prompt to LLM and return parsed JSON response.

        System prompt is fixed to JSON-only output.
        Raises on unrecoverable errors; caller must handle exceptions.
        """


def get_classifier() -> BaseClassifier:
    """Return the configured classifier, creating it once (singleton).

    Reads ``settings.AI_PROVIDER`` to select the implementation.

    Returns:
        A concrete :class:`BaseClassifier` instance.

    Raises:
        ValueError: If the configured provider is not supported.
    """
    global _classifier_instance  # noqa: PLW0603

    if _classifier_instance is not None:
        return _classifier_instance

    from app.core.config import settings  # lazy to avoid circular imports

    provider = settings.AI_PROVIDER.lower()
    logger.info("Initialising AI classifier with provider: %s", provider)

    if provider == "gemini":
        from app.ai.gemini_classifier import GeminiClassifier  # noqa: PLC0415

        _classifier_instance = GeminiClassifier()
    elif provider == "claude":
        from app.ai.claude_classifier import ClaudeClassifier  # noqa: PLC0415

        _classifier_instance = ClaudeClassifier()
    elif provider == "openai":
        from app.ai.openai_classifier import OpenAIClassifier  # noqa: PLC0415
        
        _classifier_instance = OpenAIClassifier()
    else:
        raise ValueError(
            f"Unsupported AI provider: '{provider}'. "
            "Supported values are 'gemini', 'claude', and 'openai'."
        )

    return _classifier_instance
