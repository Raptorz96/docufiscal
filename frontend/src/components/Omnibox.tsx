import { useState, useRef, useEffect, useCallback } from 'react';
import type { Documento } from '../types/documento';
import type { Cliente } from '../types/cliente';
import api from '../services/api';

interface SemanticSearchResult {
  documento: Documento;
  score: number;
}

interface OmniboxProps {
  clienti: Array<Pick<Cliente, 'id' | 'nome' | 'cognome'>>;
  onSelectDocument: (documento: Documento) => void;
}

const TIPO_BADGE: Record<string, { label: string; className: string }> = {
  fattura:                { label: 'Fattura',        className: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200' },
  f24:                    { label: 'F24',             className: 'bg-orange-50 text-orange-700 ring-1 ring-orange-200' },
  dichiarazione_redditi:  { label: 'Dichiarazione',  className: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' },
  cu:                     { label: 'CU',              className: 'bg-violet-50 text-violet-700 ring-1 ring-violet-200' },
  busta_paga:             { label: 'Busta Paga',     className: 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200' },
  contratto:              { label: 'Contratto',      className: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200' },
  bilancio:               { label: 'Bilancio',       className: 'bg-teal-50 text-teal-700 ring-1 ring-teal-200' },
  visura_camerale:        { label: 'Visura',         className: 'bg-cyan-50 text-cyan-700 ring-1 ring-cyan-200' },
  comunicazione_agenzia:  { label: 'Com. Agenzia',  className: 'bg-rose-50 text-rose-700 ring-1 ring-rose-200' },
  documento_identita:     { label: 'Identità',      className: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200' },
  altro:                  { label: 'Altro',          className: 'bg-gray-100 text-gray-500 ring-1 ring-gray-200' },
};

function getTipoBadge(tipo: string) {
  return TIPO_BADGE[tipo] ?? { label: tipo, className: 'bg-gray-100 text-gray-500 ring-1 ring-gray-200' };
}

export function Omnibox({ clienti, onSelectDocument }: OmniboxProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SemanticSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isFocused, setIsFocused] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // "/" shortcut: focus input if no other input has focus
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Cleanup debounce + abort on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, []);

  // Click outside → close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchResults = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setIsLoading(true);
    try {
      const res = await api.get<SemanticSearchResult[]>('/search/semantic', {
        params: { q, limit: 5 },
        signal: abortRef.current.signal,
      });
      setResults(res.data);
      setIsOpen(true);
      setActiveIndex(-1);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError' && err.name !== 'CanceledError') {
        console.error('[Omnibox] search error:', err);
        setResults([]);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (val.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    debounceRef.current = setTimeout(() => fetchResults(val), 400);
  };

  const handleSelect = (doc: Documento) => {
    onSelectDocument(doc);
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setActiveIndex(-1);
    inputRef.current?.blur();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(results[activeIndex].documento);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setActiveIndex(-1);
      inputRef.current?.blur();
    }
  };

  const resolveClienteName = (clienteId: number | null): string => {
    if (clienteId == null) return 'Non assegnato';
    const c = clienti.find(cl => cl.id === clienteId);
    if (!c) return 'Non assegnato';
    return c.cognome ? `${c.nome} ${c.cognome}` : c.nome;
  };

  const showEmpty = isOpen && !isLoading && results.length === 0 && query.trim().length >= 2;

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      {/* Input */}
      <div className={`
        flex items-center gap-2 px-3 py-2 rounded-lg border bg-white transition-all duration-150
        ${isOpen || isFocused
          ? 'border-slate-400 ring-2 ring-slate-800/8 shadow-sm'
          : 'border-gray-200 hover:border-gray-300'
        }
      `}>
        {/* Search icon */}
        <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>

        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => { setIsFocused(true); if (results.length > 0) setIsOpen(true); }}
          onBlur={() => setIsFocused(false)}
          placeholder="Cerca documenti… ( / )"
          className="flex-1 text-sm text-slate-700 placeholder-gray-400 bg-transparent outline-none min-w-0"
          autoComplete="off"
          spellCheck={false}
        />

        {/* Right slot: spinner or clear */}
        {isLoading ? (
          <svg className="w-4 h-4 text-slate-400 flex-shrink-0 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
            <path className="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : query.length > 0 ? (
          <button
            onMouseDown={e => e.preventDefault()}
            onClick={() => { setQuery(''); setResults([]); setIsOpen(false); inputRef.current?.focus(); }}
            className="text-gray-400 hover:text-gray-600 flex-shrink-0 transition-colors"
            aria-label="Cancella ricerca"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        ) : (
          <span className="text-[11px] text-gray-300 font-mono flex-shrink-0 select-none hidden sm:block">/</span>
        )}
      </div>

      {/* Dropdown */}
      {(isOpen || showEmpty) && (
        <div className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-gray-100 rounded-xl shadow-xl z-40 overflow-hidden">
          {showEmpty ? (
            <div className="px-4 py-6 text-center text-sm text-gray-400">
              Nessun risultato
            </div>
          ) : (
            <ul className="divide-y divide-gray-50">
              {results.map((res, idx) => {
                const doc = res.documento;
                const badge = getTipoBadge(doc.tipo_documento);
                const clienteNome = resolveClienteName(doc.cliente_id);
                const isActive = idx === activeIndex;

                return (
                  <li key={doc.id}>
                    <button
                      onMouseDown={e => e.preventDefault()}
                      onClick={() => handleSelect(doc)}
                      onMouseEnter={() => setActiveIndex(idx)}
                      className={`
                        w-full text-left px-4 py-3 flex items-center gap-3 transition-colors duration-75
                        ${isActive ? 'bg-slate-50' : 'hover:bg-gray-50'}
                      `}
                    >
                      {/* Document icon */}
                      <div className="flex-shrink-0 w-8 h-8 rounded-md bg-slate-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-slate-800 truncate max-w-[180px]" title={doc.file_name}>
                            {doc.file_name}
                          </span>
                          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium flex-shrink-0 ${badge.className}`}>
                            {badge.label}
                          </span>
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5 truncate">{clienteNome}</div>
                      </div>

                      {/* Arrow */}
                      <svg className={`w-4 h-4 flex-shrink-0 transition-opacity ${isActive ? 'opacity-60' : 'opacity-0'}`}
                        fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
