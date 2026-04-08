import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { Documento } from '../types/documento';
import { getClienti } from '../services/clientiService';
import { getContratti } from '../services/contrattiService';
import type { Cliente } from '../types/cliente';
import type { Contratto } from '../types/contratto';

interface DocumentContextType {
    viewingDocument: Documento | null;
    setViewingDocument: (doc: Documento | null) => void;
    openDocumentById: (docId: number) => Promise<void>;
    clienti: Cliente[];
    contratti: Contratto[];
    refreshSupportData: () => Promise<void>;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export function DocumentProvider({ children }: { children: ReactNode }) {
    const [viewingDocument, setViewingDocument] = useState<Documento | null>(null);
    const [clienti, setClienti] = useState<Cliente[]>([]);
    const [contratti, setContratti] = useState<Contratto[]>([]);

    const refreshSupportData = useCallback(async () => {
        try {
            const [clientiData, contrattiData] = await Promise.all([
                getClienti(),
                getContratti(),
            ]);
            setClienti(clientiData);
            setContratti(contrattiData);
        } catch (err) {
            console.error('Errore nel caricamento dei dati di supporto:', err);
        }
    }, []);

    const openDocumentById = useCallback(async (docId: number) => {
        // Here we could fetch the specific document from the backend if not in memory
        // For now, since we usually have the ID from search results, we'll need an API to get doc details
        // Or we assume the chatbot returns enough metadata.
        // Let's assume we need to fetch it to be safe.
        try {
            const { getDocumento } = await import('../services/documentoService');
            const doc = await getDocumento(docId);
            setViewingDocument(doc);
        } catch (err) {
            console.error('Errore nell\'apertura del documento:', err);
        }
    }, []);

    return (
        <DocumentContext.Provider
            value={{
                viewingDocument,
                setViewingDocument,
                openDocumentById,
                clienti,
                contratti,
                refreshSupportData,
            }}
        >
            {children}
        </DocumentContext.Provider>
    );
}

export function useDocument() {
    const context = useContext(DocumentContext);
    if (context === undefined) {
        throw new Error('useDocument must be used within a DocumentProvider');
    }
    return context;
}
