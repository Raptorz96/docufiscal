import api from './api';
import type { DashboardStats, ContrattoScadenza, DocumentoRecente } from '@/types/dashboard';

export async function getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/dashboard/stats');
    return response.data;
}

