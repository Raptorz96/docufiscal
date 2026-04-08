import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, FileText, ChevronDown, User, Bot, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useDocument } from '../context/DocumentContext';
import api from '../services/api';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    references?: Array<{ doc_id: number; file_name: string }>;
    timestamp: Date;
}

export function DocumentChatbot() {
    const [isOpen, setIsOpen] = useState(false);
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: 'Ciao! Sono il tuo assistente DocuFiscal. Posso aiutarti a trovare informazioni nei tuoi documenti. Cosa vorresti sapere?',
            timestamp: new Date(),
        },
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { openDocumentById } = useDocument();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const history = messages.map(m => ({
                role: m.role,
                content: m.content
            }));

            const response = await api.post('/chat/query', {
                query: input,
                history: history
            });

            const data = response.data;

            const botMessage: Message = {
                id: Date.now().toString(),
                role: 'assistant',
                content: data.answer,
                timestamp: new Date(),
                references: data.references || data.referenced_doc_ids?.map((id: number) => ({
                    doc_id: id,
                    file_name: `Documento #${id}`
                })) || []
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: 'assistant',
                content: "Spiacente, si è verificato un errore nel collegamento con l'AI. Riprova più tardi.",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-40 flex flex-col items-end">
            {/* Chat Window */}
            {isOpen && (
                <div className="mb-4 w-[400px] h-[600px] bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden transition-all duration-300 transform origin-bottom-right">
                    {/* Header */}
                    <div className="bg-indigo-600 px-4 py-3 flex items-center justify-between shadow-sm">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="text-white font-bold text-sm tracking-tight">DocuFiscal AI</h3>
                                <div className="flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                                    <span className="text-indigo-100 text-[10px] font-medium uppercase tracking-wider">Online</span>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="p-1.5 rounded-lg text-indigo-100 hover:bg-white/10 transition-colors"
                        >
                            <ChevronDown className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50 dark:bg-gray-900/50">
                        {messages.map((m) => (
                            <div
                                key={m.id}
                                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className={`max-w-[85%] flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                                    <div className="flex items-center gap-2 mb-1 px-1">
                                        {m.role === 'assistant' ? (
                                            <>
                                                <Bot className="w-3.5 h-3.5 text-indigo-500" />
                                                <span className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-tighter">Assistente</span>
                                            </>
                                        ) : (
                                            <>
                                                <span className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-tighter">Tu</span>
                                                <User className="w-3.5 h-3.5 text-gray-500" />
                                            </>
                                        )}
                                    </div>

                                    <div
                                        className={`rounded-2xl px-4 py-2.5 shadow-sm text-sm ${m.role === 'user'
                                            ? 'bg-indigo-600 text-white rounded-tr-none'
                                            : 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-100 dark:border-gray-600 rounded-tl-none'
                                            }`}
                                    >
                                        <div className="prose prose-sm max-w-none">
                                            <ReactMarkdown>{m.content}</ReactMarkdown>
                                        </div>
                                    </div>

                                    {/* References */}
                                    {m.references && m.references.length > 0 && (
                                        <div className="mt-2 flex flex-wrap gap-2 w-full justify-start">
                                            {m.references.map((ref) => (
                                                <button
                                                    key={ref.doc_id}
                                                    onClick={() => openDocumentById(ref.doc_id)}
                                                    className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-100 text-xs font-semibold hover:bg-indigo-100 transition-all group"
                                                >
                                                    <FileText className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                                                    <span className="truncate max-w-[150px]">{ref.file_name}</span>
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    <span className="text-[9px] text-gray-400 dark:text-gray-500 mt-1 px-1">
                                        {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-white dark:bg-gray-700 border border-gray-100 dark:border-gray-600 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                                    <div className="flex gap-1">
                                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></span>
                                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-100 dark:border-gray-700">
                        <div className="relative flex items-center group">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                placeholder="Chiedi pure..."
                                className="w-full pl-4 pr-12 py-3 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:placeholder:text-gray-400 border-none rounded-xl text-sm focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-gray-400"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || isLoading}
                                className="absolute right-2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:bg-gray-300 transition-all shadow-md active:scale-95"
                            >
                                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-[9px] text-center text-gray-400 dark:text-gray-500 mt-3 uppercase tracking-widest font-medium">
                            Powered by DocuFiscal RAG Engine
                        </p>
                    </div>
                </div>
            )}

            {/* FAB */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`w-14 h-14 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 transform active:scale-90 ${isOpen ? 'bg-indigo-100 text-indigo-600 rotate-90' : 'bg-indigo-600 text-white hover:scale-110'
                    }`}
            >
                {isOpen ? <X className="w-7 h-7" /> : <MessageCircle className="w-7 h-7" />}
                {!isOpen && (
                    <span className="absolute -top-1 -right-1 flex h-4 w-4">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-4 w-4 bg-indigo-500"></span>
                    </span>
                )}
            </button>
        </div>
    );
}
