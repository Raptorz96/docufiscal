import api from '@/services/api';
import type { ClassificazioneOverride, Documento, DocumentoUpdate } from '@/types/documento';

interface GetDocumentiParams {
  cliente_id?: number;
  contratto_id?: number;
  tipo_documento?: string;
  skip?: number;
  limit?: number;
}

export const getDocumenti = async (params?: GetDocumentiParams): Promise<Documento[]> => {
  const response = await api.get('/documenti/', { params });
  return response.data;
};

export const getDocumento = async (id: number): Promise<Documento> => {
  const response = await api.get(`/documenti/${id}`);
  return response.data;
};

export const uploadDocumento = async (data: FormData): Promise<Documento> => {
  const response = await api.post('/documenti/upload', data);
  return response.data;
};

export const updateDocumento = async (id: number, data: DocumentoUpdate): Promise<Documento> => {
  const response = await api.put(`/documenti/${id}`, data);
  return response.data;
};

export const classificaDocumento = async (
  id: number,
  data: Partial<ClassificazioneOverride>,
): Promise<Documento> => {
  const response = await api.patch(`/documenti/${id}/classifica`, data);
  return response.data;
};

export const deleteDocumento = async (id: number): Promise<void> => {
  await api.delete(`/documenti/${id}`);
};

export const downloadDocumento = async (id: number, fileName: string): Promise<void> => {
  const response = await api.get(`/documenti/${id}/download`, {
    responseType: 'blob',
  });

  const url = URL.createObjectURL(response.data as Blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
