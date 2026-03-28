"""
Router to identify clients using Regex before LLM classification.
"""
import logging
import re
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai.text_extraction import text_extraction_service
from app.models.cliente import Cliente

logger = logging.getLogger(__name__)

# Regex for Italian Partita IVA (11 digits)
PI_REGEX = re.compile(r"\b\d{11}\b")

# Regex for Italian Codice Fiscale (16 chars: 6 letters, 2 digits, 1 letter, 2 digits, 1 letter, 3 digits, 1 letter)
CF_REGEX = re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", re.IGNORECASE)


class RegexRouter:
    """Identifies clients by searching for CF or PI in document text using Regex."""

    async def find_client_by_regex(
        self, db: Session, file_path: str, mime_type: str
    ) -> Optional[Cliente]:
        """Attempt to find a client by extracting text from the first 2 pages.

        Args:
            db: Database session.
            file_path: Relative path to the file.
            mime_type: MIME type of the file.

        Returns:
            Matched Cliente object or None.
        """
        if mime_type != "application/pdf":
            # For now, regex routing is optimized for PDF text extraction (fast with fitz)
            # OCR on images is slower and better handled by the full classification flow
            return None

        try:
            # Extract first 2 pages for fast routing
            text = text_extraction_service.extract_text(file_path, mime_type, max_pages=2)
            if not text.strip():
                return None

            # 1. Search for Partita IVA
            pi_matches = PI_REGEX.findall(text)
            for pi in pi_matches:
                cliente = db.query(Cliente).filter(Cliente.partita_iva == pi).first()
                if cliente:
                    logger.info("Regex Match: Found client %d via Partita IVA: %s", cliente.id, pi)
                    return cliente

            # 2. Search for Codice Fiscale
            cf_matches = CF_REGEX.findall(text)
            for cf in cf_matches:
                cf_upper = cf.upper()
                cliente = db.query(Cliente).filter(Cliente.codice_fiscale == cf_upper).first()
                if cliente:
                    logger.info("Regex Match: Found client %d via Codice Fiscale: %s", cliente.id, cf_upper)
                    return cliente

        except Exception:
            logger.exception("Error during Regex routing for %s", file_path)

        return None


regex_router = RegexRouter()
