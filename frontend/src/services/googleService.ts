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

export async function createEventFromScadenza(
  scadenzaId: number,
  reminderMinutes: number = 1440
): Promise<{ success: boolean; event_link?: string; error?: string }> {
  const res = await api.post('/calendar/events/from-scadenza', {
    scadenza_id: scadenzaId,
    reminder_minutes: reminderMinutes,
  });
  return res.data;
}
