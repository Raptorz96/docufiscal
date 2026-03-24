import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AxiosError } from 'axios';
import { useAuth } from '../context/AuthContext';
import * as authService from '../services/authService';
import * as googleService from '../services/googleService';

const ProfilePage: React.FC = () => {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // --- Profile form state ---
  const [profileForm, setProfileForm] = useState({
    nome: '',
    cognome: '',
    email: '',
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState('');
  const [profileError, setProfileError] = useState('');

  // --- Password form state ---
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // --- Google Calendar state ---
  const [googleConnected, setGoogleConnected] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleConnectLoading, setGoogleConnectLoading] = useState(false);
  const [googleSuccess, setGoogleSuccess] = useState('');
  const [googleError, setGoogleError] = useState('');
  const [googleUnavailable, setGoogleUnavailable] = useState(false);

  // Populate profile form from user context on mount / user change
  useEffect(() => {
    if (user) {
      setProfileForm({
        nome: user.nome,
        cognome: user.cognome,
        email: user.email,
      });
    }
  }, [user]);

  // Fetch Google connection status on mount
  useEffect(() => {
    setGoogleLoading(true);
    googleService.getGoogleStatus()
      .then((status) => setGoogleConnected(status.connected))
      .catch(() => setGoogleUnavailable(true))
      .finally(() => setGoogleLoading(false));
  }, []);

  // Handle ?google=connected redirect from OAuth callback
  useEffect(() => {
    if (searchParams.get('google') === 'connected') {
      setGoogleSuccess('Google Calendar connesso con successo!');
      setGoogleConnected(true);
      searchParams.delete('google');
      setSearchParams(searchParams, { replace: true });
    }
  }, []);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileError('');
    setProfileSuccess('');

    // Determine if email is changing BEFORE making any request
    const emailChanged = profileForm.email !== user?.email;

    setProfileLoading(true);
    try {
      await authService.updateProfile({
        nome: profileForm.nome,
        cognome: profileForm.cognome,
        email: profileForm.email,
      });

      if (emailChanged) {
        // Token is now invalid (sub = old email). Logout immediately and
        // redirect to login with message — do NOT call refreshUser() here
        // as it would trigger the 401 global interceptor and lose the message.
        logout();
        navigate('/login', { state: { message: 'Email aggiornata. Effettua nuovamente il login.' } });
      } else {
        await refreshUser();
        setProfileSuccess('Profilo aggiornato con successo.');
      }
    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 409) {
          setProfileError('Email già in uso da un altro account.');
        } else {
          setProfileError('Errore imprevisto. Riprova.');
        }
      } else {
        setProfileError('Errore imprevisto. Riprova.');
      }
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    // Client-side validation
    if (passwordForm.new_password.length < 8) {
      setPasswordError('La nuova password deve essere di almeno 8 caratteri.');
      return;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('Le password non corrispondono.');
      return;
    }

    setPasswordLoading(true);
    try {
      await authService.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPasswordSuccess('Password aggiornata con successo.');
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      if (err instanceof AxiosError && err.response?.status === 400) {
        setPasswordError(err.response.data?.detail ?? 'Errore nella modifica della password.');
      } else {
        setPasswordError('Errore imprevisto. Riprova.');
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleGoogleConnect = async () => {
    setGoogleError('');
    setGoogleConnectLoading(true);
    try {
      const url = await googleService.getGoogleAuthorizeUrl();
      window.location.href = url;
    } catch {
      setGoogleError('Impossibile avviare la connessione con Google. Riprova.');
      setGoogleConnectLoading(false);
    }
  };

  const handleGoogleDisconnect = async () => {
    if (!window.confirm('Disconnettere Google Calendar? Le scadenze non genereranno più eventi automatici.')) {
      return;
    }
    setGoogleError('');
    setGoogleConnectLoading(true);
    try {
      await googleService.disconnectGoogle();
      setGoogleConnected(false);
      setGoogleSuccess('');
    } catch {
      setGoogleError('Errore durante la disconnessione. Riprova.');
    } finally {
      setGoogleConnectLoading(false);
    }
  };

  const inputClass =
    'w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1';
  const btnPrimary =
    'px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed';
  const btnSecondary =
    'px-4 py-2 bg-white text-gray-700 text-sm font-medium rounded-md border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed';

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('it-IT', {
        day: '2-digit', month: 'long', year: 'numeric',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Il mio profilo</h1>

      {/* Section 1 — Profile data */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Dati personali</h2>

        {/* Read-only info */}
        <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-md text-sm">
          <div>
            <span className="font-medium text-gray-500">Ruolo</span>
            <p className="text-gray-800 mt-0.5 capitalize">{user?.role ?? '—'}</p>
          </div>
          <div>
            <span className="font-medium text-gray-500">Registrato il</span>
            <p className="text-gray-800 mt-0.5">
              {user?.created_at ? formatDate(user.created_at) : '—'}
            </p>
          </div>
        </div>

        <form onSubmit={handleProfileSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass} htmlFor="nome">Nome</label>
              <input
                id="nome"
                type="text"
                required
                className={inputClass}
                value={profileForm.nome}
                onChange={(e) => setProfileForm((f) => ({ ...f, nome: e.target.value }))}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="cognome">Cognome</label>
              <input
                id="cognome"
                type="text"
                required
                className={inputClass}
                value={profileForm.cognome}
                onChange={(e) => setProfileForm((f) => ({ ...f, cognome: e.target.value }))}
              />
            </div>
          </div>

          <div>
            <label className={labelClass} htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              className={inputClass}
              value={profileForm.email}
              onChange={(e) => setProfileForm((f) => ({ ...f, email: e.target.value }))}
            />
            <p className="text-xs text-amber-600 mt-1">
              Attenzione: cambiare l'email richiede un nuovo accesso.
            </p>
          </div>

          {profileSuccess && (
            <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-md px-4 py-3">
              {profileSuccess}
            </div>
          )}
          {profileError && (
            <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md px-4 py-3">
              {profileError}
            </div>
          )}

          <div className="flex justify-end">
            <button type="submit" disabled={profileLoading} className={btnPrimary}>
              {profileLoading ? 'Salvataggio...' : 'Salva modifiche'}
            </button>
          </div>
        </form>
      </div>

      {/* Section 2 — Password change */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Cambia password</h2>

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className={labelClass} htmlFor="current_password">Password corrente</label>
            <input
              id="current_password"
              type="password"
              required
              autoComplete="current-password"
              className={inputClass}
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, current_password: e.target.value }))}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="new_password">Nuova password</label>
            <input
              id="new_password"
              type="password"
              required
              autoComplete="new-password"
              className={inputClass}
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, new_password: e.target.value }))}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="confirm_password">Conferma nuova password</label>
            <input
              id="confirm_password"
              type="password"
              required
              autoComplete="new-password"
              className={inputClass}
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, confirm_password: e.target.value }))}
            />
          </div>

          {passwordSuccess && (
            <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-md px-4 py-3">
              {passwordSuccess}
            </div>
          )}
          {passwordError && (
            <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md px-4 py-3">
              {passwordError}
            </div>
          )}

          <div className="flex justify-end">
            <button type="submit" disabled={passwordLoading} className={btnPrimary}>
              {passwordLoading ? 'Aggiornamento...' : 'Cambia password'}
            </button>
          </div>
        </form>
      </div>

      {/* Section 3 — Integrations */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Integrazioni</h2>

        {googleSuccess && (
          <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-md px-4 py-3 mb-4">
            {googleSuccess}
          </div>
        )}
        {googleError && (
          <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md px-4 py-3 mb-4">
            {googleError}
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Google Calendar icon */}
            <div className="w-9 h-9 flex items-center justify-center rounded-full bg-gray-100 shrink-0">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="#4285F4" strokeWidth="1.5"/>
                <path d="M3 8h18" stroke="#4285F4" strokeWidth="1.5"/>
                <path d="M8 3v5M16 3v5" stroke="#4285F4" strokeWidth="1.5" strokeLinecap="round"/>
                <text x="7" y="18" fontSize="7" fill="#EA4335" fontWeight="bold">31</text>
              </svg>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-800">Google Calendar</p>
              {googleLoading ? (
                <p className="text-xs text-gray-400">Verifica connessione...</p>
              ) : googleUnavailable ? (
                <p className="text-xs text-gray-400">Non disponibile</p>
              ) : googleConnected ? (
                <span className="inline-flex items-center gap-1 text-xs text-green-600 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
                  Connesso
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-300 inline-block" />
                  Non connesso
                </span>
              )}
            </div>
          </div>

          {!googleLoading && !googleUnavailable && (
            googleConnected ? (
              <button
                onClick={handleGoogleDisconnect}
                disabled={googleConnectLoading}
                className={btnSecondary}
              >
                {googleConnectLoading ? 'Disconnessione...' : 'Disconnetti'}
              </button>
            ) : (
              <button
                onClick={handleGoogleConnect}
                disabled={googleConnectLoading}
                className={btnPrimary}
              >
                {googleConnectLoading ? 'Attendere...' : 'Connetti Google Calendar'}
              </button>
            )
          )}
        </div>

        <p className="text-xs text-gray-400 mt-4">
          Connetti il tuo Google Calendar per creare reminder automatici dalle scadenze dei contratti.
        </p>
      </div>
    </div>
  );
};

export default ProfilePage;
