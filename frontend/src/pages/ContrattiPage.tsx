import { useState, useEffect, useRef, useCallback } from 'react';
import { AxiosError } from 'axios';
import { getContratti, deleteContratto } from '@/services/contrattiService';
import { getClienti } from '@/services/clientiService';
import { getTipiContratto } from '@/services/tipiContrattoService';
import type { Contratto } from '@/types/contratto';
import type { Cliente } from '@/types/cliente';
import type { TipoContratto } from '@/types/tipoContratto';
import { ContrattoFormModal } from '@/components/ContrattoFormModal';

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

  // Maps per lookup nomi
  const clientiMap = useRef<Map<number, string>>(new Map());
  const tipiContrattoMap = useRef<Map<number, string>>(new Map());
  const isInitialMount = useRef(true);

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
    const initializeData = async () => {
      await loadSupportData();
      await loadContratti();
    };
    initializeData();
  }, []);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    loadContratti();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteFilter, tipoContrattoFilter, statoFilter]);

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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
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
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Contratti</h1>
            <p className="mt-2 text-sm text-gray-700">Gestione dei contratti</p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
            <button
              onClick={handleCreateClick}
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
            >
              + Nuovo Contratto
            </button>
          </div>
        </div>

        <div className="mt-6 bg-white shadow-sm rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
                <select
                  value={clienteFilter}
                  onChange={(e) => setClienteFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Contratto</label>
                <select
                  value={tipoContrattoFilter}
                  onChange={(e) => setTipoContrattoFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Stato</label>
                <select
                  value={statoFilter}
                  onChange={(e) => setStatoFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
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
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo Contratto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data Inizio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data Fine
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stato
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Azioni
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {contratti.map((contratto) => (
                    <tr key={contratto.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {clientiMap.current.get(contratto.cliente_id) || 'Cliente sconosciuto'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {tipiContrattoMap.current.get(contratto.tipo_contratto_id) || 'Tipo sconosciuto'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(contratto.data_inizio)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(contratto.data_fine)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatoBadge(contratto.stato)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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

      <ContrattoFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
        contratto={editingContratto}
        clienti={clienti}
        tipiContratto={tipiContratto}
      />
    </div>
  );
}