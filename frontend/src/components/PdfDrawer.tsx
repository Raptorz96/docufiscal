import { useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';
import { getDocumentoBlobUrl, classificaDocumento } from '@/services/documentoService';
import {
    TIPO_LABELS,
    MACRO_CATEGORIA_LABELS,
    MACRO_CATEGORIA_BADGE_CLASSES,
    type MacroCategoria,
} from '@/utils/documentoLabels';
import { ClassificazioneModal } from '@/components/ClassificazioneModal';
import type { Documento } from '@/types/documento';
import type { Cliente } from '@/types/cliente';
import type { Contratto } from '@/types/contratto';

interface Props {
    documento: Documento | null;
    clienti: Cliente[];
    contratti: Contratto[];
    onClose: () => void;
    /** Called after a successful Conferma or Modifica so the parent can refresh the row. */
    onSuccess: (updated: Documento) => void;
}

export function PdfDrawer({ documento, clienti, contratti, onClose, onSuccess }: Props) {
    const [blobUrl, setBlobUrl] = useState<string | null>(null);
    const [loadingPdf, setLoadingPdf] = useState(false);
    const [pdfError, setPdfError] = useState<string | null>(null);
    const [confirmingId, setConfirmingId] = useState<number | null>(null);
    const [showModifica, setShowModifica] = useState(false);

    // ─── Blob URL lifecycle ────────────────────────────────────────────────────
    // This is the critical section the user asked about.
    //
    // Every time `documento` changes (new file selected) we:
    //   1. Immediately revoke the *previous* blob URL to free browser memory.
    //   2. Fetch the new blob and create a fresh ObjectURL.
    //
    // The cleanup function returned by useEffect is called:
    //   - When `documento` changes (before the next effect runs) → prevents
    //     accumulating URLs when the user browses through multiple documents.
    //   - When the component unmounts → ensures the last URL is always revoked.
    //
    // Net result: at most ONE live ObjectURL at any given moment.
    useEffect(() => {
        // Nothing to do if the drawer is closed
        if (documento === null) {
            setBlobUrl(null);
            setPdfError(null);
            return;
        }

        // Only try to load PDFs; show a clear message for other types
        if (documento.mime_type !== 'application/pdf') {
            setBlobUrl(null);
            setPdfError('Anteprima non disponibile per questo tipo di file.');
            return;
        }

        let cancelled = false; // guard against stale async results if the doc changes quickly
        let createdUrl: string | null = null;

        const loadBlob = async () => {
            setLoadingPdf(true);
            setPdfError(null);
            try {
                const url = await getDocumentoBlobUrl(documento.id);
                if (!cancelled) {
                    createdUrl = url;
                    setBlobUrl(url);
                } else {
                    // We were already superseded — revoke immediately
                    URL.revokeObjectURL(url);
                }
            } catch (err) {
                if (!cancelled) {
                    const msg =
                        err instanceof AxiosError
                            ? err.response?.data?.detail ?? 'Errore nel caricamento del PDF'
                            : 'Errore sconosciuto';
                    setPdfError(typeof msg === 'string' ? msg : 'Errore nel caricamento del PDF');
                }
            } finally {
                if (!cancelled) setLoadingPdf(false);
            }
        };

        loadBlob();

        // Cleanup: revoke the URL we created for *this* render to avoid memory leaks.
        return () => {
            cancelled = true;
            if (createdUrl) {
                URL.revokeObjectURL(createdUrl);
                createdUrl = null;
            }
            setBlobUrl(null);
        };
    }, [documento?.id]); // re-run only when the selected document ID changes

    // ─── Actions ──────────────────────────────────────────────────────────────
    const handleConferma = useCallback(async () => {
        if (!documento) return;
        setConfirmingId(documento.id);
        try {
            const updated = await classificaDocumento(documento.id, {});
            onSuccess(updated);
        } catch {
            // keep drawer open on error, let user retry
        } finally {
            setConfirmingId(null);
        }
    }, [documento, onSuccess]);

    const handleModificaSuccess = useCallback(
        (updated: Documento) => {
            setShowModifica(false);
            onSuccess(updated);
        },
        [onSuccess],
    );

    // ─── Helpers ──────────────────────────────────────────────────────────────
    const getMacroBadge = (macro?: string | null) => {
        if (!macro) return <span className="text-xs text-gray-400">—</span>;
        const key = macro as MacroCategoria;
        const label = MACRO_CATEGORIA_LABELS[key] ?? macro;
        const cls =
            MACRO_CATEGORIA_BADGE_CLASSES[key] ?? 'bg-gray-100 text-gray-600 border border-gray-200';
        return (
            <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${cls}`}
            >
                {label}
            </span>
        );
    };

    const isConfirming = confirmingId !== null;
    const isVerified = documento?.verificato_da_utente ?? false;
    const hasAiData = documento?.classificazione_ai !== null;

    // ─── Render ───────────────────────────────────────────────────────────────
    // The drawer is always mounted alongside DocumentiPage; visibility is driven by `documento !== null`.
    const isOpen = documento !== null;

    return (
        <>
            {/* ── Backdrop (subtle dimming, doesn't block table interaction) ── */}
            <div
                className={`fixed inset-y-0 right-0 z-50 pointer-events-none transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0'
                    }`}
                style={{ width: '45vw', background: 'rgba(0,0,0,0.12)' }}
            />

            {/* ── Drawer panel ── */}
            <div
                className={`fixed top-0 right-0 h-full z-[60] flex flex-col bg-white shadow-2xl border-l border-gray-200 transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'
                    }`}
                style={{ width: '45vw' }}
                aria-hidden={!isOpen}
            >
                {documento && (
                    <>
                        {/* ── Header ── */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 bg-gray-50 flex-shrink-0">
                            <div className="min-w-0 flex-1 pr-3">
                                <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-0.5">
                                    Anteprima documento
                                </p>
                                <h2
                                    className="text-sm font-semibold text-gray-900 truncate"
                                    title={documento.file_name}
                                >
                                    {documento.file_name}
                                </h2>
                            </div>
                            <button
                                onClick={onClose}
                                className="flex-shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-200 transition-colors"
                                title="Chiudi anteprima"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        {/* ── PDF viewer (60% of drawer height) ── */}
                        <div className="flex-shrink-0 bg-gray-100 border-b border-gray-200" style={{ height: '58%' }}>
                            {loadingPdf && (
                                <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-500">
                                    <svg
                                        className="animate-spin h-8 w-8 text-indigo-500"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        />
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8v8H4z"
                                        />
                                    </svg>
                                    <span className="text-sm font-medium">Caricamento PDF…</span>
                                </div>
                            )}

                            {pdfError && !loadingPdf && (
                                <div className="flex flex-col items-center justify-center h-full gap-2 text-gray-400 px-6 text-center">
                                    <svg
                                        className="w-10 h-10 text-gray-300"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={1.5}
                                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                        />
                                    </svg>
                                    <p className="text-sm text-gray-500">{pdfError}</p>
                                </div>
                            )}

                            {blobUrl && !loadingPdf && !pdfError && (
                                <iframe
                                    src={blobUrl}
                                    title={`Anteprima: ${documento.file_name}`}
                                    className="w-full h-full border-0"
                                // sandbox is intentionally omitted so the browser PDF renderer works fully
                                />
                            )}
                        </div>

                        {/* ── Info panel + quick actions (scrollable remainder) ── */}
                        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
                            {/* Classification status pill */}
                            <div className="flex items-center gap-2">
                                {isVerified ? (
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">
                                        ✓ Verificato
                                    </span>
                                ) : hasAiData ? (
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-200">
                                        ⚡ Classificato dall'AI
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200">
                                        Non classificato
                                    </span>
                                )}
                            </div>

                            {/* Metadata grid */}
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-gray-50 rounded-lg px-3 py-2.5">
                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                                        Tipo
                                    </p>
                                    <p className="text-sm font-medium text-gray-800">
                                        {TIPO_LABELS[documento.tipo_documento]}
                                    </p>
                                </div>

                                <div className="bg-gray-50 rounded-lg px-3 py-2.5">
                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                                        Anno
                                    </p>
                                    <p className="text-sm font-semibold text-gray-800">
                                        {documento.anno_competenza ?? (
                                            <span className="text-gray-400 font-normal">—</span>
                                        )}
                                    </p>
                                </div>

                                <div className="bg-gray-50 rounded-lg px-3 py-2.5 col-span-2">
                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                                        Macro-Categoria
                                    </p>
                                    <div className="mt-0.5">{getMacroBadge(documento.macro_categoria)}</div>
                                </div>

                                {documento.note && (
                                    <div className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2.5 col-span-2">
                                        <p className="text-xs font-semibold text-amber-500 uppercase tracking-wider mb-1">
                                            Note
                                        </p>
                                        <p className="text-sm text-gray-700 leading-relaxed">{documento.note}</p>
                                    </div>
                                )}

                                {documento.confidence_score !== null && !isVerified && (
                                    <div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2.5 col-span-2">
                                        <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">
                                            Confidenza AI
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-blue-100 rounded-full h-1.5 overflow-hidden">
                                                <div
                                                    className="h-full rounded-full bg-blue-500 transition-all duration-500"
                                                    style={{ width: `${Math.round((documento.confidence_score ?? 0) * 100)}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-semibold text-blue-700 flex-shrink-0">
                                                {Math.round((documento.confidence_score ?? 0) * 100)}%
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Quick action buttons */}
                            <div className="pt-2 border-t border-gray-100 flex flex-col gap-2">
                                {!isVerified && (
                                    <button
                                        onClick={handleConferma}
                                        disabled={isConfirming}
                                        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                                    >
                                        {isConfirming ? (
                                            <>
                                                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                                    <circle
                                                        className="opacity-25"
                                                        cx="12"
                                                        cy="12"
                                                        r="10"
                                                        stroke="currentColor"
                                                        strokeWidth="4"
                                                    />
                                                    <path
                                                        className="opacity-75"
                                                        fill="currentColor"
                                                        d="M4 12a8 8 0 018-8v8H4z"
                                                    />
                                                </svg>
                                                Conferma in corso…
                                            </>
                                        ) : (
                                            <>✓ Conferma classificazione</>
                                        )}
                                    </button>
                                )}

                                <button
                                    onClick={() => setShowModifica(true)}
                                    disabled={isConfirming}
                                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                        />
                                    </svg>
                                    Modifica classificazione
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* ClassificazioneModal — opened from inside the drawer */}
            {showModifica && documento && (
                <ClassificazioneModal
                    documento={documento}
                    clienti={clienti}
                    contratti={contratti}
                    onClose={() => setShowModifica(false)}
                    onSuccess={handleModificaSuccess}
                />
            )}
        </>
    );
}
