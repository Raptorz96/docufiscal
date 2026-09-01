"""Tests for the generic deadline extractor."""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.ai.deadline_extractor import DeadlineExtractionResult, extract_deadline


def _make_classifier(json_response: dict):
    """Return a mock classifier whose raw_json_call returns json_response."""
    mock = MagicMock()
    mock.raw_json_call.return_value = json_response
    return mock


def test_extract_deadline_with_payment():
    """When LLM returns a payment deadline, result is populated correctly."""
    payload = {
        "has_deadline": True,
        "tipo_scadenza": "pagamento",
        "data_scadenza": "2026-06-16",
        "data_inizio": None,
        "importo": "€1.500",
        "descrizione": "Pagamento F24 secondo acconto IRPEF",
        "confidence": 0.92,
    }
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo documento f24", "f24")

    assert result.has_deadline is True
    assert result.tipo_scadenza == "pagamento"
    assert result.data_scadenza == date(2026, 6, 16)
    assert result.importo == "€1.500"
    assert result.confidence == pytest.approx(0.92)


def test_extract_deadline_no_deadline():
    """When LLM returns has_deadline=false, result has has_deadline=False."""
    payload = {"has_deadline": False}
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo senza scadenza", "busta_paga")

    assert result.has_deadline is False
    assert result.data_scadenza is None


def test_extract_deadline_never_raises():
    """extract_deadline must return a safe default even if the classifier explodes."""
    with patch("app.ai.deadline_extractor.get_classifier", side_effect=RuntimeError("boom")):
        result = extract_deadline("qualsiasi testo", "altro")

    assert isinstance(result, DeadlineExtractionResult)
    assert result.has_deadline is False


def test_extract_deadline_invalid_date():
    """Malformed date strings must not raise — they become None."""
    payload = {
        "has_deadline": True,
        "tipo_scadenza": "generico",
        "data_scadenza": "not-a-date",
        "data_inizio": None,
        "importo": None,
        "descrizione": "descrizione",
        "confidence": 0.5,
    }
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo", "altro")

    assert result.has_deadline is True
    assert result.data_scadenza is None


def test_extract_deadline_confidence_clamped():
    """Confidence values outside [0,1] are clamped."""
    payload = {
        "has_deadline": True,
        "tipo_scadenza": "generico",
        "data_scadenza": "2026-12-31",
        "data_inizio": None,
        "importo": None,
        "descrizione": "test",
        "confidence": 99.0,  # out of range
    }
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo", "altro")

    assert result.confidence == 1.0
