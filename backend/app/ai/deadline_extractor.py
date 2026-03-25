"""Generic deadline extraction from any document type."""
import logging
from datetime import date

from app.ai.classifier import get_classifier
from app.ai.prompts import build_deadline_extraction_prompt

logger = logging.getLogger(__name__)


class DeadlineExtractionResult:
    def __init__(
        self,
        has_deadline: bool = False,
        tipo_scadenza: str = "generico",
        data_scadenza: date | None = None,
        data_inizio: date | None = None,
        importo: str | None = None,
        descrizione: str | None = None,
        confidence: float = 0.0,
    ) -> None:
        self.has_deadline = has_deadline
        self.tipo_scadenza = tipo_scadenza
        self.data_scadenza = data_scadenza
        self.data_inizio = data_inizio
        self.importo = importo
        self.descrizione = descrizione
        self.confidence = confidence


def _parse_date(value: object) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def extract_deadline(text: str, tipo_documento: str) -> DeadlineExtractionResult:
    """Extract the most relevant deadline from any document. Never raises."""
    try:
        prompt = build_deadline_extraction_prompt(text, tipo_documento)
        classifier = get_classifier()
        data = classifier.raw_json_call(prompt)

        if not data.get("has_deadline", False):
            return DeadlineExtractionResult(has_deadline=False)

        return DeadlineExtractionResult(
            has_deadline=True,
            tipo_scadenza=data.get("tipo_scadenza", "generico"),
            data_scadenza=_parse_date(data.get("data_scadenza")),
            data_inizio=_parse_date(data.get("data_inizio")),
            importo=data.get("importo"),
            descrizione=data.get("descrizione"),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0)))),
        )
    except Exception:
        logger.exception("Deadline extraction failed")
        return DeadlineExtractionResult()
