import pytest
import io
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.api.documenti import upload_documento
from app.models.cliente import Cliente
from app.models.user import User
from app.ai.routing import regex_router
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_regex_routing_logic(db: Session):
    # Setup: create a client with a specific P.IVA
    test_pi = "12345678901"
    cliente = Cliente(nome="Test Client", partita_iva=test_pi, tipo="azienda")
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    # Mock text extraction to return text containing the P.IVA
    mock_text = f"Fattura emessa a: Test Client, P.IVA: {test_pi}"
    
    with patch("app.ai.routing.text_extraction_service.extract_text", return_value=mock_text):
        # Test finding client by regex
        matched = await regex_router.find_client_by_regex(db, "fake_path.pdf", "application/pdf")
        
        assert matched is not None
        assert matched.id == cliente.id
        assert matched.partita_iva == test_pi

@pytest.mark.asyncio
async def test_regex_routing_no_match(db: Session):
    # Mock text extraction with no useful info
    mock_text = "Testo casuale senza P.IVA o CF."
    
    with patch("app.ai.routing.text_extraction_service.extract_text", return_value=mock_text):
        matched = await regex_router.find_client_by_regex(db, "fake_path.pdf", "application/pdf")
        assert matched is None

@pytest.mark.asyncio
async def test_regex_routing_cf_match(db: Session):
    # Setup: create a client with a specific CF
    test_cf = "MRCRSS80A01H501Z"
    cliente = Cliente(nome="Marco Rossi", codice_fiscale=test_cf, tipo="privato")
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    # Mock text extraction
    mock_text = f"Documento di {test_cf}..."
    
    with patch("app.ai.routing.text_extraction_service.extract_text", return_value=mock_text):
        matched = await regex_router.find_client_by_regex(db, "fake_path.pdf", "application/pdf")
        
        assert matched is not None
        assert matched.id == cliente.id
        assert matched.codice_fiscale == test_cf
