import { useState } from 'react';
import { AxiosError } from 'axios';
import { classificaDocumento } from '@/services/documentoService';
import { TIPO_LABELS } from '@/utils/documentoLabels';
import type { ClassificazioneOverride, Documento, TipoDocumento } from '@/types/documento';
import type { Cliente } from '@/types/cliente';
import type { Contratto } from '@/types/contratto';

interface Props {
  documento: Documento;
  clienti: Cliente[];
  contratti: Contratto[];
  onClose: () => void;
  onSuccess: (updated: Documento) => void;
}

export function ClassificazioneModal({ documento, clienti, contratti, onClose, onSuccess }: Props) {
  const [tipoDocumento, setTipoDocumento] = useState<TipoDocumento>(documento.tipo_documento);
  const [clienteId, setClienteId] = useState<number>(documento.cliente_id);
  const [contrattoId, setContrattoId] = useState<number | null>(documento.contratto_id);
  const [note, setNote] = useState(documento.note ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const contrattiFiltered = contratti.filter((c) => c.cliente_id === clienteId);

  const call = async (body: ClassificazioneOverride) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await classificaDocumento(documento.id, body);
      onSuccess(updated);
    } catch (err) {
      if (err instanceof AxiosError) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Errore durante la classificazione');
      } else {
        setError('Errore sconosciuto');
      }
    } finally {
      setLoading(false);
    }
  };

  // Confirms the current tipo_documento with minimal body (no other fields touched).
  const handleConferma = () => call({ tipo_documento: tipoDocumento });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    call({
      tipo_documento: tipoDocumento,
      cliente_id: clienteId,
      contratto_id: contrattoId,
      note: note.trim() || null,
    });
  };

  const handleClienteChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setClienteId(parseInt(e.target.value));
    setContrattoId(null);
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  const spinner = (
    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  );

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4"
      onClick={handleOverlayClick}
    >
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Classificazione documento</h3>
            <p className="mt-0.5 text-xs text-gray-500 truncate max-w-xs">{documento.file_name}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <span className="sr-only">Chiudi</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md">{error}</div>
          )}

          {/* AI info banner */}
          {documento.classificazione_ai !== null && !documento.verificato_da_utente && (
            <div className="p-3 text-sm bg-blue-50 border border-blue-100 rounded-md">
              <p className="text-blue-800 font-medium">Classificazione AI</p>
              {documento.tipo_documento_raw && (
                <p className="text-blue-700 mt-0.5">{documento.tipo_documento_raw}</p>
              )}
              {documento.confidence_score !== null && (
                <p className="text-blue-600 mt-0.5">
                  Confidenza: {Math.round(documento.confidence_score * 100)}%
                </p>
              )}
            </div>
          )}

          {/* Tipo Documento */}
          <div>
            <label htmlFor="classifica-tipo" className="block text-sm font-medium text-gray-700 mb-1">
              Tipo Documento *
            </label>
            <select
              id="classifica-tipo"
              value={tipoDocumento}
              onChange={(e) => setTipoDocumento(e.target.value as TipoDocumento)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              {(Object.keys(TIPO_LABELS) as TipoDocumento[]).map((tipo) => (
                <option key={tipo} value={tipo}>{TIPO_LABELS[tipo]}</option>
              ))}
            </select>
          </div>

          {/* Cliente */}
          <div>
            <label htmlFor="classifica-cliente" className="block text-sm font-medium text-gray-700 mb-1">
              Cliente *
            </label>
            <select
              id="classifica-cliente"
              value={clienteId}
              onChange={handleClienteChange}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              {clienti.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome} {c.cognome ?? ''}
                </option>
              ))}
            </select>
          </div>

          {/* Contratto */}
          <div>
            <label htmlFor="classifica-contratto" className="block text-sm font-medium text-gray-700 mb-1">
              Contratto
            </label>
            <select
              id="classifica-contratto"
              value={contrattoId ?? ''}
              onChange={(e) => setContrattoId(e.target.value ? parseInt(e.target.value) : null)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="">Nessuno</option>
              {contrattiFiltered.map((c) => (
                <option key={c.id} value={c.id}>
                  Contratto #{c.id} ({c.stato})
                </option>
              ))}
            </select>
          </div>

          {/* Note */}
          <div>
            <label htmlFor="classifica-note" className="block text-sm font-medium text-gray-700 mb-1">
              Note
            </label>
            <textarea
              id="classifica-note"
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="Note aggiuntive..."
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Annulla
            </button>
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={handleConferma}
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md shadow-sm hover:bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? spinner : '✓ Conferma'}
              </button>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading && spinner}
                {loading ? 'Salvataggio...' : 'Salva Correzione'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
