export interface ContrattoScadenza {
    id: number;
    cliente_id: number;
    cliente_nome: string;
    tipo_contratto_nome: string;
    data_scadenza: string;
    giorni_rimanenti: number;
}

export interface DashboardStats {
    totale_clienti: number;
    totale_documenti: number;
    documenti_da_assegnare: number;
}
