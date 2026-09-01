interface TipoContratto {
  id: number;
  nome: string;
  descrizione: string | null;
  categoria: string;
}

export type { TipoContratto };