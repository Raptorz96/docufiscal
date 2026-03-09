export interface ContrattoScadenza {
    id: number;
    cliente_id: number;
    cliente_nome: string;
    tipo_contratto_nome: string;
    data_scadenza: string;
    giorni_rimanenti: number;
}

export interface DocumentoRecente {
    id: number;
    file_name: string;
    tipo_documento: string;
    cliente_nome: string;
    created_at: string;
    verificato_da_utente: boolean;
    confidence_score: number | null;
}

export interface DashboardStats {
    totale_clienti: number;
    totale_documenti: number;
    totale_contratti_attivi: number;
    documenti_da_verificare: number;
    contratti_scaduti: number;
    contratti_in_scadenza: number;
    contratti_critici: ContrattoScadenza[];
    ultimi_documenti: DocumentoRecente[];
}
