interface Contratto {
  id: number;
  cliente_id: number;
  tipo_contratto_id: number;
  data_inizio: string;
  data_fine: string | null;
  stato: "attivo" | "scaduto" | "sospeso";
  note: string | null;
  created_at: string;
  updated_at: string;
}

interface ContrattoCreate {
  cliente_id: number;
  tipo_contratto_id: number;
  data_inizio: string;
  data_fine?: string;
  stato?: "attivo" | "scaduto" | "sospeso";
  note?: string;
}

type ContrattoUpdate = Partial<ContrattoCreate>;

export type { Contratto, ContrattoCreate, ContrattoUpdate };