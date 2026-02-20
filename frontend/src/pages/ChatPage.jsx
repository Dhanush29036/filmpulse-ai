import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, Send, RefreshCw, Bot, User, Trash2, ChevronDown, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const API = 'http://localhost:8000/api/v1'

const SUGGESTIONS = [
    'What is the Hype Score?',
    'How does audience prediction work?',
    'What is the best time to release a film?',
    'Explain the Discoverability Score',
    'How does the trailer analyzer work?',
    'Should I release on OTT or theatres?',
]

/** Render markdown-like bot replies: bold, bullet lists, numbered lists, newlines, headers */
function formatMessage(text) {
    // Bold **text**
    let html = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08);padding:2px 6px;border-radius:4px;font-size:0.82em">$1</code>')

    // Headers ### Header
    html = html.replace(/^### (.*$)/gm, '<h3 style="margin:16px 0 8px;font-size:1rem;color:var(--primary)">$1</h3>')
    html = html.replace(/^## (.*$)/gm, '<h2 style="margin:20px 0 10px;font-size:1.2rem;color:var(--primary)">$1</h2>')

    // Split into lines
    const lines = html.split('\n')
    const out = []
    let inList = false
    lines.forEach((line, i) => {
        const bulletMatch = line.match(/^[•\-\*]\s+(.+)/)
        const numMatch = line.match(/^(\d+)\.\s+(.+)/)
        if (bulletMatch) {
            if (!inList) { out.push('<ul style="margin:8px 0;padding-left:18px;list-style:none">'); inList = 'ul' }
            out.push(`<li style="margin:4px 0;padding-left:4px">• ${bulletMatch[1]}</li>`)
        } else if (numMatch) {
            if (!inList) { out.push('<ol style="margin:8px 0;padding-left:18px">'); inList = 'ol' }
            out.push(`<li style="margin:4px 0">${numMatch[2]}</li>`)
        } else {
            if (inList) { out.push(inList === 'ul' ? '</ul>' : '</ol>'); inList = false }
            if (line.trim() === '') {
                out.push('<div style="height:6px"></div>')
            } else if (!line.includes('<h')) {
                out.push(`<span>${line}</span><br/>`)
            } else {
                out.push(line)
            }
        }
    })
    if (inList) out.push(inList === 'ul' ? '</ul>' : '</ol>')
    return out.join('')
}

export default function ChatPage() {
    const { authFetch, user } = useAuth()
    const [messages, setMessages] = useState([
        { role: 'assistant', text: `👋 Hi${user?.name ? ` ${user.name.split(' ')[0]}` : ''}! I'm **FilmPulse AI**, your Bollywood intelligence assistant.\n\nAsk me anything about:\n• Audience prediction & demographics\n• Budget optimization & channel allocation\n• Trailer analysis & viral potential\n• Sentiment & hype tracking\n• Release strategy (OTT vs Theatre)\n• Discoverability Score explained`, time: new Date() }
    ])
    const [input, setInput] = useState('')
    const [typing, setTyping] = useState(false)
    const [historyLoaded, setHistoryLoaded] = useState(false)
    const [showScrollBtn, setShowScrollBtn] = useState(false)
    const messagesEndRef = useRef()
    const scrollContainerRef = useRef()
    const textareaRef = useRef()

    // Auto-scroll to bottom
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [])

    useEffect(() => { scrollToBottom() }, [messages, typing])

    // Track scroll position to show/hide scroll button
    const handleScroll = (e) => {
        const el = e.target
        const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
        setShowScrollBtn(!atBottom)
    }

    // Load chat history on mount
    useEffect(() => {
        if (!user || historyLoaded) return
        authFetch(`${API}/chat/history`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data?.messages?.length > 0) {
                    const loaded = data.messages.map(m => ({
                        role: m.role,
                        text: m.content,
                        time: new Date(m.created_at),
                    }))
                    setMessages([
                        { role: 'assistant', text: '🔄 **Resuming your previous session.** Here is your chat history:', time: new Date(), isSystem: true },
                        ...loaded,
                    ])
                }
            })
            .catch(() => { }) // silently ignore — show fresh chat
            .finally(() => setHistoryLoaded(true))
    }, [user])

    const sendMessage = async (text) => {
        const msg = (text || input).trim()
        if (!msg || typing) return
        setInput('')
        setMessages(prev => [...prev, { role: 'user', text: msg, time: new Date() }])
        setTyping(true)
        try {
            const r = await authFetch(`${API}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg }),
            })
            if (!r.ok) {
                const err = await r.json().catch(() => ({}))
                throw new Error(err.detail || `HTTP ${r.status}`)
            }
            const data = await r.json()
            const reply = data.reply || data.message || "I couldn't process that. Please try again."
            // Simulate natural typing delay (100-300ms)
            await new Promise(res => setTimeout(res, 150 + Math.min(reply.length * 0.5, 400)))
            setMessages(prev => [...prev, { role: 'assistant', text: reply, time: new Date(), intent: data.intent }])
        } catch (e) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                text: `⚠️ **Error:** ${e.message || 'Could not reach the backend. Make sure the server is running at port 8000.'}`,
                time: new Date(),
                isError: true,
            }])
        } finally {
            setTyping(false)
            setTimeout(() => textareaRef.current?.focus(), 50)
        }
    }

    const handleKey = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
    }

    const clearChat = () => {
        setMessages([{
            role: 'assistant',
            text: `🆕 Chat cleared! Ask me anything about your film strategy.`,
            time: new Date()
        }])
        setInput('')
    }

    const showSuggestions = messages.length <= 2

    return (
        <div className="page" style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
            <div className="orb orb-purple" style={{ width: 400, height: 400, top: 0, right: -150 }} />
            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40, paddingBottom: 20 }}>

                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
                    <div>
                        <div className="section-label">AI Assistant</div>
                        <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '2rem', marginBottom: 4 }}>
                            FilmPulse Chat
                        </h1>
                        <p className="text-secondary">Powered by TF-IDF intent matching + film industry knowledge base.</p>
                    </div>
                    <button className="btn btn-outline btn-sm" onClick={clearChat} style={{ marginTop: 8 }}>
                        <Trash2 size={14} /> Clear Chat
                    </button>
                </div>

                {/* Chat Container */}
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 280px)', minHeight: 520, position: 'relative' }}>

                    {/* Messages */}
                    <div
                        ref={scrollContainerRef}
                        onScroll={handleScroll}
                        style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}
                    >
                        <AnimatePresence initial={false}>
                            {messages.map((m, i) => (
                                <motion.div key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.2 }}
                                    style={{ display: 'flex', flexDirection: m.role === 'user' ? 'row-reverse' : 'row', gap: 12, alignItems: 'flex-start' }}
                                >
                                    {/* Avatar */}
                                    <div style={{
                                        width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        background: m.role === 'user'
                                            ? 'linear-gradient(135deg, #F5C842, #8B5CF6)'
                                            : m.isError ? 'linear-gradient(135deg,#EF4444,#B91C1C)'
                                                : 'linear-gradient(135deg, #06B6D4, #3B82F6)',
                                        color: 'white',
                                    }}>
                                        {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                                    </div>

                                    {/* Bubble */}
                                    <div style={{ maxWidth: '72%' }}>
                                        <div style={{
                                            background: m.role === 'user'
                                                ? 'rgba(245,200,66,0.10)'
                                                : m.isError ? 'rgba(239,68,68,0.08)'
                                                    : m.isSystem ? 'rgba(6,182,212,0.06)'
                                                        : 'rgba(255,255,255,0.04)',
                                            border: `1px solid ${m.role === 'user' ? 'rgba(245,200,66,0.22)'
                                                : m.isError ? 'rgba(239,68,68,0.3)'
                                                    : m.isSystem ? 'rgba(6,182,212,0.2)'
                                                        : 'rgba(255,255,255,0.07)'
                                                }`,
                                            borderRadius: m.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                                            padding: '12px 16px',
                                            fontSize: '0.88rem',
                                            lineHeight: '1.65',
                                            color: 'var(--text-primary)',
                                        }}
                                            dangerouslySetInnerHTML={{ __html: formatMessage(m.text) }}
                                        />
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4, justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                                            {m.time?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            {m.intent === 'llm_generated' && (
                                                <span style={{ display: 'flex', alignItems: 'center', gap: 3, color: '#10B981' }}>
                                                    <Sparkles size={10} /> AI Insight
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            ))}

                            {/* Typing indicator */}
                            {typing && (
                                <motion.div key="typing" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                                    style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                                    <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg,#06B6D4,#3B82F6)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                        <Bot size={16} color="#fff" />
                                    </div>
                                    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '4px 16px 16px 16px', padding: '14px 20px' }}>
                                        <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                                            {[0, 1, 2].map(d => (
                                                <div key={d} style={{
                                                    width: 7, height: 7, borderRadius: '50%',
                                                    background: '#06B6D4',
                                                    animation: `chatBounce 1.2s ${d * 0.2}s ease-in-out infinite`
                                                }} />
                                            ))}
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Scroll to bottom button */}
                    <AnimatePresence>
                        {showScrollBtn && (
                            <motion.button
                                initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }}
                                onClick={scrollToBottom}
                                style={{
                                    position: 'absolute', bottom: 90, right: 20, width: 36, height: 36,
                                    borderRadius: '50%', background: 'var(--primary)', border: 'none', cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white',
                                    boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
                                }}
                            >
                                <ChevronDown size={18} />
                            </motion.button>
                        )}
                    </AnimatePresence>

                    {/* Suggestion chips */}
                    <AnimatePresence>
                        {showSuggestions && (
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                style={{ padding: '0 20px 12px', display: 'flex', flexWrap: 'wrap', gap: 8, borderTop: '1px solid rgba(255,255,255,0.05)' }}
                            >
                                <div style={{ width: '100%', fontSize: '0.72rem', color: 'var(--text-muted)', padding: '8px 0 4px', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                                    Suggested Questions
                                </div>
                                {SUGGESTIONS.map(s => (
                                    <button key={s} className="btn btn-outline btn-sm"
                                        style={{ fontSize: '0.74rem', padding: '5px 12px' }}
                                        onClick={() => sendMessage(s)}>
                                        {s}
                                    </button>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Input bar */}
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '16px 20px', display: 'flex', gap: 12, alignItems: 'flex-end' }}>
                        <textarea
                            ref={textareaRef}
                            style={{
                                flex: 1, background: 'rgba(255,255,255,0.04)',
                                border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12,
                                color: 'var(--text-primary)', fontFamily: 'Inter', fontSize: '0.88rem',
                                padding: '12px 14px', resize: 'none', outline: 'none',
                                minHeight: 48, maxHeight: 140,
                                transition: 'border-color 0.2s',
                            }}
                            onFocus={e => e.target.style.borderColor = 'rgba(245,200,66,0.4)'}
                            onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                            placeholder="Ask FilmPulse AI anything… (Enter to send, Shift+Enter for new line)"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKey}
                            rows={1}
                            disabled={typing}
                        />
                        <button
                            className="btn btn-primary"
                            style={{ alignSelf: 'flex-end', padding: '12px 18px', flexShrink: 0 }}
                            onClick={() => sendMessage()}
                            disabled={!input.trim() || typing}
                        >
                            {typing ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
                        </button>
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes chatBounce {
                    0%, 100% { transform: translateY(0); opacity: 0.6; }
                    50% { transform: translateY(-5px); opacity: 1; }
                }
            `}</style>
        </div>
    )
}
