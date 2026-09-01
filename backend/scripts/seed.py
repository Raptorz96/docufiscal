"""Seed script for DocuFiscal - popola il DB con dati demo.

Eseguire con:
    cd backend && python -m scripts.seed
"""
import sys
from datetime import date

from sqlalchemy.orm import Session

from app.core import SessionLocal, hash_password
from app.models import User, TipoContratto, Cliente, Contratto

# ── colori ANSI ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

def ok(msg: str)   -> None: print(f"{GREEN}✅ {msg}{RESET}")
def skip(msg: str) -> None: print(f"{YELLOW}⏭️  {msg}{RESET}")
def err(msg: str)  -> None: print(f"{RED}❌ {msg}{RESET}")


# ── dati seed ────────────────────────────────────────────────────────────────

ADMIN_USER = {
    "email":    "admin@docufiscal.it",
    "password": "admin123",
    "nome":     "Admin",
    "cognome":  "DocuFiscal",
    "role":     "admin",
}

TIPI_CONTRATTO = [
    {"nome": "Dichiarazione Redditi",   "categoria": "fiscale",    "descrizione": "Gestione e presentazione dichiarazione dei redditi persone fisiche e giuridiche."},
    {"nome": "Contabilità Ordinaria",   "categoria": "fiscale",    "descrizione": "Tenuta della contabilità ordinaria con registri IVA e libro giornale."},
    {"nome": "Contabilità Semplificata","categoria": "fiscale",    "descrizione": "Contabilità in regime semplificato per professionisti e ditte individuali."},
    {"nome": "Consulenza Fiscale",      "categoria": "fiscale",    "descrizione": "Consulenza e assistenza su tematiche fiscali e tributarie."},
    {"nome": "Gestione Payroll",        "categoria": "lavoro",     "descrizione": "Elaborazione buste paga, contributi e adempimenti previdenziali."},
    {"nome": "Consulenza Societaria",   "categoria": "societario", "descrizione": "Assistenza nella costituzione, modifica e scioglimento di società."},
]

CLIENTI = [
    # persone fisiche
    {
        "tipo": "persona_fisica",
        "nome": "Marco", "cognome": "Rossi",
        "codice_fiscale": "RSSMRC85A01H501Z",
        "partita_iva": None,
        "email": "marco.rossi@email.it",
        "telefono": "333 1234567",
    },
    {
        "tipo": "persona_fisica",
        "nome": "Giulia", "cognome": "Bianchi",
        "codice_fiscale": "BNCGLI92D41F205X",
        "partita_iva": None,
        "email": "giulia.bianchi@libero.it",
        "telefono": "347 9876543",
    },
    {
        "tipo": "persona_fisica",
        "nome": "Luca", "cognome": "Ferrari",
        "codice_fiscale": "FRRLCU78C12L219P",
        "partita_iva": None,
        "email": "luca.ferrari@gmail.com",
        "telefono": "320 4561230",
    },
    {
        "tipo": "persona_fisica",
        "nome": "Anna", "cognome": "Conti",
        "codice_fiscale": "CNTNNA65E45G273Q",
        "partita_iva": None,
        "email": "anna.conti@tiscali.it",
        "telefono": "338 7654321",
    },
    # aziende
    {
        "tipo": "azienda",
        "nome": "Edilrossi Srl", "cognome": None,
        "codice_fiscale": None,
        "partita_iva": "03421670283",
        "email": "amministrazione@edilrossi.it",
        "telefono": "02 4893021",
    },
    {
        "tipo": "azienda",
        "nome": "TechMilano Srl", "cognome": None,
        "codice_fiscale": None,
        "partita_iva": "07812340156",
        "email": "info@techmilano.it",
        "telefono": "02 9876543",
    },
    {
        "tipo": "azienda",
        "nome": "Studio Legale Meroni", "cognome": None,
        "codice_fiscale": None,
        "partita_iva": "04567890121",
        "email": "segreteria@meroni-legale.it",
        "telefono": "011 3456789",
    },
    {
        "tipo": "azienda",
        "nome": "Panificio Savoia Snc", "cognome": None,
        "codice_fiscale": None,
        "partita_iva": "02198760349",
        "email": "panificio.savoia@hotmail.it",
        "telefono": "055 6789012",
    },
]

# Ogni contratto è (indice_cliente, indice_tipo, data_inizio, data_fine, stato, note)
# indici 0-based rispetto ai list sopra
CONTRATTI_SPEC = [
    (0, 0, date(2023, 1, 10), date(2023, 12, 31), "scaduto",  "Dichiarazione 730 anno 2022."),
    (0, 0, date(2024, 1, 15), date(2024, 12, 31), "scaduto",  "Dichiarazione 730 anno 2023."),
    (0, 3, date(2025, 3,  1), None,               "attivo",   "Consulenza ordinaria annuale."),
    (1, 2, date(2024, 4,  1), date(2024, 12, 31), "scaduto",  "Regime forfettario - primo anno."),
    (1, 0, date(2025, 1, 20), date(2025, 12, 31), "attivo",   "Dichiarazione redditi 2024."),
    (2, 4, date(2023, 6,  1), date(2024, 5, 31),  "scaduto",  "Payroll dipendente unico."),
    (2, 3, date(2024, 9,  1), None,               "sospeso",  "Sospeso in attesa chiarimenti fiscali."),
    (3, 0, date(2025, 2,  1), date(2025, 12, 31), "attivo",   None),
    (4, 1, date(2023, 1,  1), date(2023, 12, 31), "scaduto",  "Contabilità ordinaria esercizio 2023."),
    (4, 1, date(2024, 1,  1), None,               "attivo",   "Contabilità ordinaria esercizio 2024."),
    (5, 5, date(2024, 7, 15), None,               "attivo",   "Consulenza per aumento capitale sociale."),
    (6, 4, date(2025, 1,  1), None,               "attivo",   "Gestione buste paga 3 dipendenti."),
]


# ── funzioni seed ─────────────────────────────────────────────────────────────

def seed_admin(db: Session) -> User:
    existing = db.query(User).filter_by(email=ADMIN_USER["email"]).first()
    if existing:
        skip(f"Utente admin già presente ({ADMIN_USER['email']})")
        return existing
    try:
        user = User(
            email=ADMIN_USER["email"],
            hashed_password=hash_password(ADMIN_USER["password"]),
            nome=ADMIN_USER["nome"],
            cognome=ADMIN_USER["cognome"],
            role=ADMIN_USER["role"],
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        ok(f"Utente admin creato: {user.email}")
        return user
    except Exception as exc:
        db.rollback()
        err(f"Errore creazione admin: {exc}")
        sys.exit(1)


def seed_tipi_contratto(db: Session) -> list[TipoContratto]:
    results: list[TipoContratto] = []
    for spec in TIPI_CONTRATTO:
        existing = db.query(TipoContratto).filter_by(nome=spec["nome"]).first()
        if existing:
            skip(f"TipoContratto già presente: {spec['nome']}")
            results.append(existing)
            continue
        try:
            tc = TipoContratto(**spec)
            db.add(tc)
            db.commit()
            db.refresh(tc)
            ok(f"TipoContratto creato: {tc.nome} ({tc.categoria})")
            results.append(tc)
        except Exception as exc:
            db.rollback()
            err(f"Errore TipoContratto '{spec['nome']}': {exc}")
    return results


def seed_clienti(db: Session) -> list[Cliente]:
    results: list[Cliente] = []
    for spec in CLIENTI:
        # Cerca per codice_fiscale (persone fisiche) o partita_iva (aziende)
        existing = None
        if spec["codice_fiscale"]:
            existing = db.query(Cliente).filter_by(codice_fiscale=spec["codice_fiscale"]).first()
        elif spec["partita_iva"]:
            existing = db.query(Cliente).filter_by(partita_iva=spec["partita_iva"]).first()

        if existing:
            label = spec["codice_fiscale"] or spec["partita_iva"]
            skip(f"Cliente già presente: {spec['nome']} ({label})")
            results.append(existing)
            continue
        try:
            cliente = Cliente(**spec)
            db.add(cliente)
            db.commit()
            db.refresh(cliente)
            ok(f"Cliente creato: {cliente.nome} {cliente.cognome or ''} [{cliente.tipo}]")
            results.append(cliente)
        except Exception as exc:
            db.rollback()
            err(f"Errore Cliente '{spec['nome']}': {exc}")
    return results


def seed_contratti(
    db: Session,
    clienti: list[Cliente],
    tipi: list[TipoContratto],
) -> None:
    for idx_c, idx_t, data_inizio, data_fine, stato, note in CONTRATTI_SPEC:
        cliente = clienti[idx_c]
        tipo    = tipi[idx_t]

        existing = (
            db.query(Contratto)
            .filter_by(
                cliente_id=cliente.id,
                tipo_contratto_id=tipo.id,
                data_inizio=data_inizio,
            )
            .first()
        )
        if existing:
            skip(
                f"Contratto già presente: {cliente.nome} / {tipo.nome} / {data_inizio}"
            )
            continue
        try:
            contratto = Contratto(
                cliente_id=cliente.id,
                tipo_contratto_id=tipo.id,
                data_inizio=data_inizio,
                data_fine=data_fine,
                stato=stato,
                note=note,
            )
            db.add(contratto)
            db.commit()
            db.refresh(contratto)
            ok(
                f"Contratto creato: {cliente.nome} / {tipo.nome} / "
                f"{data_inizio} → {data_fine or '∞'} [{stato}]"
            )
        except Exception as exc:
            db.rollback()
            err(f"Errore Contratto ({cliente.nome} / {tipo.nome}): {exc}")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("\n══════════════════════════════════════════")
    print("  DocuFiscal — Seed database demo")
    print("══════════════════════════════════════════\n")

    db = SessionLocal()
    try:
        print("── Utente Admin ────────────────────────")
        seed_admin(db)

        print("\n── Tipi Contratto ──────────────────────")
        tipi = seed_tipi_contratto(db)

        print("\n── Clienti ─────────────────────────────")
        clienti = seed_clienti(db)

        print("\n── Contratti ───────────────────────────")
        seed_contratti(db, clienti, tipi)

    finally:
        db.close()

    print("\n══════════════════════════════════════════")
    print("  Seed completato.")
    print("══════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
