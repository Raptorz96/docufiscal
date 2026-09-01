import { useState, useEffect, useRef, useCallback } from 'react';
import { AxiosError } from 'axios';
import { getContratti, deleteContratto, bulkDeleteContratti } from '@/services/contrattiService';
import { getClienti } from '@/services/clientiService';
import { getTipiContratto } from '@/services/tipiContrattoService';
import { getContrattiDocumenti } from '@/services/documentoService';
import type { Contratto } from '@/types/contratto';
import type { Cliente } from '@/types/cliente';
import type { TipoContratto } from '@/types/tipoContratto';
import type { Documento } from '@/types/documento';
import { ContrattoFormModal } from '@/components/ContrattoFormModal';
import { UploadDocumentoModal } from '@/components/UploadDocumentoModal';

export function ContrattiPage() {
  const [contratti, setContratti] = useState<Contratto[]>([]);
  const [clienti, setClienti] = useState<Cliente[]>([]);
  const [tipiContratto, setTipiContratto] = useState<TipoContratto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clienteFilter, setClienteFilter] = useState<string>('');
  const [tipoContrattoFilter, setTipoContrattoFilter] = useState<string>('');
  const [statoFilter, setStatoFilter] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingContratto, setEditingContratto] = useState<Contratto | undefined>(undefined);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [contrattiDocumenti, setContrattiDocumenti] = useState<Documento[]>([]);
  const [uploadBanner, setUploadBanner] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkConfirmOpen, setBulkConfirmOpen] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const toastTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Maps per lookup nomi
  const clientiMap = useRef<Map<number, string>>(new Map());
  const tipiContrattoMap = useRef<Map<number, string>>(new Map());
  const isInitialMount = useRef(true);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    if (toastTimeout.current) clearTimeout(toastTimeout.current);
    setToast({ message, type });
    toastTimeout.current = setTimeout(() => setToast(null), 5000);
  }, []);

  const loadSupportData = useCallback(async () => {
    try {
      const [clientiData, tipiContrattoData] = await Promise.all([
        getClienti(),
        getTipiContratto()
      ]);

      setClienti(clientiData);
      setTipiContratto(tipiContrattoData);

      // Crea maps per lookup
      clientiMap.current = new Map(
        clientiData.map(cliente => [
          cliente.id,
          `${cliente.nome} ${cliente.cognome || ''}`.trim()
        ])
      );

      tipiContrattoMap.current = new Map(
        tipiContrattoData.map(tipo => [tipo.id, tipo.nome])
      );
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail || 'Errore nel caricamento dei dati di supporto');
      } else {
        setError('Errore sconosciuto');
      }
    }
  }, []);

  const loadContrattiDocumenti = useCallback(async () => {
    try {
      const data = await getContrattiDocumenti();
      setContrattiDocumenti(data);
    } catch {
      // non-critical, silently ignore
    }
  }, []);

  const loadContratti = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { cliente_id?: number; tipo_contratto_id?: number; stato?: string } = {};
      if (clienteFilter) params.cliente_id = parseInt(clienteFilter);
      if (tipoContrattoFilter) params.tipo_contratto_id = parseInt(tipoContrattoFilter);
      if (statoFilter) params.stato = statoFilter;

      const data = await getContratti(params);
      setContratti(data);
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail || 'Errore nel caricamento dei contratti');
      } else {
        setError('Errore sconosciuto');
      }
    } finally {
      setLoading(false);
    }
  }, [clienteFilter, tipoContrattoFilter, statoFilter]);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;

      const initializeData = async () => {
        await loadSupportData();
        await Promise.all([loadContratti(), loadContrattiDocumenti()]);
      };
      initializeData();
      return;
    }

    loadContratti();
    setSelectedIds(new Set());
  }, [loadSupportData, loadContratti, loadContrattiDocumenti]);

  const allSelected = contratti.length > 0 && contratti.every((c) => selectedIds.has(c.id));
  const someSelected = contratti.some((c) => selectedIds.has(c.id)) && !allSelected;

  const toggleAllSelection = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(contratti.map((c) => c.id)));
    }
  };

  const handleBulkDelete = async () => {
    setBulkDeleting(true);
    try {
      const result = await bulkDeleteContratti(Array.from(selectedIds));
      setBulkConfirmOpen(false);
      setSelectedIds(new Set());
      await loadContratti();
      const msg = result.failed.length > 0
        ? `${result.deleted} eliminati, ${result.failed.length} falliti`
        : `${result.deleted} eliminati con successo`;
      showToast(msg, result.failed.length > 0 ? 'error' : 'success');
    } catch {
      showToast("Errore durante l'eliminazione in massa", 'error');
    } finally {
      setBulkDeleting(false);
    }
  };

  const handleDelete = async (contratto: Contratto) => {
    const clienteNome = clientiMap.current.get(contratto.cliente_id) || 'Cliente sconosciuto';
    if (!window.confirm(`Sei sicuro di voler eliminare il contratto per "${clienteNome}"?`)) {
      return;
    }

    try {
      await deleteContratto(contratto.id);
      await loadContratti();
    } catch (err) {
      if (err instanceof AxiosError) {
        alert(err.response?.data?.detail || 'Errore durante l\'eliminazione');
      } else {
        alert('Errore sconosciuto durante l\'eliminazione');
      }
    }
  };

  const handleCreateClick = () => {
    setEditingContratto(undefined);
    setIsModalOpen(true);
  };

  const handleEditClick = (contratto: Contratto) => {
    setEditingContratto(contratto);
    setIsModalOpen(true);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    loadContratti();
  };

  const handleUploadSuccess = (doc: Documento) => {
    setIsUploadOpen(false);
    setUploadBanner(`"${doc.file_name}" caricato con successo e in elaborazione AI.`);
    loadContrattiDocumenti();
    setTimeout(() => setUploadBanner(null), 5000);
  };

  const handleRetry = async () => {
    await loadSupportData();
    await loadContratti();
  };

  const getStatoBadge = (stato: string) => {
    if (stato === 'attivo') {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Attivo</span>;
    } else if (stato === 'sospeso') {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Sospeso</span>;
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Scaduto</span>;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {uploadBanner && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md text-sm text-green-800 dark:text-green-300">
            {uploadBanner}
          </div>
        )}

        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Contratti</h1>
            <p className="mt-2 text-sm text-gray-700 dark:text-gray-400">Gestione dei contratti</p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none flex gap-2">
            <button
              onClick={() => setIsUploadOpen(true)}
              className="inline-flex items-center justify-center rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 shadow-sm hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
            >
              Carica Contratto PDF
            </button>
            <button
              onClick={handleCreateClick}
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
            >
              + Nuovo Contratto
            </button>
          </div>
        </div>

        {selectedIds.size > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-3 px-4 py-2.5 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl">
            <span className="text-sm font-medium text-indigo-700 dark:text-indigo-300">
              {selectedIds.size} {selectedIds.size === 1 ? 'selezionato' : 'selezionati'}
            </span>
            <button
              onClick={() => setBulkConfirmOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Elimina selezionati
            </button>
            <button
              onClick={() => setSelectedIds(new Set())}
              className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            >
              Annulla selezione
            </button>
          </div>
        )}

        <div className="mt-6 bg-white dark:bg-gray-800 shadow-sm rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cliente</label>
                <select
                  value={clienteFilter}
                  onChange={(e) => setClienteFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="">Tutti</option>
                  {clienti.map((cliente) => (
                    <option key={cliente.id} value={cliente.id}>
                      {cliente.nome} {cliente.cognome || ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo Contratto</label>
                <select
                  value={tipoContrattoFilter}
                  onChange={(e) => setTipoContrattoFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="">Tutti</option>
                  {tipiContratto.map((tipo) => (
                    <option key={tipo.id} value={tipo.id}>
                      {tipo.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Stato</label>
                <select
                  value={statoFilter}
                  onChange={(e) => setStatoFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="">Tutti</option>
                  <option value="attivo">Attivo</option>
                  <option value="scaduto">Scaduto</option>
                  <option value="sospeso">Sospeso</option>
                </select>
              </div>
            </div>
          </div>

          {contratti.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Nessun contratto trovato</p>
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-3 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={allSelected}
                        ref={(el) => { if (el) el.indeterminate = someSelected; }}
                        onChange={toggleAllSelection}
                        className="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Tipo Contratto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Data Inizio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Data Fine
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Stato
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Azioni
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {contratti.map((contratto) => (
                    <tr key={contratto.id} className={selectedIds.has(contratto.id) ? 'ring-1 ring-inset ring-indigo-300 dark:ring-indigo-600' : ''}>
                      <td className="px-3 py-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(contratto.id)}
                          onChange={() => setSelectedIds((prev) => {
                            const next = new Set(prev);
                            if (next.has(contratto.id)) next.delete(contratto.id); else next.add(contratto.id);
                            return next;
                          })}
                          className="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                        {clientiMap.current.get(contratto.cliente_id) || 'Cliente sconosciuto'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {tipiContrattoMap.current.get(contratto.tipo_contratto_id) || 'Tipo sconosciuto'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatDate(contratto.data_inizio)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatDate(contratto.data_fine)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatoBadge(contratto.stato)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditClick(contratto)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Modifica
                          </button>
                          <button
                            onClick={() => handleDelete(contratto)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Elimina
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* PDF Contracts Section */}
      {contrattiDocumenti.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Contratti caricati (PDF)</h2>
          <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data caricamento</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stato AI</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {contrattiDocumenti.map((doc) => (
                  <tr key={doc.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">{doc.file_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{doc.tipo_documento_raw || doc.tipo_documento}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {new Date(doc.created_at).toLocaleDateString('it-IT')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {doc.verificato_da_utente ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Verificato</span>
                      ) : doc.classificazione_ai ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Da verificare</span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">In elaborazione</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ContrattoFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
        contratto={editingContratto}
        clienti={clienti}
        tipiContratto={tipiContratto}
      />

      <UploadDocumentoModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={handleUploadSuccess}
        isContratto={true}
      />

      {/* Bulk delete confirmation modal */}
      {bulkConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Conferma eliminazione</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Stai per eliminare{' '}
              <strong className="text-gray-900 dark:text-gray-100">
                {selectedIds.size} {selectedIds.size === 1 ? 'contratto' : 'contratti'}
              </strong>.{' '}
              L'operazione non è reversibile.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setBulkConfirmOpen(false)}
                disabled={bulkDeleting}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
              >
                Annulla
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={bulkDeleting}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-50"
              >
                {bulkDeleting && (
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                )}
                {bulkDeleting ? 'Eliminazione...' : 'Elimina'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className={`rounded-xl px-4 py-3 shadow-xl flex items-center gap-3 ${toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
            <span className="text-sm font-medium">{toast.message}</span>
            <button onClick={() => setToast(null)} className="ml-auto p-1 hover:bg-white/20 rounded-lg transition-colors">
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