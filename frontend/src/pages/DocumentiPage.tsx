import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AxiosError } from 'axios';
import { getDocumenti, deleteDocumento, downloadDocumento, classificaDocumento } from '@/services/documentoService';
import { getClienti } from '@/services/clientiService';
import { getContratti } from '@/services/contrattiService';
import { TIPO_LABELS, TIPO_BADGE_CLASSES } from '@/utils/documentoLabels';
import { formatFileSize, formatDate } from '@/utils/formatters';
import { UploadDocumentoModal } from '@/components/UploadDocumentoModal';
import { ClassificazioneModal } from '@/components/ClassificazioneModal';
import type { Documento, TipoDocumento } from '@/types/documento';
import type { Cliente } from '@/types/cliente';
import type { Contratto } from '@/types/contratto';

export function DocumentiPage() {
  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [clienti, setClienti] = useState<Cliente[]>([]);
  const [contratti, setContratti] = useState<Contratto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clienteFilter, setClienteFilter] = useState('');
  const [tipoFilter, setTipoFilter] = useState('');
  const [contrattoFilter, setContrattoFilter] = useState('');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDocumento, setSelectedDocumento] = useState<Documento | null>(null);
  const [confirmingId, setConfirmingId] = useState<number | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchFilter, setSearchFilter] = useState('');
  const [unassignedFilter, setUnassignedFilter] = useState(searchParams.get('unassigned') === 'true');

  const clientiMap = useRef<Map<number, string>>(new Map());
  const contrattiMap = useRef<Map<number, string>>(new Map());
  const isInitialMount = useRef(true);
  const toastTimeout = useRef<any>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    if (toastTimeout.current) clearTimeout(toastTimeout.current);
    setToast({ message, type });
    toastTimeout.current = setTimeout(() => setToast(null), 5000);
  }, []);

  const loadSupportData = useCallback(async () => {
    try {
      const [clientiData, contrattiData] = await Promise.all([
        getClienti(),
        getContratti(),
      ]);
      setClienti(clientiData);
      setContratti(contrattiData);
      clientiMap.current = new Map(
        clientiData.map((c) => [c.id, `${c.nome} ${c.cognome ?? ''}`.trim()])
      );
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail ?? 'Errore nel caricamento dei dati');
      } else {
        setError('Errore sconosciuto');
      }
    }
  }, []);

  const loadDocumenti = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { cliente_id?: number; contratto_id?: number; tipo_documento?: string; search?: string; unassigned?: boolean } = {};
      if (clienteFilter) params.cliente_id = parseInt(clienteFilter);
      if (contrattoFilter) params.contratto_id = parseInt(contrattoFilter);
      if (tipoFilter) params.tipo_documento = tipoFilter;
      if (searchFilter) params.search = searchFilter;
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
  }, [clienteFilter, contrattoFilter, tipoFilter, searchFilter, unassignedFilter]);

  useEffect(() => {
    const init = async () => {
      await loadSupportData();
      await loadDocumenti();
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    loadDocumenti();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteFilter, contrattoFilter, tipoFilter, searchFilter, unassignedFilter]);

  // Synchronize unassigned from URL if it changes
  useEffect(() => {
    const isUnassigned = searchParams.get('unassigned') === 'true';
    if (isUnassigned !== unassignedFilter) {
      setUnassignedFilter(isUnassigned);
    }
  }, [searchParams]);

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
    await loadSupportData();
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

  const getTipoBadge = (tipo: TipoDocumento) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${TIPO_BADGE_CLASSES[tipo]}`}>
      {TIPO_LABELS[tipo]}
    </span>
  );

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

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Documenti</h1>
            <p className="mt-2 text-sm text-gray-700">Gestione documenti caricati</p>
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

        <div className="mt-6 bg-white shadow-sm rounded-lg overflow-hidden">
          {/* Filtri */}
          <div className="px-6 py-4 border-b border-gray-200 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
                <select
                  value={clienteFilter}
                  onChange={(e) => {
                    setClienteFilter(e.target.value);
                    setContrattoFilter('');
                  }}
                  disabled={unassignedFilter}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Tutti</option>
                  {clienti.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome} {c.cognome ?? ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Documento</label>
                <select
                  value={tipoFilter}
                  onChange={(e) => setTipoFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="">Tutti</option>
                  {(Object.keys(TIPO_LABELS) as TipoDocumento[]).map((tipo) => (
                    <option key={tipo} value={tipo}>{TIPO_LABELS[tipo]}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contratto</label>
                <select
                  value={contrattoFilter}
                  onChange={(e) => setContrattoFilter(e.target.value)}
                  disabled={unassignedFilter}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Tutti</option>
                  {contrattiFiltered.map((c) => (
                    <option key={c.id} value={c.id}>
                      {`#${c.id} — ${clientiMap.current.get(c.cliente_id) ?? ''} (${c.stato})`}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cerca nel nome file</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    placeholder="Es: fattura.pdf..."
                    className="block w-full pl-10 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>
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
                  className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors border-2 ${unassignedFilter
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                    }`}
                >
                  <span className={`w-2 h-2 rounded-full mr-2 ${unassignedFilter ? 'bg-amber-500 animate-pulse' : 'bg-gray-400'}`}></span>
                  {unassignedFilter ? 'Mostrando: Da Assegnare' : 'Filtra: Da Assegnare'}
                </button>
              </div>
            </div>
          </div>

          {/* Tabella */}
          {documenti.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Nessun documento trovato</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome file</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo Documento</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Classificazione AI</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dimensione</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {documenti.map((doc) => {
                    const isUnassigned = doc.cliente_id === null;
                    return (
                      <tr key={doc.id} className={`${isUnassigned ? 'bg-red-50/50 hover:bg-red-50' : 'hover:bg-gray-50'} transition-colors`}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {doc.file_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getTipoBadge(doc.tipo_documento)}
                        </td>
                        <td className="px-6 py-4">
                          {getAiBadge(doc)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {isUnassigned ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
                              Da Assegnare
                            </span>
                          ) : (
                            <span className="text-sm text-gray-600 font-medium">
                              {clientiMap.current.get(doc.cliente_id!) ?? '—'}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatFileSize(doc.file_size)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(doc.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center space-x-4">
                            <button
                              onClick={() => setSelectedDocumento(doc)}
                              className="inline-flex items-center text-amber-600 hover:text-amber-900 group"
                              title="Modifica Classificazione"
                            >
                              <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              <span>Modifica</span>
                            </button>
                            <button
                              onClick={() => handleDownload(doc)}
                              className="text-indigo-600 hover:text-indigo-900 font-medium"
                            >
                              Download
                            </button>
                            <button
                              onClick={() => handleDelete(doc)}
                              className="text-red-500 hover:text-red-700 font-medium"
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

      {toast && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className={`rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 ${toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
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
              className="ml-auto p-1 hover:bg-white/20 rounded transition-colors"
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
