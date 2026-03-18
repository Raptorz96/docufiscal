import api from '@/services/api';
import type { TipoContratto } from '@/types/tipoContratto';

export const getTipiContratto = async (): Promise<TipoContratto[]> => {
  const response = await api.get('/tipi-contratto/');
  return response.data;
};