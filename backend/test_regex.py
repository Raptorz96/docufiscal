from app.ai.classifier import extract_short_id

names = [
    "#105_fattura.pdf",
    "105_fattura.pdf",
    "105 fattura.pdf",
    "#105 fattura.pdf",
    "105-fattura.pdf",
    "1051) 2 (1).pdf",
    "105 Software guidi CAPITOLATO.pdf"
]

for n in names:
    print(f"{n} -> {extract_short_id(n)}")
