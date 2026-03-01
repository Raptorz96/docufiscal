import { useState, useEffect, useRef, useCallback } from 'react';
import { AxiosError } from 'axios';
import { getDocumenti, deleteDocumento, downloadDocumento } from '@/services/documentoService';
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

  const clientiMap = useRef<Map<number, string>>(new Map());
  const contrattiMap = useRef<Map<number, string>>(new Map());
  const isInitialMount = useRef(true);

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
      contrattiMap.current = new Map(
        contrattiData.map((c) => [c.id, `Contratto #${c.id}`])
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
      const params: { cliente_id?: number; contratto_id?: number; tipo_documento?: string } = {};
      if (clienteFilter) params.cliente_id = parseInt(clienteFilter);
      if (contrattoFilter) params.contratto_id = parseInt(contrattoFilter);
      if (tipoFilter) params.tipo_documento = tipoFilter;
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
  }, [clienteFilter, contrattoFilter, tipoFilter]);

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
  }, [clienteFilter, contrattoFilter, tipoFilter]);

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

  const getTipoBadge = (tipo: TipoDocumento) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${TIPO_BADGE_CLASSES[tipo]}`}>
      {TIPO_LABELS[tipo]}
    </span>
  );

  const getAiBadge = (doc: Documento) => {
    // CASO A: already verified by user
    if (doc.verificato_da_utente) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          ✓ Verificato
        </span>
      );
    }
    // CASO D: AI never ran
    if (doc.classificazione_ai === null) {
      return <span className="text-xs text-gray-400">—</span>;
    }
    const label = doc.tipo_documento_raw ?? TIPO_LABELS[doc.tipo_documento];
    // CASO B: high confidence
    if (doc.confidence_score !== null && doc.confidence_score >= 0.75) {
      const pct = Math.round(doc.confidence_score * 100);
      return (
        <div className="flex flex-col gap-1">
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            {label} · {pct}%
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setSelectedDocumento(doc)}
              className="px-2 py-0.5 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700"
            >
              Conferma
            </button>
            <button
              onClick={() => setSelectedDocumento(doc)}
              className="px-2 py-0.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100"
            >
              Correggi
            </button>
          </div>
        </div>
      );
    }
    // CASO C: low / missing confidence
    const pct = doc.confidence_score !== null ? Math.round(doc.confidence_score * 100) : null;
    return (
      <div className="flex flex-col gap-1">
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          {pct !== null ? `${label} · ${pct}%` : 'Non classificato'}
        </span>
        <button
          onClick={() => setSelectedDocumento(doc)}
          className="px-2 py-0.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100 self-start"
        >
          Correggi
        </button>
      </div>
    );
  };

  // Contratti visibili nel select: filtrati per cliente se selezionato
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

        <div className="mt-6 bg-white shadow-sm rounded-lg">

          {/* Filtri */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
                <select
                  value={clienteFilter}
                  onChange={(e) => {
                    setClienteFilter(e.target.value);
                    setContrattoFilter('');
                  }}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
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
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nome file
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo Documento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Classificazione AI
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Dimensione
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data caricamento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Azioni
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {documenti.map((doc) => (
                    <tr key={doc.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {doc.file_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getTipoBadge(doc.tipo_documento)}
                      </td>
                      <td className="px-6 py-4">
                        {getAiBadge(doc)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {clientiMap.current.get(doc.cliente_id) ?? '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFileSize(doc.file_size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(doc.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleDownload(doc)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Download
                          </button>
                          <button
                            onClick={() => handleDelete(doc)}
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

      <UploadDocumentoModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={() => { setIsUploadOpen(false); loadDocumenti(); }}
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
    </div>
  );
}
