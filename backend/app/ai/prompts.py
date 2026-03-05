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

MACRO_DESCRIPTIONS: dict[str, str] = {
    "fiscale": "Documenti per dichiarazioni, imposte, avvisi (es. 730, REDDITI, F24, Comunicazioni AdE)",
    "lavoro": "Documenti relativi al personale (es. Buste Paga, CU, Contratti di assunzione)",
    "amministrazione": "Documenti gestionali e contabili (es. Fatture, Bilanci, Visure)",
    "altro": "Documenti non classificabili nelle categorie precedenti",
}

MAX_TEXT_CHARS: int = 4000


def build_classification_prompt(
    text: str,
    available_types: list[str],
    clienti_context: list[dict] | None = None,
    skip_client_id: bool = False,
) -> str:
    """Build the document classification prompt.

    Args:
        text: Full extracted text (truncated to MAX_TEXT_CHARS internally).
        available_types: Valid TipoDocumento enum values to include.
        clienti_context: Optional list of client dicts for matching.
        skip_client_id: If True, tell the LLM to skip client identification.

    Returns:
        Prompt string ready to send to any LLM.
    """
    tipo_lines = "\n".join(
        f"- {tipo}: {TIPO_DESCRIPTIONS.get(tipo, '')}"
        for tipo in available_types
    )

    macro_lines = "\n".join(
        f"- {macro}: {desc}"
        for macro, desc in MACRO_DESCRIPTIONS.items()
    )

    clienti_section = ""
    if clienti_context and not skip_client_id:
        names = [
            " ".join(filter(None, [c.get("nome"), c.get("cognome"), c.get("codice_fiscale")]))
            for c in clienti_context
        ]
        clienti_section = (
            "\nCERCA DI IDENTIFICARE IL CLIENTE tra i seguenti:\n"
            + "\n".join(f"- {n}" for n in names if n)
            + "\n"
        )
    elif skip_client_id:
        clienti_section = "\nNON IDENTIFICARE IL CLIENTE. È già stato identificato dal sistema deterministico.\n"

    truncated_text = text[:MAX_TEXT_CHARS]
    if len(text) > MAX_TEXT_CHARS:
        truncated_text += "\n[... testo troncato ...]"

    client_task = "5. Identifica il CLIENTE se presente nel testo (confrontandolo con la LISTA CLIENTI CONTESTUALE)."
    if skip_client_id:
        client_task = "5. SKIP: Il cliente è già noto, non cercarlo."

    return f"""PERSONA:
Sei un Consulente Fiscale Senior esperto in fiscalità italiana e gestione documentale per studi professionali. Il tuo compito è analizzare documenti contabili e fiscali con estrema precisione.

TASK:
1. Analizza il TESTO ESTRATTO (OCR) fornito in fondo.
2. Determina la MACRO-CATEGORIA corretta tra quelle disponibili.
3. Identifica la CATEGORIA corretta tra quelle in TIPI DOCUMENTO DISPONIBILI.
4. Indica l'ANNO DI COMPETENZA del documento (es. l'anno a cui si riferiscono le imposte o la prestazione lavorativa).
{client_task}
6. Estrai, se presenti, il Codice Fiscale (CF) e la Partita IVA (PI) del soggetto a cui si riferisce il documento.
7. Fornisci una descrizione specifica in 'tipo_documento_raw' (es: "Fattura Proforma", "Modello F24 Semplificato").
8. Determina la 'confidence' (0.0-1.0). Sii prudente se il testo è molto disturbato o ambiguo.

CONTEXT & RULES (MACRO-CATEGORIE):
{macro_lines}

CONTEXT & RULES (TIPI DOCUMENTO):
- F24: Cerca parole come "Delega irrevocabile", "Sezione Erario/INPS", codici tributo.
- FATTURA: Cerca "P.IVA", "Imponibile", "Aliquota", "Totale a pagare".
- CU: Cerca "Certificazione di cui all'art. 4", "Ritenute operate".
- DICHIARAZIONE REDDITI: Cerca "Quadro RN", "Modello 730", "Redditi Persone Fisiche".
- Se l'anno non è esplicito, cerca date di emissione o periodi di riferimento.
- Se il testo non permette una classificazione certa, usa 'altro'.

TIPI DOCUMENTO DISPONIBILI:
{tipo_lines}

LISTA CLIENTI CONTESTUALE:
{clienti_section}

TESTO ESTRATTO DAL DOCUMENTO:
{truncated_text}

Restituisci il risultato in formato JSON coerente con lo schema richiesto:
{{
  "macro_categoria": "string",
  "tipo_documento": "string",
  "tipo_documento_raw": "string",
  "anno_competenza": integer or null,
  "confidence": number,
  "cliente_suggerito": "string or null",
  "codice_fiscale": "string or null",
  "partita_iva": "string or null",
  "contratto_suggerito": "string or null"
}}
"""


def build_rag_chat_prompt(query: str, chunks: list[dict]) -> str:
    """
    Build a prompt for RAG-based chat using retrieved document chunks.
    """
    context_parts = []
    for chunk in chunks:
        doc_id = chunk.get("document_id")
        meta = chunk.get("metadata", {})
        file_name = meta.get("file_name", f"Documento {doc_id}")
        text = chunk.get("text", "")
        context_parts.append(f"--- DOCUMENTO ID: {doc_id} (Nome: {file_name}) ---\n{text}")

    context_str = "\n\n".join(context_parts)

    return f"""Sei un assistente esperto dello studio professionale DocuFiscal. 
Il tuo compito è rispondere alle domande degli utenti basandoti ESCLUSIVAMENTE sui documenti forniti nel CONTESTO sotto.

REGOLE:
1. Se il contesto contiene la risposta, rispondi in modo professionale ed esaustivo usando il formato Markdown.
2. Cita sempre i documenti di riferimento inserendo nel testo della risposta dei riferimenti come [ID: numero].
3. Alla fine della risposta, aggiungi SEMPRE una sezione tecnica delimitata da '--- CITATIONS ---' che contenga esclusivamente un array JSON con gli ID numerici dei documenti citati, ad esempio: [105, 120].
4. Se il contesto NON contiene informazioni sufficienti, spiega gentilmente che non hai dati su quell'argomento specifico tra i documenti caricati.
5. Non inventare informazioni non presenti nei documenti.
6. Rispondi in Italiano.

CONTESTO DOCUMENTI:
{context_str}

DOMANDA UTENTE:
{query}

RISPOSTA:
"""
