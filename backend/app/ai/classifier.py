"""
Base classifier interface and factory for AI document classification.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

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

    cliente_suggerito: str | None = None
    """Client name or tax code recognised in the document text, if any."""

    contratto_suggerito: str | None = None
    """Contract type recognised in the document text, if any."""

    raw_response: dict = field(default_factory=dict)
    """Full model response, preserved for debugging."""


class BaseClassifier(ABC):
    """Abstract base class for document classifiers."""

    @abstractmethod
    def classify(
        self,
        text: str,
        available_types: list[str],
        clienti_context: list[dict] | None = None,
    ) -> ClassificationResult:
        """Classify a document based on its extracted text.

        Args:
            text: Text extracted from the document.
            available_types: List of valid TipoDocumento enum values.
            clienti_context: Optional list of client dicts with keys
                ``nome``, ``cognome``, ``codice_fiscale`` for entity matching.

        Returns:
            A :class:`ClassificationResult` with the classification details.
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
    else:
        raise ValueError(
            f"Unsupported AI provider: '{provider}'. "
            "Supported values are 'gemini' and 'claude'."
        )

    return _classifier_instance
