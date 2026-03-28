interface Cliente {
  id: number;
  short_id: number | null;
  nome: string;
  cognome: string | null;
  codice_fiscale: string | null;
  partita_iva: string | null;
  tipo: "persona_fisica" | "azienda";
  email: string | null;
  telefono: string | null;
  created_at: string;
  updated_at: string;
}

interface ClienteCreate {
  nome: string;
  short_id?: number;
  cognome?: string;
  codice_fiscale?: string;
  partita_iva?: string;
  tipo?: "persona_fisica" | "azienda";
  email?: string;
  telefono?: string;
}

type ClienteUpdate = Partial<ClienteCreate>;

export type { Cliente, ClienteCreate, ClienteUpdate };