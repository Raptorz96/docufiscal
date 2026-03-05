import { useState, useEffect, useRef, useCallback } from 'react';
import { AxiosError } from 'axios';
import { getClienti, deleteCliente } from '@/services/clientiService';
import type { Cliente } from '@/types/cliente';
import { ClienteFormModal } from '@/components/ClienteFormModal';

export function ClientiPage() {
  const [clienti, setClienti] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [tipoFilter, setTipoFilter] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCliente, setEditingCliente] = useState<Cliente | undefined>(undefined);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isInitialMount = useRef(true);

  const loadClienti = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { tipo?: string; search?: string } = {};
      if (tipoFilter) params.tipo = tipoFilter;
      if (search.trim()) params.search = search.trim();

      const data = await getClienti(params);
      setClienti(data);
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail || 'Errore nel caricamento dei clienti');
      } else {
        setError('Errore sconosciuto');
      }
    } finally {
      setLoading(false);
    }
  }, [search, tipoFilter]);

  useEffect(() => {
    loadClienti();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipoFilter]);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      loadClienti();
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [search, loadClienti]);

  const handleDelete = async (cliente: Cliente) => {
    if (!window.confirm(`Sei sicuro di voler eliminare il cliente "${cliente.nome} ${cliente.cognome || ''}"?`)) {
      return;
    }

    try {
      await deleteCliente(cliente.id);
      await loadClienti();
    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 409) {
          alert('Impossibile eliminare: il cliente ha contratti associati');
        } else {
          alert(err.response?.data?.detail || 'Errore durante l\'eliminazione');
        }
      } else {
        alert('Errore sconosciuto durante l\'eliminazione');
      }
    }
  };

  const handleCreateClick = () => {
    setEditingCliente(undefined);
    setIsModalOpen(true);
  };

  const handleEditClick = (cliente: Cliente) => {
    setEditingCliente(cliente);
    setIsModalOpen(true);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    loadClienti();
  };

  const getTipoBadge = (tipo: string) => {
    if (tipo === 'persona_fisica') {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">Persona Fisica</span>;
    }
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Azienda</span>;
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
            onClick={loadClienti}
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
            <h1 className="text-2xl font-semibold text-gray-900">Clienti</h1>
            <p className="mt-2 text-sm text-gray-700">Gestione dei clienti</p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
            <button
              onClick={handleCreateClick}
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
            >
              + Nuovo Cliente
            </button>
          </div>
        </div>

        <div className="mt-6 bg-white shadow-sm rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Cerca clienti..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <select
                  value={tipoFilter}
                  onChange={(e) => setTipoFilter(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="">Tutti</option>
                  <option value="persona_fisica">Persona Fisica</option>
                  <option value="azienda">Azienda</option>
                </select>
              </div>
            </div>
          </div>

          {clienti.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Nessun cliente trovato</p>
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ID Breve
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nome completo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Codice Fiscale
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      P.IVA
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Azioni
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clienti.map((cliente) => (
                    <tr key={cliente.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                        {cliente.short_id ? `#${cliente.short_id}` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {cliente.nome} {cliente.cognome || ''}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {cliente.codice_fiscale || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {cliente.partita_iva || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getTipoBadge(cliente.tipo)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {cliente.email || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditClick(cliente)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Modifica
                          </button>
                          <button
                            onClick={() => handleDelete(cliente)}
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

      <ClienteFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
        cliente={editingCliente}
      />
    </div>
  );
}