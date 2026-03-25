export interface ScadenzaDashboard {
    id: number;
    documento_id: number;
    cliente_id: number;
    cliente_nome: string;
    file_name: string;
    tipo_scadenza: string;
    descrizione: string | null;
    data_scadenza: string | null;
    giorni_rimanenti: number | null;
    canone: string | null;
    rinnovo_automatico: boolean | null;
    preavviso_disdetta: string | null;
    confidence_score: number;
    verificato: boolean;
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
    scadenze_scadute: number;
    scadenze_in_scadenza: number;
    scadenze_critiche: ScadenzaDashboard[];
    ultimi_documenti: DocumentoRecente[];
}
