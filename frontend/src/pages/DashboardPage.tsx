import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getDashboardStats } from '@/services/dashboardService';
import type { DashboardStats, ScadenzaDashboard } from '@/types/dashboard';

// Inline SVG components to replace lucide-react dependency
const UsersIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
);

const FileTextIcon = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" /></svg>
);

const AlertCircleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
);

const ArrowRightIcon = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg>
);

const CalendarIcon = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><rect width="18" height="18" x="3" y="4" rx="2" ry="2" /><line x1="16" x2="16" y1="2" y2="6" /><line x1="8" x2="8" y1="2" y2="6" /><line x1="3" x2="21" y1="10" y2="10" /></svg>
);

const BriefcaseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="14" x="2" y="7" rx="2" ry="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /></svg>
);

const SparklesIcon = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" /></svg>
);

function scadenzaBadgeStyle(giorni: number | null): string {
  if (giorni === null) return 'bg-gray-100 text-gray-600';
  if (giorni < 0) return 'bg-red-100 text-red-700 ring-1 ring-red-200';
  if (giorni < 7) return 'bg-orange-100 text-orange-700 ring-1 ring-orange-200';
  return 'bg-yellow-100 text-yellow-700 ring-1 ring-yellow-200';
}

function scadenzaBadgeLabel(giorni: number | null): string {
  if (giorni === null) return 'Data sconosciuta';
  if (giorni < 0) return `Scaduto da ${Math.abs(giorni)} gg`;
  if (giorni === 0) return 'Scade oggi';
  return `Tra ${giorni} giorni`;
}

function ScadenzaCard({ s }: { s: ScadenzaDashboard }) {
  const navigate = useNavigate();
  const giorni = s.giorni_rimanenti;

  const borderColor =
    giorni === null ? 'border-gray-100'
    : giorni < 0 ? 'border-red-200'
    : giorni < 7 ? 'border-orange-200'
    : 'border-yellow-200';

  return (
    <div
      onClick={() => navigate(`/documenti?cliente_id=${s.cliente_id}`)}
      className={`bg-white rounded-xl border ${borderColor} p-4 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer flex flex-col gap-3`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-bold text-gray-900 truncate">{s.cliente_nome}</p>
          <p className="text-xs text-gray-400 truncate mt-0.5" title={s.file_name}>
            {s.file_name.length > 40 ? s.file_name.slice(0, 40) + '…' : s.file_name}
          </p>
        </div>
        {!s.verificato && (
          <span className="shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-600 ring-1 ring-amber-200">
            Non verificato
          </span>
        )}
      </div>

      {/* Data scadenza + badge giorni */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-sm text-gray-500">
          <CalendarIcon className="w-4 h-4 shrink-0" />
          {s.data_scadenza
            ? new Date(s.data_scadenza).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
            : '—'}
        </div>
        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${scadenzaBadgeStyle(giorni)}`}>
          {scadenzaBadgeLabel(giorni)}
        </span>
      </div>

      {/* Canone */}
      {s.canone && (
        <div className="text-xs text-gray-600">
          <span className="font-semibold text-gray-700">Canone:</span> {s.canone}
        </div>
      )}

      {/* Rinnovo automatico */}
      {s.rinnovo_automatico !== null && s.rinnovo_automatico !== undefined && (
        <div>
          {s.rinnovo_automatico ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-50 text-green-700 ring-1 ring-green-200">
              Rinnovo auto
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-500">
              No rinnovo
            </span>
          )}
        </div>
      )}

      {/* Preavviso disdetta */}
      {s.preavviso_disdetta && (
        <p className="text-xs text-gray-400 leading-snug">
          <span className="font-medium text-gray-500">Preavviso:</span> {s.preavviso_disdetta}
        </p>
      )}
    </div>
  );
}

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsData = await getDashboardStats();
        setStats(statsData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const cards = [
    {
      title: 'Totale Clienti',
      value: stats?.totale_clienti || 0,
      icon: UsersIcon,
      color: 'bg-blue-50 text-blue-600',
      link: '/clienti',
    },
    {
      title: 'Totale Documenti',
      value: stats?.totale_documenti || 0,
      icon: FileTextIcon,
      color: 'bg-green-50 text-green-600',
      link: '/documenti',
    },
    {
      title: 'Contratti Attivi',
      value: stats?.totale_contratti_attivi || 0,
      icon: BriefcaseIcon,
      color: 'bg-indigo-50 text-indigo-600',
      link: '/contratti',
    },
    {
      title: 'Da Verificare',
      value: stats?.documenti_da_verificare || 0,
      icon: AlertCircleIcon,
      color: 'bg-amber-50 text-amber-600',
      link: '/documenti?da_verificare=true',
      urgent: (stats?.documenti_da_verificare || 0) > 0,
    },
  ];

  const critiche = stats?.scadenze_critiche ?? [];
  const ultimi = stats?.ultimi_documenti ?? [];
  const scaduteCount = stats?.scadenze_scadute ?? 0;
  const inScadenzaCount = stats?.scadenze_in_scadenza ?? 0;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Panoramica Generale</h1>
        <p className="text-gray-500 mt-2">Benvenuto in DocuFiscal. Ecco un riepilogo delle tue attività.</p>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {cards.map((card) => (
          <div
            key={card.title}
            className={`relative group bg-white rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition-all duration-300 ${card.urgent ? 'ring-1 ring-amber-200' : ''}`}
          >
            <div className="flex items-start justify-between">
              <div className={`p-3 rounded-xl ${card.color}`}>
                <card.icon />
              </div>
              {card.urgent && (
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                </span>
              )}
            </div>

            <div className="mt-4">
              <p className="text-sm font-medium text-gray-500">{card.title}</p>
              <h2 className="text-4xl font-bold text-gray-900 mt-1">{card.value}</h2>
            </div>

            <Link
              to={card.link}
              className="mt-6 flex items-center text-sm font-semibold text-indigo-600 group-hover:text-indigo-700 transition-colors"
            >
              Vedi dettagli
              <ArrowRightIcon className="w-4 h-4 ml-1 transform group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        ))}
      </div>

      {/* Sezione Scadenze Contratti (AI) */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <CalendarIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Scadenze Contratti (AI)</h2>
              <p className="text-xs text-gray-400 mt-0.5">Estratte automaticamente dai PDF caricati</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {scaduteCount > 0 && (
              <span className="px-2.5 py-1 bg-red-50 text-red-700 rounded-full text-xs font-semibold ring-1 ring-red-200">
                {scaduteCount} scadut{scaduteCount === 1 ? 'a' : 'e'}
              </span>
            )}
            {inScadenzaCount > 0 && (
              <span className="px-2.5 py-1 bg-yellow-50 text-yellow-700 rounded-full text-xs font-semibold ring-1 ring-yellow-200">
                {inScadenzaCount} in scadenza
              </span>
            )}
            {scaduteCount === 0 && inScadenzaCount === 0 && (
              <span className="px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs font-semibold">
                Nessuna critica
              </span>
            )}
          </div>
        </div>

        {critiche.length > 0 ? (
          <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {critiche.map((s) => (
              <ScadenzaCard key={s.id} s={s} />
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="inline-flex items-center justify-center p-4 bg-gray-50 rounded-full mb-4">
              <SparklesIcon className="w-8 h-8 text-gray-300" />
            </div>
            <p className="text-gray-500 font-medium">Nessuna scadenza rilevata.</p>
            <p className="text-gray-400 text-sm mt-1">Le scadenze vengono estratte automaticamente dai PDF contratto caricati.</p>
          </div>
        )}
      </div>

      {/* Sezione Ultimi Documenti */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-50 text-green-600 rounded-lg">
              <FileTextIcon className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Ultimi Documenti Caricati</h2>
          </div>
          <Link
            to="/documenti"
            className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 inline-flex items-center"
          >
            Vedi tutti
            <ArrowRightIcon className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {ultimi.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50/50 text-gray-400 text-[10px] uppercase font-bold tracking-widest">
                  <th className="px-6 py-4">File</th>
                  <th className="px-6 py-4">Tipo</th>
                  <th className="px-6 py-4">Cliente</th>
                  <th className="px-6 py-4">Data</th>
                  <th className="px-6 py-4">Stato</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {ultimi.map((doc) => (
                  <tr key={doc.id} className="hover:bg-green-50/20 transition-colors">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 max-w-xs truncate">{doc.file_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600">{doc.tipo_documento}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600">{doc.cliente_nome}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(doc.created_at).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })}
                    </td>
                    <td className="px-6 py-4">
                      {doc.verificato_da_utente ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-green-100 text-green-700">
                          Verificato
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-700">
                          Da verificare
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="inline-flex items-center justify-center p-4 bg-gray-50 rounded-full mb-4">
              <FileTextIcon className="w-8 h-8 text-gray-300" />
            </div>
            <p className="text-gray-500 font-medium">Nessun documento caricato.</p>
          </div>
        )}
      </div>

      <div className="bg-indigo-600 rounded-3xl p-8 text-white relative overflow-hidden shadow-2xl">
        <div className="relative z-10 max-w-lg">
          <h3 className="text-2xl font-bold mb-2">Nuova Funzionalità: Auto-Matching AI</h3>
          <p className="text-indigo-100 mb-6">
            Ora puoi caricare i documenti senza selezionare un cliente. Il nostro motore AI estrarrà automaticamente il Codice Fiscale o la Partita IVA per te.
          </p>
          <Link
            to="/documenti"
            className="inline-flex items-center px-6 py-3 bg-white text-indigo-600 rounded-xl font-bold hover:bg-indigo-50 transition-colors shadow-lg"
          >
            Prova l'upload veloce
          </Link>
        </div>
        <div className="absolute top-0 right-0 -mr-16 -mt-16 opacity-10">
          <FileTextIcon className="w-96 h-96 transform -rotate-12" />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
