import api from './api';

export interface DashboardStats {
    totale_clienti: number;
    totale_documenti: number;
    documenti_da_assegnare: number;
}

export async function getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/dashboard/stats');
    return response.data;
}
