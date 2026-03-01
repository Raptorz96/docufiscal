"""
Text extraction service for PDF and image documents.

System dependencies required:
- Tesseract OCR: sudo apt install tesseract-ocr tesseract-ocr-ita
- Poppler (for pdf2image): sudo apt install poppler-utils
- Windows: Tesseract installer from https://github.com/UB-Mannheim/tesseract/wiki (add to PATH)
"""
import logging
import re
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class TextExtractionService:
    """Extracts text from PDF and image documents stored in the local filesystem."""

    def extract_text(self, file_path: str, mime_type: str) -> str:
        """Extract text from a document given its relative path and MIME type.

        Args:
            file_path: Relative path as stored in DB (relative to STORAGE_ROOT).
            mime_type: MIME type of the document.

        Returns:
            Extracted text string, or empty string if extraction fails.
        """
        try:
            abs_path = str(Path(settings.STORAGE_ROOT) / file_path)

            if mime_type == "application/pdf":
                return self._extract_from_pdf(abs_path)
            elif mime_type in ("image/jpeg", "image/png"):
                return self._extract_from_image(abs_path)
            else:
                logger.warning("Unsupported MIME type for text extraction: %s", mime_type)
                return ""
        except Exception:
            logger.exception("Unexpected error during text extraction for %s", file_path)
            return ""

    def _extract_from_pdf(self, abs_path: str) -> str:
        """Extract text from a PDF file using PyPDF2, with OCR fallback.

        Falls back to OCR if extracted text is empty or shorter than 50 characters.
        """
        try:
            import PyPDF2  # noqa: PLC0415

            with open(abs_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = [page.extract_text() or "" for page in reader.pages]

            text = self._normalize_whitespace(" ".join(pages_text))

            if len(text) < 50:
                logger.info("PDF text too short (%d chars), falling back to OCR: %s", len(text), abs_path)
                return self._extract_from_pdf_ocr(abs_path)

            return text

        except FileNotFoundError:
            logger.error("File not found: %s", abs_path)
            return ""
        except Exception:
            logger.exception("Error extracting text from PDF: %s", abs_path)
            return ""

    def _extract_from_pdf_ocr(self, abs_path: str) -> str:
        """Extract text from a PDF via OCR by converting pages to images first."""
        try:
            import pytesseract  # noqa: PLC0415
            from pdf2image import convert_from_path  # noqa: PLC0415

            images = convert_from_path(abs_path)
            pages_text = [pytesseract.image_to_string(img, lang="ita") for img in images]
            return self._normalize_whitespace(" ".join(pages_text))

        except FileNotFoundError:
            logger.error("File not found: %s", abs_path)
            return ""
        except pytesseract.TesseractNotFoundError:  # type: ignore[attr-defined]
            logger.error("Tesseract OCR not installed or not found in PATH")
            return ""
        except Exception:
            logger.exception("Error during PDF OCR extraction: %s", abs_path)
            return ""

    def _extract_from_image(self, abs_path: str) -> str:
        """Extract text from an image file using Tesseract OCR."""
        try:
            import pytesseract  # noqa: PLC0415
            from PIL import Image  # noqa: PLC0415

            img = Image.open(abs_path)
            text = pytesseract.image_to_string(img, lang="ita")
            return self._normalize_whitespace(text)

        except FileNotFoundError:
            logger.error("File not found: %s", abs_path)
            return ""
        except pytesseract.TesseractNotFoundError:  # type: ignore[attr-defined]
            logger.error("Tesseract OCR not installed or not found in PATH")
            return ""
        except Exception:
            logger.exception("Error extracting text from image: %s", abs_path)
            return ""

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Strip and collapse internal whitespace."""
        return re.sub(r"\s+", " ", text).strip()


text_extraction_service = TextExtractionService()
