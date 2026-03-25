import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getScadenze } from '../services/scadenzeService';
import type { Scadenza, ScadenzaFilters } from '../types/scadenza';

const TIPO_OPTIONS = [
    { value: '', label: 'Tutti i tipi' },
    { value: 'pagamento', label: 'Pagamento' },
    { value: 'incasso', label: 'Incasso' },
    { value: 'canone', label: 'Canone' },
    { value: 'adempimento', label: 'Adempimento' },
    { value: 'rinnovo', label: 'Rinnovo' },
    { value: 'generico', label: 'Generico' },
];

function tipoBadge(tipo: string): { label: string; className: string } {
    switch (tipo) {
        case 'pagamento': return { label: 'Pagamento', className: 'bg-red-100 text-red-700' };
        case 'incasso': return { label: 'Incasso', className: 'bg-green-100 text-green-700' };
        case 'canone':
        case 'contratto': return { label: 'Canone', className: 'bg-blue-100 text-blue-700' };
        case 'adempimento': return { label: 'Adempimento', className: 'bg-purple-100 text-purple-700' };
        case 'rinnovo': return { label: 'Rinnovo', className: 'bg-orange-100 text-orange-700' };
        default: return { label: 'Scadenza', className: 'bg-gray-100 text-gray-600' };
    }
}

function urgenzaRowClass(giorni: number | null): string {
    if (giorni === null) return '';
    if (giorni < 0) return 'bg-red-50';
    if (giorni < 7) return 'bg-orange-50';
    if (giorni < 30) return 'bg-yellow-50/50';
    return '';
}

function giorniLabel(giorni: number | null): string {
    if (giorni === null) return '—';
    if (giorni < 0) return `Scaduto da ${Math.abs(giorni)} gg`;
    if (giorni === 0) return 'Oggi';
    return `${giorni} gg`;
}

function giorniColor(giorni: number | null): string {
    if (giorni === null) return 'text-gray-400';
    if (giorni < 0) return 'text-red-600 font-semibold';
    if (giorni < 7) return 'text-orange-600 font-semibold';
    return 'text-gray-500';
}

const ScadenzePage: React.FC = () => {
    const navigate = useNavigate();
    const [scadenze, setScadenze] = useState<Scadenza[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [tipoFilter, setTipoFilter] = useState('');
    const [soloNonVerificati, setSoloNonVerificati] = useState(false);

    const fetchScadenze = useCallback(async () => {
        setLoading(true);
        try {
            const activeFilters: ScadenzaFilters = {};
            if (tipoFilter) activeFilters.tipo_scadenza = tipoFilter;
            if (soloNonVerificati) activeFilters.verificato = false;
            if (search) activeFilters.search = search;
            const data = await getScadenze(activeFilters);
            setScadenze(data);
        } catch (err) {
            console.error('Errore caricamento scadenze:', err);
        } finally {
            setLoading(false);
        }
    }, [tipoFilter, soloNonVerificati, search]);

    useEffect(() => {
        fetchScadenze();
    }, [fetchScadenze]);

    return (
        <div className="p-8 space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Scadenze</h1>
                <p className="text-gray-500 mt-1">
                    {scadenze.length} scadenz{scadenze.length === 1 ? 'a' : 'e'} totali
                </p>
            </div>

            {/* Barra filtri */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex flex-wrap gap-3 items-center">
                <input
                    type="text"
                    placeholder="Cerca cliente o descrizione..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm flex-1 min-w-[200px] focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
                <select
                    value={tipoFilter}
                    onChange={(e) => setTipoFilter(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                    {TIPO_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                </select>
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
                    <input
                        type="checkbox"
                        checked={soloNonVerificati}
                        onChange={(e) => setSoloNonVerificati(e.target.checked)}
                        className="rounded"
                    />
                    Solo non verificate
                </label>
            </div>

            {/* Tabella */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center p-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                    </div>
                ) : scadenze.length === 0 ? (
                    <div className="p-12 text-center text-gray-500">
                        <p className="font-medium">Nessuna scadenza trovata.</p>
                        <p className="text-sm mt-1">Prova a modificare i filtri.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50/50 text-gray-400 text-[10px] uppercase font-bold tracking-widest">
                                    <th className="px-5 py-4">Cliente</th>
                                    <th className="px-5 py-4">Tipo</th>
                                    <th className="px-5 py-4">Descrizione</th>
                                    <th className="px-5 py-4">Data Scadenza</th>
                                    <th className="px-5 py-4">Giorni</th>
                                    <th className="px-5 py-4">Importo</th>
                                    <th className="px-5 py-4">Stato</th>
                                    <th className="px-5 py-4">Documento</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {scadenze.map((s) => {
                                    const badge = tipoBadge(s.tipo_scadenza);
                                    return (
                                        <tr
                                            key={s.id}
                                            className={`hover:bg-gray-50/50 transition-colors cursor-pointer ${urgenzaRowClass(s.giorni_rimanenti)}`}
                                            onClick={() => navigate(`/documenti?cliente_id=${s.cliente_id}`)}
                                        >
                                            <td className="px-5 py-3 text-sm font-medium text-gray-900">{s.cliente_nome}</td>
                                            <td className="px-5 py-3">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${badge.className}`}>
                                                    {badge.label}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 text-sm text-gray-600 max-w-xs truncate">{s.descrizione || '—'}</td>
                                            <td className="px-5 py-3 text-sm text-gray-600">
                                                {s.data_scadenza
                                                    ? new Date(s.data_scadenza).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
                                                    : '—'}
                                            </td>
                                            <td className="px-5 py-3">
                                                <span className={`text-xs ${giorniColor(s.giorni_rimanenti)}`}>
                                                    {giorniLabel(s.giorni_rimanenti)}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 text-sm text-gray-600">{s.canone || '—'}</td>
                                            <td className="px-5 py-3">
                                                {s.verificato ? (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-50 text-green-700">
                                                        Verificata
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-600">
                                                        Non verificata
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-5 py-3 text-xs text-gray-400 max-w-[150px] truncate" title={s.file_name}>
                                                {s.file_name}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ScadenzePage;
