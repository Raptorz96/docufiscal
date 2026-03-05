import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardStats, getUpcomingDeadlines } from '@/services/dashboardService';
import type { DashboardStats, ContrattoScadenza } from '@/types/dashboard';

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

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [deadlines, setDeadlines] = useState<ContrattoScadenza[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, deadlinesData] = await Promise.all([
          getDashboardStats(),
          getUpcomingDeadlines()
        ]);
        setStats(statsData);
        setDeadlines(deadlinesData);
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
      link: '/clienti'
    },
    {
      title: 'Totale Documenti',
      value: stats?.totale_documenti || 0,
      icon: FileTextIcon,
      color: 'bg-green-50 text-green-600',
      link: '/documenti'
    },
    {
      title: 'Da Assegnare',
      value: stats?.documenti_da_assegnare || 0,
      icon: AlertCircleIcon,
      color: 'bg-amber-50 text-amber-600',
      link: '/documenti?unassigned=true',
      urgent: (stats?.documenti_da_assegnare || 0) > 0
    }
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Panoramica Generale</h1>
        <p className="text-gray-500 mt-2">Benvenuto in DocuFiscal. Ecco un riepilogo delle tue attività.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

      {/* Sezione Scadenze Imminenti */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="p-6 border-b border-gray-50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <CalendarIcon className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Scadenze Imminenti (30 giorni)</h2>
          </div>
          <span className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-semibold">
            {deadlines.length} contratti
          </span>
        </div>

        {deadlines.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50/50 text-gray-400 text-[10px] uppercase font-bold tracking-widest">
                  <th className="px-6 py-4">Cliente</th>
                  <th className="px-6 py-4">Tipo Contratto</th>
                  <th className="px-6 py-4">Scadenza</th>
                  <th className="px-6 py-4">Stato</th>
                  <th className="px-6 py-4 text-right">Azioni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {deadlines.map((scadenza) => (
                  <tr key={scadenza.id} className="hover:bg-indigo-50/30 transition-colors group/row">
                    <td className="px-6 py-4">
                      <div className="text-sm font-bold text-gray-900">{scadenza.cliente_nome}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600">{scadenza.tipo_contratto_nome}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 font-medium">
                      {new Date(scadenza.data_scadenza).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${scadenza.giorni_rimanenti < 7
                          ? 'bg-red-100 text-red-700 ring-1 ring-red-200'
                          : 'bg-yellow-100 text-yellow-700 ring-1 ring-yellow-200'
                        }`}>
                        {scadenza.giorni_rimanenti <= 0
                          ? 'Scaduto'
                          : `Tra ${scadenza.giorni_rimanenti} giorni`}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/documenti?cliente_id=${scadenza.cliente_id}`}
                        className="text-indigo-600 hover:text-indigo-800 text-sm font-bold inline-flex items-center group-hover/row:translate-x-1 transition-transform"
                      >
                        Vedi Documenti
                        <ArrowRightIcon className="w-4 h-4 ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="inline-flex items-center justify-center p-4 bg-gray-50 rounded-full mb-4">
              <CalendarIcon className="w-8 h-8 text-gray-300" />
            </div>
            <p className="text-gray-500 font-medium">Nessuna scadenza imminente nei prossimi 30 giorni.</p>
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
