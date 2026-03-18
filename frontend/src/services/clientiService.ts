import api from '@/services/api';
import type { Cliente, ClienteCreate, ClienteUpdate } from '@/types/cliente';

interface GetClientiParams {
  tipo?: string;
  search?: string;
}

export const getClienti = async (params?: GetClientiParams): Promise<Cliente[]> => {
  const response = await api.get('/clienti', { params });
  return response.data;
};

export const getCliente = async (id: number): Promise<Cliente> => {
  const response = await api.get(`/clienti/${id}`);
  return response.data;
};

export const createCliente = async (data: ClienteCreate): Promise<Cliente> => {
  const response = await api.post('/clienti', data);
  return response.data;
};

export const updateCliente = async (id: number, data: ClienteUpdate): Promise<Cliente> => {
  const response = await api.put(`/clienti/${id}`, data);
  return response.data;
};

export const deleteCliente = async (id: number): Promise<void> => {
  await api.delete(`/clienti/${id}`);
};