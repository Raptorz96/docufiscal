import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AxiosError } from 'axios';
import { getDocumenti, deleteDocumento, downloadDocumento, classificaDocumento } from '@/services/documentoService';
import {
  TIPO_LABELS,
  TIPO_BADGE_CLASSES,
  MACRO_CATEGORIA_LABELS,
  MACRO_CATEGORIA_BADGE_CLASSES,
  type MacroCategoria,
} from '@/utils/documentoLabels';
import { formatFileSize, formatDate } from '@/utils/formatters';
import { UploadDocumentoModal } from '@/components/UploadDocumentoModal';
import { ClassificazioneModal } from '@/components/ClassificazioneModal';
import { useDocument } from '@/context/DocumentContext';
import type { Documento, TipoDocumento } from '@/types/documento';

type StatoFilter = 'tutti' | 'da_verificare' | 'verificati';

export function DocumentiPage() {
  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Backend filters (trigger API calls)
  const [clienteFilter, setClienteFilter] = useState('');
  const [tipoFilter, setTipoFilter] = useState('');
  const [contrattoFilter, setContrattoFilter] = useState('');
  const [unassignedFilter, setUnassignedFilter] = useState(false);

  // Frontend-only filters (instant, no API call)
  const [searchFilter, setSearchFilter] = useState('');
  const [macroCategoriaFilter, setMacroCategoriaFilter] = useState<MacroCategoria | ''>('');
  const [annoFilter, setAnnoFilter] = useState('');
  const [statoFilter, setStatoFilter] = useState<StatoFilter>('tutti');

  const [filtersOpen, setFiltersOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDocumento, setSelectedDocumento] = useState<Documento | null>(null);
  /** The document currently open in the PDF side-drawer (managed by context). */
  const { viewingDocument, setViewingDocument, clienti, contratti, refreshSupportData } = useDocument();
  const [confirmingId, setConfirmingId] = useState<number | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const clientiMap = useRef<Map<number, string>>(new Map());
  const isInitialMount = useRef(true);
  const toastTimeout = useRef<any>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    if (toastTimeout.current) clearTimeout(toastTimeout.current);
    setToast({ message, type });
    toastTimeout.current = setTimeout(() => setToast(null), 5000);
  }, []);


  const loadDocumenti = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { cliente_id?: number; contratto_id?: number; tipo_documento?: string; unassigned?: boolean } = {};
      if (clienteFilter) params.cliente_id = parseInt(clienteFilter);
      if (contrattoFilter) params.contratto_id = parseInt(contrattoFilter);
      if (tipoFilter) params.tipo_documento = tipoFilter;
      if (unassignedFilter) params.unassigned = true;

      const data = await getDocumenti(params);
      setDocumenti(data);
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail ?? 'Errore nel caricamento dei documenti');
      } else {
        setError('Errore sconosciuto');
      }
    } finally {
      setLoading(false);
    }
  }, [clienteFilter, contrattoFilter, tipoFilter, unassignedFilter]);

  useEffect(() => {
    const isUnassigned = searchParams.get('unassigned') === 'true';
    setUnassignedFilter(isUnassigned);
    const init = async () => {
      await refreshSupportData();
      await loadDocumenti();
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update clientiMap whenever context data changes
  useEffect(() => {
    clientiMap.current = new Map(
      clienti.map((c) => [c.id, `${c.nome} ${c.cognome ?? ''}`.trim()])
    );
  }, [clienti]);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    loadDocumenti();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteFilter, contrattoFilter, tipoFilter, unassignedFilter]);

  useEffect(() => {
    const isUnassigned = searchParams.get('unassigned') === 'true';
    if (isUnassigned !== unassignedFilter) {
      setUnassignedFilter(isUnassigned);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Derive unique years from the loaded documents for the Anno dropdown
  const availableAnni = useMemo(() => {
    const anni = new Set<number>();
    documenti.forEach((doc) => {
      if (doc.anno_competenza) anni.add(doc.anno_competenza);
    });
    return Array.from(anni).sort((a, b) => b - a);
  }, [documenti]);

  // Frontend-only filtering — instant, no API call
  const filteredDocumenti = useMemo(() => {
    return documenti.filter((doc) => {
      // Macro-Categoria
      if (macroCategoriaFilter && doc.macro_categoria !== macroCategoriaFilter) return false;
      // Anno
      if (annoFilter && String(doc.anno_competenza) !== annoFilter) return false;
      // Stato
      if (statoFilter === 'verificati' && !doc.verificato_da_utente) return false;
      if (statoFilter === 'da_verificare' && doc.verificato_da_utente) return false;
      // Search (file_name + note)
      if (searchFilter) {
        const q = searchFilter.toLowerCase();
        const matchName = doc.file_name.toLowerCase().includes(q);
        const matchNote = doc.note?.toLowerCase().includes(q) ?? false;
        if (!matchName && !matchNote) return false;
      }
      return true;
    });
  }, [documenti, macroCategoriaFilter, annoFilter, statoFilter, searchFilter]);

  const handleDelete = async (documento: Documento) => {
    if (!window.confirm(`Eliminare il documento "${documento.file_name}"?`)) return;
    try {
      await deleteDocumento(documento.id);
      await loadDocumenti();
    } catch (err) {
      if (err instanceof AxiosError) {
        alert(err.response?.data?.detail ?? "Errore durante l'eliminazione");
      } else {
        alert("Errore sconosciuto durante l'eliminazione");
      }
    }
  };

  const handleDownload = async (documento: Documento) => {
    try {
      await downloadDocumento(documento.id, documento.file_name);
    } catch (err) {
      if (err instanceof AxiosError) {
        alert(err.response?.data?.detail ?? 'Errore durante il download');
      } else {
        alert('Errore sconosciuto durante il download');
      }
    }
  };

  const handleRetry = async () => {
    await refreshSupportData();
    await loadDocumenti();
  };

  const handleClassificaSuccess = useCallback((updated: Documento) => {
    setDocumenti((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
    setSelectedDocumento(null);
  }, []);


  const handleConfermaInline = useCallback(async (doc: Documento) => {
    setConfirmingId(doc.id);
    try {
      const updated = await classificaDocumento(doc.id, {});
      handleClassificaSuccess(updated);
    } catch {
      alert('Errore durante la conferma. Riprova.');
    } finally {
      setConfirmingId(null);
    }
  }, [handleClassificaSuccess]);

  const resetFrontendFilters = () => {
    setMacroCategoriaFilter('');
    setAnnoFilter('');
    setStatoFilter('tutti');
    setSearchFilter('');
  };

  const hasFrontendFilters = macroCategoriaFilter || annoFilter || statoFilter !== 'tutti' || searchFilter;

  const activeFilterCount = [
    clienteFilter,
    contrattoFilter,
    tipoFilter,
    macroCategoriaFilter,
    annoFilter,
    searchFilter,
    statoFilter !== 'tutti' ? statoFilter : '',
    unassignedFilter ? 'yes' : '',
  ].filter(Boolean).length;

  const getTipoBadge = (tipo: TipoDocumento) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${TIPO_BADGE_CLASSES[tipo]}`}>
      {TIPO_LABELS[tipo]}
    </span>
  );

  const getMacroBadge = (macro?: string | null) => {
    if (!macro) return <span className="text-xs text-gray-400">—</span>;
    const key = macro as MacroCategoria;
    const label = MACRO_CATEGORIA_LABELS[key] ?? macro;
    const classes = MACRO_CATEGORIA_BADGE_CLASSES[key] ?? 'bg-gray-100 text-gray-600 border border-gray-200';
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${classes}`}>
        {label}
      </span>
    );
  };

  const getAiBadge = (doc: Documento) => {
    if (doc.verificato_da_utente) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          ✓ Verificato
        </span>
      );
    }
    if (doc.classificazione_ai === null) {
      return <span className="text-xs text-gray-400">—</span>;
    }
    const label = doc.tipo_documento_raw ?? TIPO_LABELS[doc.tipo_documento];
    const isConfirming = confirmingId === doc.id;
    const spinnerSm = (
      <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
      </svg>
    );

    if (doc.confidence_score !== null && doc.confidence_score >= 0.75) {
      const pct = Math.round(doc.confidence_score * 100);
      return (
        <div className="flex flex-col gap-1">
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            {label} · {pct}%
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => handleConfermaInline(doc)}
              disabled={isConfirming}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isConfirming ? spinnerSm : '✓'} Conferma
            </button>
            <button
              onClick={() => setSelectedDocumento(doc)}
              disabled={isConfirming}
              className="px-2 py-0.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100 disabled:opacity-50"
            >
              Correggi
            </button>
          </div>
        </div>
      );
    }
    const pct = doc.confidence_score !== null ? Math.round(doc.confidence_score * 100) : null;
    return (
      <div className="flex flex-col gap-1">
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          {pct !== null ? `${label} · ${pct}%` : 'Non classificato'}
        </span>
        <div className="flex gap-1">
          <button
            onClick={() => handleConfermaInline(doc)}
            disabled={isConfirming}
            className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isConfirming ? spinnerSm : '✓'} Conferma
          </button>
          <button
            onClick={() => setSelectedDocumento(doc)}
            disabled={isConfirming}
            className="px-2 py-0.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100 disabled:opacity-50"
          >
            Correggi
          </button>
        </div>
      </div>
    );
  };

  const contrattiFiltered = clienteFilter
    ? contratti.filter((c) => c.cliente_id === parseInt(clienteFilter))
    : contratti;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={handleRetry}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  const statoTabs: { key: StatoFilter; label: string }[] = [
    { key: 'tutti', label: 'Tutti' },
    { key: 'da_verificare', label: 'Da Verificare' },
    { key: 'verificati', label: 'Verificati' },
  ];

  const isDrawerOpen = viewingDocument !== null;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      {/* When the drawer is open, we use a flex layout: table on the left, drawer on the right (fixed). */}
      <div
        className={`transition-all duration-300 px-4 sm:px-6 lg:px-8 w-full mx-auto`}
        style={isDrawerOpen ? { marginRight: '45vw', width: 'auto' } : undefined}
      >
        {/* Header */}
        <div className="sm:flex sm:items-center mb-6">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Documenti</h1>
            <p className="mt-1 text-sm text-gray-700">Gestione avanzata dei documenti caricati</p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
            <button
              onClick={() => setIsUploadOpen(true)}
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
            >
              + Carica Documento
            </button>
          </div>
        </div>

        {/* ─── Sticky Filter Panel ──────────────────────────────────────── */}
        <div className="sticky top-0 z-20 bg-white shadow-md rounded-xl border border-gray-200 mb-4">
          {/* Mobile toggle */}
          <button
            type="button"
            onClick={() => setFiltersOpen((v) => !v)}
            className="md:hidden w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <span className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
              </svg>
              Filtri
              {activeFilterCount > 0 && (
                <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-indigo-600 text-white text-xs font-bold">
                  {activeFilterCount}
                </span>
              )}
            </span>
            <svg
              className={`h-4 w-4 text-gray-400 transition-transform ${filtersOpen ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Collapsible filter rows — always visible on md+, toggled on mobile */}
          <div className={`${filtersOpen ? '' : 'hidden'} md:block`}>

          {/* Row 1 – Backend filters (trigger API) */}
          <div className="px-6 pt-4 pb-3 border-b border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Filtri Backend</p>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Cliente</label>
                <select
                  value={clienteFilter}
                  onChange={(e) => {
                    setClienteFilter(e.target.value);
                    setContrattoFilter('');
                  }}
                  disabled={unassignedFilter}
                  className="block w-full rounded-lg border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Tutti i clienti</option>
                  {clienti.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome} {c.cognome ?? ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Tipo Documento</label>
                <select
                  value={tipoFilter}
                  onChange={(e) => setTipoFilter(e.target.value)}
                  className="block w-full rounded-lg border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="">Tutti i tipi</option>
                  {(Object.keys(TIPO_LABELS) as TipoDocumento[]).map((tipo) => (
                    <option key={tipo} value={tipo}>{TIPO_LABELS[tipo]}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Contratto</label>
                <select
                  value={contrattoFilter}
                  onChange={(e) => setContrattoFilter(e.target.value)}
                  disabled={unassignedFilter}
                  className="block w-full rounded-lg border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Tutti i contratti</option>
                  {contrattiFiltered.map((c) => (
                    <option key={c.id} value={c.id}>
                      {`#${c.id} — ${clientiMap.current.get(c.cliente_id) ?? ''} (${c.stato})`}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Row 2 – Frontend filters (instant) */}
          <div className="px-6 py-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Filtri Istantanei</p>
            <div className="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 items-end">
              {/* Search */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Cerca (nome / note)</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400 pointer-events-none">
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    placeholder="Es: fattura.pdf, note..."
                    className="block w-full pl-10 rounded-lg border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Macro-Categoria dropdown */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Macro-Categoria</label>
                <select
                  value={macroCategoriaFilter}
                  onChange={(e) => setMacroCategoriaFilter(e.target.value as MacroCategoria | '')}
                  className="block w-full rounded-lg border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="">Tutte le categorie</option>
                  {(Object.keys(MACRO_CATEGORIA_LABELS) as MacroCategoria[]).map((key) => (
                    <option key={key} value={key}>{MACRO_CATEGORIA_LABELS[key]}</option>
                  ))}
                </select>
              </div>

              {/* Anno dropdown */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Anno</label>
                <select
                  value={annoFilter}
                  onChange={(e) => setAnnoFilter(e.target.value)}
                  className="block w-full rounded-lg border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="">Tutti gli anni</option>
                  {availableAnni.map((a) => (
                    <option key={a} value={String(a)}>{a}</option>
                  ))}
                </select>
              </div>

              {/* Da assegnare toggle */}
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={() => {
                    const newVal = !unassignedFilter;
                    setUnassignedFilter(newVal);
                    if (newVal) {
                      setSearchParams({ unassigned: 'true' });
                      setClienteFilter('');
                      setContrattoFilter('');
                    } else {
                      searchParams.delete('unassigned');
                      setSearchParams(searchParams);
                    }
                  }}
                  className={`w-full inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium transition-all border-2 ${unassignedFilter
                    ? 'bg-amber-50 text-amber-700 border-amber-300 shadow-sm'
                    : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                    }`}
                >
                  <span className={`w-2 h-2 rounded-full mr-2 flex-shrink-0 ${unassignedFilter ? 'bg-amber-500 animate-pulse' : 'bg-gray-400'}`} />
                  {unassignedFilter ? 'Da Assegnare ✓' : 'Da Assegnare'}
                </button>
              </div>
            </div>

            {/* Stato tabs */}
            <div className="mt-4 flex items-center gap-2">
              <span className="text-xs font-medium text-gray-500 mr-1">Stato:</span>
              {statoTabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setStatoFilter(tab.key)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${statoFilter === tab.key
                    ? tab.key === 'tutti'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : tab.key === 'verificati'
                        ? 'bg-green-600 text-white shadow-sm'
                        : 'bg-yellow-500 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          </div>{/* end collapsible */}

          {/* Results counter + clear */}
          <div className="px-6 py-2 bg-gray-50 rounded-b-xl border-t border-gray-100 flex items-center justify-between">
            <p className="text-xs text-gray-500">
              <span className="font-semibold text-gray-700">{filteredDocumenti.length}</span>{' '}
              {filteredDocumenti.length === 1 ? 'documento trovato' : 'documenti trovati'}
              {documenti.length !== filteredDocumenti.length && (
                <span className="ml-1 text-gray-400">(su {documenti.length} totali)</span>
              )}
            </p>
            {hasFrontendFilters && (
              <button
                onClick={resetFrontendFilters}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium underline underline-offset-2 transition-colors"
              >
                Azzera filtri istantanei
              </button>
            )}
          </div>
        </div>
        {/* ──────────────────────────────────────────────────────────────── */}

        {/* Table */}
        <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-hidden">
          {filteredDocumenti.length === 0 ? (
            <div className="text-center py-16">
              <svg className="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="mt-3 text-sm text-gray-500 font-medium">Nessun documento corrisponde ai filtri applicati</p>
              {hasFrontendFilters && (
                <button onClick={resetFrontendFilters} className="mt-2 text-xs text-indigo-600 hover:underline">
                  Azzera filtri istantanei
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Nome file</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Tipo Documento</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Macro-Categoria</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Anno</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Classificazione AI</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Cliente</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Dimensione</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Data</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Azioni</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {filteredDocumenti.map((doc) => {
                    const isUnassigned = doc.cliente_id === null;
                    return (
                      <tr
                        key={doc.id}
                        className={`${isUnassigned ? 'bg-red-50/40 hover:bg-red-50' : 'hover:bg-gray-50/60'} transition-colors`}
                      >
                        {/* Nome file – click to open PDF drawer */}
                        <td className="px-5 py-4 text-sm font-medium text-gray-900 max-w-xs" title={doc.file_name}>
                          <button
                            onClick={() => setViewingDocument(doc)}
                            className={`text-left truncate block w-full hover:text-indigo-600 transition-colors ${viewingDocument?.id === doc.id ? 'text-indigo-600 font-semibold' : ''
                              }`}
                          >
                            {doc.file_name}
                          </button>
                          {doc.note && (
                            <p className="text-xs text-gray-400 mt-0.5 truncate font-normal" title={doc.note}>{doc.note}</p>
                          )}
                        </td>

                        {/* Tipo */}
                        <td className="px-5 py-4 whitespace-nowrap">
                          {getTipoBadge(doc.tipo_documento)}
                        </td>

                        {/* Macro-Categoria badge (NEW separate column) */}
                        <td className="px-5 py-4 whitespace-nowrap">
                          {getMacroBadge(doc.macro_categoria)}
                        </td>

                        {/* Anno (NEW separate column) */}
                        <td className="px-5 py-4 whitespace-nowrap text-sm font-semibold text-gray-700">
                          {doc.anno_competenza ?? <span className="text-gray-400 font-normal">—</span>}
                        </td>

                        {/* AI */}
                        <td className="px-5 py-4">
                          {getAiBadge(doc)}
                        </td>

                        {/* Cliente */}
                        <td className="px-5 py-4 whitespace-nowrap">
                          {isUnassigned ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
                              Da Assegnare
                            </span>
                          ) : (
                            <span className="text-sm text-gray-700 font-medium">
                              {clientiMap.current.get(doc.cliente_id!) ?? '—'}
                            </span>
                          )}
                        </td>

                        {/* Dimensione */}
                        <td className="px-5 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatFileSize(doc.file_size)}
                        </td>

                        {/* Data */}
                        <td className="px-5 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(doc.created_at)}
                        </td>

                        {/* Azioni */}
                        <td className="px-5 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => setSelectedDocumento(doc)}
                              className="inline-flex items-center gap-1 text-amber-600 hover:text-amber-800 transition-colors"
                              title="Modifica Classificazione"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              <span>Modifica</span>
                            </button>
                            <button
                              onClick={() => handleDownload(doc)}
                              className="text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
                            >
                              Download
                            </button>
                            <button
                              onClick={() => handleDelete(doc)}
                              className="text-red-500 hover:text-red-700 font-medium transition-colors"
                            >
                              Elimina
                            </button>
                          </div>
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

      <UploadDocumentoModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={(doc) => {
          setIsUploadOpen(false);
          loadDocumenti();
          const clienteName = clientiMap.current.get(doc.cliente_id) || `ID ${doc.cliente_id}`;
          showToast(`Documento caricato con successo ed associato a: ${clienteName}`);
        }}
      />

      {selectedDocumento !== null && (
        <ClassificazioneModal
          documento={selectedDocumento}
          clienti={clienti}
          contratti={contratti}
          onClose={() => setSelectedDocumento(null)}
          onSuccess={handleClassificaSuccess}
        />
      )}

      {/* selectedDocumento remains local for now */}

      {toast && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className={`rounded-xl px-4 py-3 shadow-xl flex items-center gap-3 ${toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
            {toast.type === 'success' ? (
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            <span className="text-sm font-medium">{toast.message}</span>
            <button
              onClick={() => setToast(null)}
              className="ml-auto p-1 hover:bg-white/20 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
