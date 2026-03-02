import os
from fpdf import FPDF
from pathlib import Path

# Dati del seed identificati
# Cliente: Marco Rossi
CODICE_FISCALE_VALIDO = "RSSMRC85A01H501Z"
# Cliente: Edilrossi Srl
PARTITA_IVA_VALIDA = "03421670283"
# Dato inventato per test fallimento matching
PARTITA_IVA_INVENTATA = "IT99999999999"

def generate_pdf(filename, content):
    pdf = FPDF()
    pdf.add_page()
    # Usa Courier (font core) per evitare dipendenze da font di sistema/fontTools
    pdf.set_font("Courier", size=12)
    
    # Scrittura del contenuto riga per riga
    for line in content:
        # width=0 usa tutto lo spazio disponibile nella riga
        pdf.cell(0, 10, txt=line, ln=True, align='L')
    
    # Creazione cartella se non esiste
    output_path = Path("test_files") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    pdf.output(str(output_path))
    print(f"Generato: {output_path}")

def main():
    # 1. Fattura per matching tramite Partita IVA
    generate_pdf("test_fattura_matching.pdf", [
        "Fattura Elettronica #2024-001",
        "Data: 02/03/2026",
        "Cedente/Prestatore: Edilrossi Srl",
        f"Partita IVA: {PARTITA_IVA_VALIDA}",
        "---",
        "Descrizione: Lavori di manutenzione straordinaria",
        "Importo Totale: 1.540,00 EUR",
        "Scadenza: 31/03/2026"
    ])

    # 2. Modello F24 per matching tramite Codice Fiscale
    generate_pdf("test_f24_matching.pdf", [
        "Modello di pagamento F24",
        "Contribuentre: Marco Rossi",
        f"Codice Fiscale: {CODICE_FISCALE_VALIDO}",
        "---",
        "Sezione Erario",
        "Codice Tributo: 4001",
        "Anno di riferimento: 2023",
        "Importo a debito: 450,00 EUR"
    ])

    # 3. Ricevuta sconosciuta (nessun match)
    generate_pdf("test_sconosciuto.pdf", [
        "Ricevuta Generica",
        "Esercente: Ristorante Da Mario",
        f"P.IVA: {PARTITA_IVA_INVENTATA}",
        "---",
        "Data: 01/03/2026",
        "Importo: 45,00 EUR",
        "Metodo Pagamento: Contanti"
    ])

if __name__ == "__main__":
    main()
