import type { TipoDocumento } from '@/types/documento';

export const TIPO_LABELS: Record<TipoDocumento, string> = {
  dichiarazione_redditi: 'Dichiarazione Redditi',
  fattura: 'Fattura',
  f24: 'F24',
  cu: 'CU',
  visura_camerale: 'Visura Camerale',
  busta_paga: 'Busta Paga',
  contratto: 'Contratto',
  bilancio: 'Bilancio',
  comunicazione_agenzia: 'Com. Agenzia',
  documento_identita: 'Doc. Identità',
  altro: 'Altro',
};

export const TIPO_BADGE_CLASSES: Record<TipoDocumento, string> = {
  dichiarazione_redditi: 'bg-blue-100 text-blue-800',
  fattura: 'bg-green-100 text-green-800',
  f24: 'bg-orange-100 text-orange-800',
  cu: 'bg-purple-100 text-purple-800',
  visura_camerale: 'bg-cyan-100 text-cyan-800',
  busta_paga: 'bg-yellow-100 text-yellow-800',
  contratto: 'bg-indigo-100 text-indigo-800',
  bilancio: 'bg-teal-100 text-teal-800',
  comunicazione_agenzia: 'bg-pink-100 text-pink-800',
  documento_identita: 'bg-red-100 text-red-800',
  altro: 'bg-gray-100 text-gray-800',
};

export type MacroCategoria = 'fiscale' | 'lavoro' | 'amministrazione' | 'altro';

export const MACRO_CATEGORIA_LABELS: Record<MacroCategoria, string> = {
  fiscale: 'Fiscale',
  lavoro: 'Lavoro',
  amministrazione: 'Amministrazione',
  altro: 'Altro',
};

export const MACRO_CATEGORIA_BADGE_CLASSES: Record<MacroCategoria, string> = {
  fiscale: 'bg-blue-100 text-blue-800 border border-blue-200',
  lavoro: 'bg-green-100 text-green-800 border border-green-200',
  amministrazione: 'bg-amber-100 text-amber-800 border border-amber-200',
  altro: 'bg-gray-100 text-gray-600 border border-gray-200',
};
