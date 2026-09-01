import { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { createCliente, updateCliente } from '@/services/clientiService';
import type { Cliente, ClienteCreate, ClienteUpdate } from '@/types/cliente';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  cliente?: Cliente;
}

export function ClienteFormModal({ isOpen, onClose, onSuccess, cliente }: Props) {
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    short_id: '',
    codice_fiscale: '',
    partita_iva: '',
    tipo: 'persona_fisica' as 'persona_fisica' | 'azienda',
    email: '',
    telefono: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditMode = !!cliente;

  useEffect(() => {
    if (isOpen) {
      if (cliente) {
        setFormData({
          nome: cliente.nome,
          cognome: cliente.cognome || '',
          short_id: cliente.short_id?.toString() || '',
          codice_fiscale: cliente.codice_fiscale || '',
          partita_iva: cliente.partita_iva || '',
          tipo: cliente.tipo,
          email: cliente.email || '',
          telefono: cliente.telefono || ''
        });
      } else {
        setFormData({
          nome: '',
          cognome: '',
          short_id: '',
          codice_fiscale: '',
          partita_iva: '',
          tipo: 'persona_fisica',
          email: '',
          telefono: ''
        });
      }
      setError(null);
    }
  }, [isOpen, cliente]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.nome.trim()) {
      setError('Il nome è obbligatorio');
      return;
    }

    if (!formData.codice_fiscale.trim() && !formData.partita_iva.trim()) {
      setError('Inserire almeno uno tra Codice Fiscale e Partita IVA');
      return;
    }

    if (formData.email && !isValidEmail(formData.email)) {
      setError('Formato email non valido');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const dataToSubmit: ClienteCreate | ClienteUpdate = {
        nome: formData.nome.trim(),
        cognome: formData.cognome.trim() || undefined,
        short_id: formData.short_id ? parseInt(formData.short_id, 10) : undefined,
        codice_fiscale: formData.codice_fiscale.trim() || undefined,
        partita_iva: formData.partita_iva.trim() || undefined,
        tipo: formData.tipo,
        email: formData.email.trim() || undefined,
        telefono: formData.telefono.trim() || undefined
      };

      if (isEditMode && cliente) {
        await updateCliente(cliente.id, dataToSubmit);
      } else {
        await createCliente(dataToSubmit as ClienteCreate);
      }

      onSuccess();
    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 409) {
          setError('Codice fiscale/P.IVA già esistente');
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

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
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
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            {isEditMode ? 'Modifica Cliente' : 'Nuovo Cliente'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
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
            <div className="p-3 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-md">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="nome" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Nome *
              </label>
              <input
                type="text"
                id="nome"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                required
              />
            </div>

            <div>
              <label htmlFor="cognome" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Cognome
              </label>
              <input
                type="text"
                id="cognome"
                value={formData.cognome}
                onChange={(e) => setFormData({ ...formData, cognome: e.target.value })}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          <div>
            <label htmlFor="short_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Short ID (es. #105)
            </label>
            <input
              type="number"
              id="short_id"
              value={formData.short_id}
              onChange={(e) => setFormData({ ...formData, short_id: e.target.value })}
              placeholder="Inserisci numero"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          <div>
            <label htmlFor="codice_fiscale" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Codice Fiscale **
            </label>
            <input
              type="text"
              id="codice_fiscale"
              value={formData.codice_fiscale}
              onChange={(e) => setFormData({ ...formData, codice_fiscale: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              maxLength={16}
            />
          </div>

          <div>
            <label htmlFor="partita_iva" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Partita IVA **
            </label>
            <input
              type="text"
              id="partita_iva"
              value={formData.partita_iva}
              onChange={(e) => setFormData({ ...formData, partita_iva: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              maxLength={11}
            />
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 -mt-2">** Almeno uno dei due è obbligatorio</p>

          <div>
            <label htmlFor="tipo" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo
            </label>
            <select
              id="tipo"
              value={formData.tipo}
              onChange={(e) => setFormData({ ...formData, tipo: e.target.value as 'persona_fisica' | 'azienda' })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="persona_fisica">Persona Fisica</option>
              <option value="azienda">Azienda</option>
            </select>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          <div>
            <label htmlFor="telefono" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Telefono
            </label>
            <input
              type="text"
              id="telefono"
              value={formData.telefono}
              onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>

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