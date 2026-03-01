"""
Shared prompt utilities for document classification.
"""

TIPO_DESCRIPTIONS: dict[str, str] = {
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

MAX_TEXT_CHARS: int = 4000


def build_classification_prompt(
    text: str,
    available_types: list[str],
    clienti_context: list[dict] | None = None,
) -> str:
    """Build the document classification prompt.

    Args:
        text: Full extracted text (truncated to MAX_TEXT_CHARS internally).
        available_types: Valid TipoDocumento enum values to include.
        clienti_context: Optional list of client dicts with keys
            ``nome``, ``cognome``, ``codice_fiscale`` for entity matching.

    Returns:
        Prompt string ready to send to any LLM.
    """
    tipo_lines = "\n".join(
        f"- {tipo}: {TIPO_DESCRIPTIONS.get(tipo, '')}"
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

    truncated_text = text[:MAX_TEXT_CHARS]
    if len(text) > MAX_TEXT_CHARS:
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
