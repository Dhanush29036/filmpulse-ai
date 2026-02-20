import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, Send, RefreshCw, Bot, User, Zap, Trash2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const API = 'http://localhost:8000/api/v1'

const SUGGESTIONS = [
    'How do I improve my film\'s discoverability?',
    'What budget should I allocate for an Action film?',
    'When is the best time to release a Bollywood film?',
    'How does the sentiment score affect box office?',
    'Explain the discoverability formula',
    'What platforms work best for Hindi films?',
]

export default function ChatPage() {
    const { authFetch } = useAuth()
    const [messages, setMessages] = useState([
        { role: 'assistant', text: "👋 Hi! I'm **FilmPulse AI**, your Bollywood intelligence assistant. Ask me anything about releasing films, optimizing campaigns, sentiment analysis, or using our ML models.", time: new Date() }
    ])
    const [input, setInput] = useState('')
    const [typing, setTyping] = useState(false)
    const messagesEndRef = useRef()

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const sendMessage = async (text) => {
        const msg = text || input.trim()
        if (!msg) return
        setInput('')
        setMessages(prev => [...prev, { role: 'user', text: msg, time: new Date() }])
        setTyping(true)
        try {
            const r = await authFetch(`${API}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg }),
            })
            const data = await r.json()
            setMessages(prev => [...prev, { role: 'assistant', text: data.reply || data.message || 'I couldn\'t process that. Please try again.', time: new Date() }])
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', text: 'Connection error. Make sure the backend is running.', time: new Date() }])
        }
        finally { setTyping(false) }
    }

    const handleKey = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
    }

    const formatText = (text) => {
        // Bold **text**
        return text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')
    }

    return (
        <div className="page" style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
            <div className="orb orb-purple" style={{ width: 400, height: 400, top: 0, right: -150 }} />
            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40, paddingBottom: 20 }}>

                <div style={{ marginBottom: 24 }}>
                    <div className="section-label">AI Assistant</div>
                    <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '2rem', marginBottom: 4 }}>
                        FilmPulse Chat
                    </h1>
                    <p className="text-secondary">Powered by TF-IDF intent matching + film industry knowledge base.</p>
                </div>

                {/* Chat Container */}
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 280px)', minHeight: 500 }}>
                    {/* Messages */}
                    <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
                        <AnimatePresence>
                            {messages.map((m, i) => (
                                <motion.div key={i} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                                    style={{ display: 'flex', flexDirection: m.role === 'user' ? 'row-reverse' : 'row', gap: 12, alignItems: 'flex-start' }}>
                                    <div style={{
                                        width: 36, height: 36, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        background: m.role === 'user' ? 'linear-gradient(135deg, #F5C842, #8B5CF6)' : 'linear-gradient(135deg, #06B6D4, #3B82F6)',
                                        color: '#0D1526', fontWeight: 800,
                                    }}>
                                        {m.role === 'user' ? <User size={16} /> : <Bot size={16} color="#fff" />}
                                    </div>
                                    <div style={{ maxWidth: '72%' }}>
                                        <div style={{
                                            background: m.role === 'user' ? 'rgba(245,200,66,0.12)' : 'rgba(255,255,255,0.04)',
                                            border: `1px solid ${m.role === 'user' ? 'rgba(245,200,66,0.25)' : 'rgba(255,255,255,0.08)'}`,
                                            borderRadius: m.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                                            padding: '12px 16px',
                                            fontSize: '0.88rem',
                                            lineHeight: '1.6',
                                            color: 'var(--text-primary)',
                                        }} dangerouslySetInnerHTML={{ __html: formatText(m.text) }} />
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4, textAlign: m.role === 'user' ? 'right' : 'left' }}>
                                            {m.time?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                            {typing && (
                                <motion.div key="typing" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                    style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                                    <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #06B6D4, #3B82F6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <Bot size={16} color="#fff" />
                                    </div>
                                    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '4px 16px 16px 16px', padding: '12px 20px' }}>
                                        <div style={{ display: 'flex', gap: 4 }}>
                                            {[0, 1, 2].map(d => (
                                                <div key={d} style={{ width: 6, height: 6, borderRadius: '50%', background: '#06B6D4', animation: `bounce 1.2s ${d * 0.2}s ease-in-out infinite` }} />
                                            ))}
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Suggestions */}
                    {messages.length <= 2 && (
                        <div style={{ padding: '0 24px 16px', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                            {SUGGESTIONS.map(s => (
                                <button key={s} className="btn btn-outline btn-sm" style={{ fontSize: '0.75rem', padding: '6px 12px' }} onClick={() => sendMessage(s)}>
                                    {s}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Input */}
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: 20, display: 'flex', gap: 12 }}>
                        <textarea
                            style={{ flex: 1, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, color: 'var(--text-primary)', fontFamily: 'Inter', fontSize: '0.88rem', padding: '12px 14px', resize: 'none', outline: 'none', minHeight: 48, maxHeight: 120 }}
                            placeholder="Ask FilmPulse AI anything… (Enter to send)"
                            value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey} rows={1}
                        />
                        <button className="btn btn-primary" style={{ alignSelf: 'flex-end', padding: '12px 18px' }} onClick={() => sendMessage()} disabled={!input.trim() || typing}>
                            {typing ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
                        </button>
                    </div>
                </div>

                <style>{`
                    @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
                `}</style>
            </div>
        </div>
    )
}
