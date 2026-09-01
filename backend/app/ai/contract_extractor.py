"""Structured data extraction from contract documents."""
import logging
from datetime import date

from app.ai.classifier import get_classifier
from app.ai.prompts import build_contract_extraction_prompt

logger = logging.getLogger(__name__)


class ContractExtractionResult:
    """Result of AI-driven structured extraction from a contract."""

    def __init__(
        self,
        data_inizio: date | None = None,
        data_scadenza: date | None = None,
        durata: str | None = None,
        rinnovo_automatico: bool | None = None,
        preavviso_disdetta: str | None = None,
        canone: str | None = None,
        parti_coinvolte: list[str] | None = None,
        clausole_chiave: list[str] | None = None,
        confidence: float = 0.0,
        raw_response: dict | None = None,
    ) -> None:
        self.data_inizio = data_inizio
        self.data_scadenza = data_scadenza
        self.durata = durata
        self.rinnovo_automatico = rinnovo_automatico
        self.preavviso_disdetta = preavviso_disdetta
        self.canone = canone
        self.parti_coinvolte = parti_coinvolte
        self.clausole_chiave = clausole_chiave
        self.confidence = confidence
        self.raw_response = raw_response or {}


def _parse_date(value: object) -> date | None:
    """Parse a YYYY-MM-DD string to a date, return None on any failure."""
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def extract_contract_data(text: str) -> ContractExtractionResult:
    """Extract structured data from a contract using the configured LLM.

    Uses the same provider/model as document classification (Gemini/Claude/OpenAI).
    Always returns a result — never raises. If extraction fails the returned
    object has confidence=0.0 and all fields set to None.
    """
    try:
        prompt = build_contract_extraction_prompt(text)
        classifier = get_classifier()
        data = classifier.raw_json_call(prompt)

        return ContractExtractionResult(
            data_inizio=_parse_date(data.get("data_inizio")),
            data_scadenza=_parse_date(data.get("data_scadenza")),
            durata=data.get("durata"),
            rinnovo_automatico=data.get("rinnovo_automatico"),
            preavviso_disdetta=data.get("preavviso_disdetta"),
            canone=data.get("canone"),
            parti_coinvolte=data.get("parti_coinvolte"),
            clausole_chiave=data.get("clausole_chiave"),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0)))),
            raw_response=data,
        )
    except Exception:
        logger.exception("Contract extraction failed")
        return ContractExtractionResult()
