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

    return f"""PERSONA:
Sei un Consulente Fiscale Senior esperto in fiscalità italiana e gestione documentale per studi professionali. Il tuo compito è analizzare documenti contabili e fiscali con estrema precisione.

TASK:
1. Analizza il TESTO ESTRATTO (OCR) fornito in fondo.
2. Identifica la categoria corretta tra quelle in TIPI DOCUMENTO DISPONIBILI.
3. Identifica il CLIENTE se presente nel testo (confrontandolo con la LISTA CLIENTI CONTESTUALE).
4. Estrai, se presenti, il Codice Fiscale (CF) e la Partita IVA (PI) del soggetto a cui si riferisce il documento.
5. Fornisci una descrizione specifica in 'tipo_documento_raw' (es: "Fattura Proforma", "Modello F24 Semplificato").
6. Determina la 'confidence' (0.0-1.0). Sii prudente se il testo è molto disturbato o ambiguo.

CONTEXT & RULES:
- F24: Cerca parole come "Delega irrevocabile", "Sezione Erario/INPS", codici tributo.
- FATTURA: Cerca "P.IVA", "Imponibile", "Aliquota", "Totale a pagare".
- CU: Cerca "Certificazione di cui all'art. 4", "Ritenute operate".
- DICHIARAZIONE REDDITI: Cerca "Quadro RN", "Modello 730", "Redditi Persone Fisiche".
- Se il testo non permette una classificazione certa, usa 'altro'.

TIPI DOCUMENTO DISPONIBILI:
{tipo_lines}

LISTA CLIENTI CONTESTUALE:
{clienti_section}

TESTO ESTRATTO DAL DOCUMENTO:
{truncated_text}

Restituisci il risultato in formato JSON coerente con lo schema richiesto.
"""
