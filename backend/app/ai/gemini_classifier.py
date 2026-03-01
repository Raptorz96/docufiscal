"""
Document classifier implementation using Google Gemini API.
"""
import json
import logging

from google import genai

from app.ai.classifier import BaseClassifier, ClassificationResult
from app.core.config import settings

logger = logging.getLogger(__name__)

_TIPO_DESCRIPTIONS = {
    "dichiarazione_redditi": "Modello 730, Modello Redditi PF/SC/SP",
    "fattura": "Fatture di acquisto o vendita",
    "f24": "Modello F24 per pagamento imposte",
    "cu": "Certificazione Unica",
    "visura_camerale": "Visura della Camera di Commercio",
    "busta_paga": "Cedolino paga / busta paga",
    "contratto": "Contratti di lavoro, affitto, servizi",
    "bilancio": "Bilancio d'esercizio, stato patrimoniale",
    "comunicazione_agenzia": "Comunicazioni dall'Agenzia delle Entrate",
    "documento_identita": "Carta d'identità, codice fiscale, passaporto",
    "altro": "Documento non classificabile nelle categorie precedenti",
}

_MAX_TEXT_CHARS = 4000

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "tipo_documento": {"type": "string"},
        "tipo_documento_raw": {"type": "string"},
        "confidence": {"type": "number"},
        "cliente_suggerito": {"type": "string"},
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
            prompt = self._build_prompt(text, available_types, clienti_context)

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
                contratto_suggerito=data.get("contratto_suggerito") or None,
                raw_response=data,
            )

        except Exception:
            logger.exception("Gemini classification failed")
            return _DEFAULT_RESULT

    def _build_prompt(
        self,
        text: str,
        available_types: list[str],
        clienti_context: list[dict] | None,
    ) -> str:
        """Build the classification prompt.

        Args:
            text: Full extracted text (will be truncated to _MAX_TEXT_CHARS).
            available_types: Valid enum values to include in the prompt.
            clienti_context: Optional client list for entity matching.

        Returns:
            Prompt string ready to send to the model.
        """
        tipo_lines = "\n".join(
            f"- {tipo}: {_TIPO_DESCRIPTIONS.get(tipo, '')}"
            for tipo in available_types
        )

        clienti_section = ""
        if clienti_context:
            names = [
                " ".join(filter(None, [c.get("nome"), c.get("cognome"), c.get("codice_fiscale")]))
                for c in clienti_context
            ]
            clienti_section = (
                "\nCERCA DI IDENTIFICARE IL CLIENTE tra i seguenti:\n"
                + "\n".join(f"- {n}" for n in names if n)
                + "\n"
            )

        truncated_text = text[:_MAX_TEXT_CHARS]
        if len(text) > _MAX_TEXT_CHARS:
            truncated_text += "\n[... testo troncato ...]"

        return f"""Sei un assistente specializzato nella classificazione di documenti fiscali italiani \
per uno studio di commercialisti.

Analizza il seguente testo estratto da un documento e classificalo.

TIPI DOCUMENTO DISPONIBILI:
{tipo_lines}
{clienti_section}
TESTO DEL DOCUMENTO:
{truncated_text}

Classifica il documento. Per "confidence" usa un valore da 0.0 a 1.0 \
che indica quanto sei sicuro della classificazione.
Per "tipo_documento" usa SOLO uno dei valori dalla lista sopra.
Per "tipo_documento_raw" fornisci una descrizione libera del tipo di documento."""
