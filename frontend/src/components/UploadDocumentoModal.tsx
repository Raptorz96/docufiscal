import { useState, useEffect, useRef } from 'react';
import { AxiosError } from 'axios';
import { uploadDocumento } from '@/services/documentoService';
import { getClienti } from '@/services/clientiService';
import { getContratti } from '@/services/contrattiService';
import { TIPO_LABELS } from '@/utils/documentoLabels';
import { formatFileSize } from '@/utils/formatters';
import type { TipoDocumento, Documento } from '@/types/documento';
import type { Cliente } from '@/types/cliente';
import type { Contratto } from '@/types/contratto';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (doc: Documento) => void;
  isContratto?: boolean;
}

const EMPTY_FORM = {
  clienteId: '',
  contrattoId: '',
  tipoDocumento: 'altro' as TipoDocumento,
  note: '',
};

export function UploadDocumentoModal({ isOpen, onClose, onSuccess, isContratto = false }: Props) {
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [file, setFile] = useState<File | null>(null);
  const [clienti, setClienti] = useState<Cliente[]>([]);
  const [contratti, setContratti] = useState<Contratto[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load support data once on mount
  useEffect(() => {
    Promise.all([getClienti(), getContratti()])
      .then(([clientiData, contrattiData]) => {
        setClienti(clientiData);
        setContratti(contrattiData);
      })
      .catch(() => {
        setError('Errore nel caricamento dei dati');
      });
  }, []);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData(EMPTY_FORM);
      setFile(null);
      setError(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }, [isOpen]);

  const contrattiFiltered = formData.clienteId
    ? contratti.filter((c) => c.cliente_id === parseInt(formData.clienteId))
    : contratti;

  const handleClienteChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData({ ...formData, clienteId: e.target.value, contrattoId: '' });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] ?? null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Cliente is now optional for AI auto-matching
    if (!file) {
      setError('Il file è obbligatorio');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fd = new FormData();
      fd.append('cliente_id', formData.clienteId);
      if (formData.contrattoId) fd.append('contratto_id', formData.contrattoId);
      fd.append('tipo_documento', formData.tipoDocumento);
      if (formData.note.trim()) fd.append('note', formData.note.trim());
      fd.append('file', file);

      const newDoc = await uploadDocumento(fd, isContratto);
      onSuccess(newDoc);
    } catch (err) {
      if (err instanceof AxiosError) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Errore durante il caricamento');
      } else {
        setError('Errore sconosciuto');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  if (!isOpen) return null;

  const isSubmitDisabled = loading || !file;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4"
      onClick={handleOverlayClick}
    >
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Carica Documento</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <span className="sr-only">Chiudi</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-md">
              {error}
            </div>
          )}

          {/* Cliente */}
          <div>
            <label htmlFor="upload-cliente" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Cliente (opzionale per auto-matching)
            </label>
            <select
              id="upload-cliente"
              value={formData.clienteId}
              onChange={handleClienteChange}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="">Seleziona cliente</option>
              {clienti.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome} {c.cognome ?? ''}
                </option>
              ))}
            </select>
          </div>

          {/* Contratto */}
          <div>
            <label htmlFor="upload-contratto" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Contratto
            </label>
            <select
              id="upload-contratto"
              value={formData.contrattoId}
              onChange={(e) => setFormData({ ...formData, contrattoId: e.target.value })}
              disabled={!formData.clienteId}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm disabled:bg-gray-100 dark:disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              <option value="">Nessuno</option>
              {contrattiFiltered.map((c) => (
                <option key={c.id} value={c.id}>
                  Contratto #{c.id} ({c.stato})
                </option>
              ))}
            </select>
          </div>

          {/* Tipo Documento */}
          <div>
            <label htmlFor="upload-tipo" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo Documento
            </label>
            <select
              id="upload-tipo"
              value={formData.tipoDocumento}
              onChange={(e) => setFormData({ ...formData, tipoDocumento: e.target.value as TipoDocumento })}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              {(Object.keys(TIPO_LABELS) as TipoDocumento[]).map((tipo) => (
                <option key={tipo} value={tipo}>{TIPO_LABELS[tipo]}</option>
              ))}
            </select>
          </div>

          {/* Note */}
          <div>
            <label htmlFor="upload-note" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Note
            </label>
            <textarea
              id="upload-note"
              rows={3}
              value={formData.note}
              onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="Note aggiuntive..."
            />
          </div>

          {/* File */}
          <div>
            <label htmlFor="upload-file" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              File *
            </label>
            <input
              ref={fileInputRef}
              id="upload-file"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-indigo-900/30 dark:file:text-indigo-400 dark:hover:file:bg-indigo-900/50"
            />
            {file && (
              <p className="mt-1 text-xs text-gray-500">
                {file.name} — {formatFileSize(file.size)}
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Annulla
            </button>
            <button
              type="submit"
              disabled={isSubmitDisabled}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading && (
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              )}
              {loading ? 'Caricamento...' : 'Carica'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
