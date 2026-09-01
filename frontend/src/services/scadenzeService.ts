import api from './api';
import type { Scadenza, ScadenzaFilters } from '../types/scadenza';

export const getScadenze = async (filters?: ScadenzaFilters): Promise<Scadenza[]> => {
    const params: Record<string, string | number | boolean> = {};
    if (filters) {
        if (filters.tipo_scadenza) params.tipo_scadenza = filters.tipo_scadenza;
        if (filters.cliente_id !== undefined) params.cliente_id = filters.cliente_id;
        if (filters.da_data) params.da_data = filters.da_data;
        if (filters.a_data) params.a_data = filters.a_data;
        if (filters.verificato !== undefined) params.verificato = filters.verificato;
        if (filters.search) params.search = filters.search;
    }
    const response = await api.get<Scadenza[]>('/scadenze', { params });
    return response.data;
};
