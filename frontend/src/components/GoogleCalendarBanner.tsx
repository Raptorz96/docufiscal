import React, { useEffect, useState } from 'react';
import { getGoogleStatus, getGoogleAuthorizeUrl } from '@/services/googleService';

interface GoogleCalendarBannerProps {
  className?: string;
}

const GoogleCalendarBanner: React.FC<GoogleCalendarBannerProps> = ({ className }) => {
  const [connected, setConnected] = useState<boolean | null>(null); // null = loading

  useEffect(() => {
    getGoogleStatus()
      .then((s) => setConnected(s.connected))
      .catch(() => setConnected(true)); // fail silent: non mostrare banner se errore
  }, []);

  // Non mostrare nulla durante loading o se già connesso
  if (connected !== false) return null;

  const handleConnect = async () => {
    try {
      const url = await getGoogleAuthorizeUrl();
      window.location.href = url;
    } catch {
      // silently ignore
    }
  };

  return (
    <div className={`bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-center gap-4 ${className ?? ''}`}>
      <span className="text-2xl shrink-0" aria-hidden="true">📅</span>
      <p className="text-sm text-blue-800 dark:text-blue-300 flex-1">
        Collega Google Calendar per aggiungere le scadenze direttamente al tuo calendario.
      </p>
      <button
        onClick={handleConnect}
        className="shrink-0 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
      >
        Connetti Google Calendar
      </button>
    </div>
  );
};

export default GoogleCalendarBanner;
