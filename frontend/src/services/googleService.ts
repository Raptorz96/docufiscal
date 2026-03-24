import api from './api';

export async function getGoogleStatus(): Promise<{ connected: boolean; scope: string | null }> {
  const res = await api.get('/google/status');
  return res.data;
}

export async function getGoogleAuthorizeUrl(): Promise<string> {
  const res = await api.get('/google/authorize');
  return res.data.authorization_url;
}

export async function disconnectGoogle(): Promise<void> {
  await api.delete('/google/disconnect');
}
