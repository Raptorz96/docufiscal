export interface Scadenza {
    id: number;
    documento_id: number | null;
    contratto_id: number | null;
    cliente_id: number;
    cliente_nome: string;
    file_name: string;
    tipo_scadenza: string;
    descrizione: string | null;
    data_scadenza: string | null;
    data_inizio: string | null;
    giorni_rimanenti: number | null;
    canone: string | null;
    rinnovo_automatico: boolean | null;
    preavviso_disdetta: string | null;
    confidence_score: number;
    verificato: boolean;
    is_contratto: boolean;
    created_at: string;
}

export interface ScadenzaFilters {
    tipo_scadenza?: string;
    cliente_id?: number;
    da_data?: string;
    a_data?: string;
    verificato?: boolean;
    search?: string;
}
