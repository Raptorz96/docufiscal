import api from '@/services/api';
import type { Contratto, ContrattoCreate, ContrattoUpdate } from '@/types/contratto';

interface GetContrattiParams {
  cliente_id?: number;
  tipo_contratto_id?: number;
  stato?: string;
}

export const getContratti = async (params?: GetContrattiParams): Promise<Contratto[]> => {
  const response = await api.get('/contratti', { params });
  return response.data;
};

export const getContratto = async (id: number): Promise<Contratto> => {
  const response = await api.get(`/contratti/${id}`);
  return response.data;
};

export const createContratto = async (data: ContrattoCreate): Promise<Contratto> => {
  const response = await api.post('/contratti', data);
  return response.data;
};

export const updateContratto = async (id: number, data: ContrattoUpdate): Promise<Contratto> => {
  const response = await api.put(`/contratti/${id}`, data);
  return response.data;
};

export const deleteContratto = async (id: number): Promise<void> => {
  await api.delete(`/contratti/${id}`);
};