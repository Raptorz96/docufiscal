import { createContext, useContext } from 'react';
import type { Documento } from '../types/documento';
import type { Cliente } from '../types/cliente';
import type { Contratto } from '../types/contratto';

export interface DocumentContextType {
    viewingDocument: Documento | null;
    setViewingDocument: (doc: Documento | null) => void;
    openDocumentById: (docId: number) => Promise<void>;
    clienti: Cliente[];
    contratti: Contratto[];
    refreshSupportData: () => Promise<void>;
}

export const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export function useDocument() {
    const context = useContext(DocumentContext);
    if (context === undefined) {
        throw new Error('useDocument must be used within a DocumentProvider');
    }
    return context;
}
