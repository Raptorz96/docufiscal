import { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { createContratto, updateContratto } from '@/services/contrattiService';
import type { Contratto, ContrattoCreate, ContrattoUpdate } from '@/types/contratto';
import type { Cliente } from '@/types/cliente';
import type { TipoContratto } from '@/types/tipoContratto';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  contratto?: Contratto;
  clienti: Cliente[];
  tipiContratto: TipoContratto[];
}

export function ContrattoFormModal({ isOpen, onClose, onSuccess, contratto, clienti, tipiContratto }: Props) {
  const [formData, setFormData] = useState({
    cliente_id: '',
    tipo_contratto_id: '',
    data_inizio: '',
    data_fine: '',
    stato: 'attivo' as 'attivo' | 'scaduto' | 'sospeso',
    note: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditMode = !!contratto;

  useEffect(() => {
    if (isOpen) {
      if (contratto) {
        setFormData({
          cliente_id: contratto.cliente_id.toString(),
          tipo_contratto_id: contratto.tipo_contratto_id.toString(),
          data_inizio: contratto.data_inizio,
          data_fine: contratto.data_fine || '',
          stato: contratto.stato,
          note: contratto.note || ''
        });
      } else {
        setFormData({
          cliente_id: '',
          tipo_contratto_id: '',
          data_inizio: '',
          data_fine: '',
          stato: 'attivo',
          note: ''
        });
      }
      setError(null);
    }
  }, [isOpen, contratto]);


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.cliente_id || !formData.tipo_contratto_id || !formData.data_inizio) {
      setError('Cliente, tipo contratto e data inizio sono obbligatori');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const dataToSubmit: ContrattoCreate | ContrattoUpdate = {
        cliente_id: parseInt(formData.cliente_id),
        tipo_contratto_id: parseInt(formData.tipo_contratto_id),
        data_inizio: formData.data_inizio,
        data_fine: formData.data_fine || undefined,
        stato: formData.stato,
        note: formData.note || undefined
      };

      if (isEditMode && contratto) {
        await updateContratto(contratto.id, dataToSubmit);
      } else {
        await createContratto(dataToSubmit as ContrattoCreate);
      }

      onSuccess();
    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 404) {
          setError('Cliente o tipo contratto non trovato');
        } else {
          setError(err.response?.data?.detail || 'Errore durante il salvataggio');
        }
      } else {
        setError('Errore sconosciuto');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4"
      onClick={handleOverlayClick}
    >
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            {isEditMode ? 'Modifica Contratto' : 'Nuovo Contratto'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            type="button"
          >
            <span className="sr-only">Chiudi</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="cliente_id" className="block text-sm font-medium text-gray-700 mb-1">
                Cliente *
              </label>
              <select
                id="cliente_id"
                value={formData.cliente_id}
                onChange={(e) => setFormData({ ...formData, cliente_id: e.target.value })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                required
              >
                <option value="">Seleziona cliente</option>
                {clienti.map((cliente) => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nome} {cliente.cognome || ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="tipo_contratto_id" className="block text-sm font-medium text-gray-700 mb-1">
                Tipo Contratto *
              </label>
              <select
                id="tipo_contratto_id"
                value={formData.tipo_contratto_id}
                onChange={(e) => setFormData({ ...formData, tipo_contratto_id: e.target.value })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                required
              >
                <option value="">Seleziona tipo contratto</option>
                {tipiContratto.map((tipo) => (
                  <option key={tipo.id} value={tipo.id}>
                    {tipo.nome}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="data_inizio" className="block text-sm font-medium text-gray-700 mb-1">
                Data Inizio *
              </label>
              <input
                type="date"
                id="data_inizio"
                value={formData.data_inizio}
                onChange={(e) => setFormData({ ...formData, data_inizio: e.target.value })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                required
              />
            </div>

            <div>
              <label htmlFor="data_fine" className="block text-sm font-medium text-gray-700 mb-1">
                Data Fine
              </label>
              <input
                type="date"
                id="data_fine"
                value={formData.data_fine}
                onChange={(e) => setFormData({ ...formData, data_fine: e.target.value })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div>
              <label htmlFor="stato" className="block text-sm font-medium text-gray-700 mb-1">
                Stato
              </label>
              <select
                id="stato"
                value={formData.stato}
                onChange={(e) => setFormData({ ...formData, stato: e.target.value as 'attivo' | 'scaduto' | 'sospeso' })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value="attivo">Attivo</option>
                <option value="scaduto">Scaduto</option>
                <option value="sospeso">Sospeso</option>
              </select>
            </div>

            <div>
              <label htmlFor="note" className="block text-sm font-medium text-gray-700 mb-1">
                Note
              </label>
              <textarea
                id="note"
                rows={3}
                value={formData.note}
                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="Note aggiuntive..."
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Annulla
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Salvataggio...' : (isEditMode ? 'Aggiorna' : 'Crea')}
              </button>
            </div>
          </form>
      </div>
    </div>
  );
}