type TipoDocumento =
  | 'dichiarazione_redditi'
  | 'fattura'
  | 'f24'
  | 'cu'
  | 'visura_camerale'
  | 'busta_paga'
  | 'contratto'
  | 'bilancio'
  | 'comunicazione_agenzia'
  | 'documento_identita'
  | 'altro';

interface Documento {
  id: number;
  cliente_id: number;
  contratto_id: number | null;
  tipo_documento: TipoDocumento;
  tipo_documento_raw: string | null;
  file_name: string;
  file_size: number;
  mime_type: string;
  classificazione_ai: unknown;
  confidence_score: number | null;
  macro_categoria?: 'fiscale' | 'lavoro' | 'amministrazione' | 'altro';
  anno_competenza?: number | null;
  verificato_da_utente: boolean;
  note: string | null;
  created_at: string;
  updated_at: string;
}

interface DocumentoUpdate {
  contratto_id?: number | null;
  tipo_documento?: TipoDocumento;
  tipo_documento_raw?: string | null;
  note?: string | null;
  verificato_da_utente?: boolean;
}

interface ClassificazioneOverride {
  tipo_documento?: TipoDocumento; // opzionale: undefined = conferma pura senza cambio tipo
  macro_categoria?: 'fiscale' | 'lavoro' | 'amministrazione' | 'altro';
  anno_competenza?: number | null;
  cliente_id?: number;
  contratto_id?: number | null;
  note?: string | null;
}

export type { TipoDocumento, Documento, DocumentoUpdate, ClassificazioneOverride };
