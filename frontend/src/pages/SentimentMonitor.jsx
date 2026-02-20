import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'react-chartjs-2'
import { MessageSquare, TrendingUp, Heart, Minus, ThumbsDown, RefreshCw, Zap, Send, PlusCircle, Brain, CheckCircle, AlertCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './SentimentMonitor.css'

ChartJS.register(ArcElement, Tooltip, Legend)

const API = 'http://localhost:8000/api/v1'

const DEMO_TWEETS = [
    { id: 1, user: '@cinephile_raj', text: 'The new trailer just dropped and I am HYPED! This is going to be massive 🎬🔥', severity: 'positive', time: '2m ago' },
    { id: 2, user: '@moviebuff_priya', text: 'Story looks predictable but the cinematography is 🤌. Might still watch for visuals.', severity: 'neutral', time: '5m ago' },
    { id: 3, user: '@critic_arun', text: 'Another loud action film with no substance. Tired of this formula. Pass.', severity: 'negative', time: '8m ago' },
    { id: 4, user: '@filmlover_divya', text: "Cast performance in this clip gave me CHILLS. Can't wait for the release!", severity: 'positive', time: '11m ago' },
    { id: 5, user: '@srk_forever', text: 'The background score is absolutely 🔥 Who composed this? Pure gold.', severity: 'positive', time: '14m ago' },
]

const WORDS = [
    { text: 'BLOCKBUSTER', size: 32, color: '#F5C842' }, { text: 'EPIC', size: 28, color: '#8B5CF6' },
    { text: 'HYPED', size: 26, color: '#10B981' }, { text: 'CINEMATIC', size: 22, color: '#06B6D4' },
    { text: 'PREDICTABLE', size: 20, color: '#EF4444' }, { text: 'FIRE', size: 24, color: '#F5C842' },
    { text: 'BRILLIANT', size: 20, color: '#A78BFA' }, { text: 'MASTERPIECE', size: 22, color: '#F5C842' },
    { text: 'BORING', size: 16, color: '#EF4444' }, { text: 'MUST-WATCH', size: 20, color: '#10B981' },
    { text: 'INCREDIBLE', size: 22, color: '#8B5CF6' }, { text: 'AVERAGE', size: 16, color: '#94A3B8' },
]

function HypeGauge({ score }) {
    const color = score >= 70 ? '#10B981' : score >= 50 ? '#F5C842' : '#EF4444'
    return (
        <div className="hype-gauge">
            <svg viewBox="0 0 200 120" width="200" height="120">
                <path d="M 20 110 A 90 90 0 0 1 180 110" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" strokeLinecap="round" />
                <path d="M 20 110 A 90 90 0 0 1 180 110" fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
                    strokeDasharray={`${score * 2.83} 283`}
                    style={{ filter: `drop-shadow(0 0 8px ${color}80)`, transition: 'stroke-dasharray 1.4s cubic-bezier(0.34,1.56,0.64,1)' }} />
                <text x="100" y="95" textAnchor="middle" fill={color} fontSize="32" fontFamily="Outfit" fontWeight="900">{score}</text>
                <text x="100" y="112" textAnchor="middle" fill="#475569" fontSize="11" fontFamily="Inter">HYPE SCORE</text>
            </svg>
        </div>
    )
}

// Inline toast notification component
function Toast({ toast }) {
    if (!toast) return null
    const isSuccess = toast.type === 'success'
    return (
        <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6 }}
            style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 16px', borderRadius: 10,
                background: isSuccess ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                border: `1px solid ${isSuccess ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.35)'}`,
                fontSize: '0.85rem', color: isSuccess ? '#10B981' : '#EF4444',
                flex: '0 0 auto',
            }}
        >
            {isSuccess ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
            {toast.message}
        </motion.div>
    )
}

export default function SentimentMonitor() {
    const { authFetch, user } = useAuth()
    const [films, setFilms] = useState([])
    const [selectedFilmId, setSelectedFilmId] = useState('')
    const [tweets, setTweets] = useState(DEMO_TWEETS)
    const [mlResult, setMlResult] = useState(null)
    const [inputText, setInputText] = useState('')
    const [analyzing, setAnalyzing] = useState(false)
    const [filter, setFilter] = useState('all')
    const [collecting, setCollecting] = useState(false)
    const [refreshing, setRefreshing] = useState(false)
    const [toast, setToast] = useState(null)
    const toastTimerRef = useRef(null)

    const showToast = (message, type = 'success') => {
        clearTimeout(toastTimerRef.current)
        setToast({ message, type })
        toastTimerRef.current = setTimeout(() => setToast(null), 4000)
    }

    // Get the currently selected film object (for title/trailer_url)
    const selectedFilm = films.find(f => f.film_id === selectedFilmId) || null

    // Fetch user's films
    useEffect(() => {
        const query = (user && user.role === 'admin') ? '?show_all=true' : ''
        authFetch(`${API}/films${query}`)
            .then(r => r.json())
            .then(d => {
                const filmList = d.films || []
                setFilms(filmList)
                if (filmList.length > 0) setSelectedFilmId(filmList[0].film_id)
            })
            .catch(console.error)
    }, [user])

    // Fetch real social comments for selected film
    const fetchSocialComments = async (filmId = selectedFilmId) => {
        if (!filmId) return
        setRefreshing(true)
        try {
            const r = await authFetch(`${API}/social/${filmId}/comments?limit=20`)
            if (r.ok) {
                const data = await r.json()
                const comments = data.comments || []
                if (comments.length > 0) {
                    // Format DB comments to match tweet UI
                    const formatted = comments.map(c => ({
                        id: c._id || Math.random(),
                        user: `@${c.username || 'user'}`,
                        text: c.text,
                        severity: (c.sentiment_label || 'neutral').toLowerCase(),
                        time: new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }))
                    setTweets(formatted)
                } else {
                    // Fall back to demo tweets when no collection has run yet
                    setTweets(DEMO_TWEETS)
                }
            }
        } catch (e) {
            console.error('Failed to fetch social feeds', e)
            setTweets(DEMO_TWEETS)
        } finally {
            setRefreshing(false)
        }
    }

    useEffect(() => {
        if (selectedFilmId) fetchSocialComments()
    }, [selectedFilmId])

    // Trigger Scraper — passes film_title so the backend can run collection
    const triggerCollection = async () => {
        if (!selectedFilmId) return
        setCollecting(true)
        try {
            const title = selectedFilm?.title || ''
            const trailerUrl = selectedFilm?.trailer_url || ''
            const params = new URLSearchParams({ film_title: title, trailer_url: trailerUrl })
            const r = await authFetch(`${API}/social/${selectedFilmId}/collect?${params}`, { method: 'POST' })
            if (r.ok) {
                showToast('Social data collection triggered! Feed will refresh in 5s.', 'success')
                setTimeout(() => fetchSocialComments(), 5000)
            } else {
                const err = await r.json().catch(() => ({}))
                showToast(err.detail || 'Collection failed. Check your permissions.', 'error')
            }
        } catch (e) {
            console.error('Trigger failed', e)
            showToast('Network error — could not trigger scraper.', 'error')
        } finally {
            setCollecting(false)
        }
    }

    const runSentimentAnalysis = async () => {
        if (!inputText.trim()) return
        setAnalyzing(true)
        try {
            const comments = inputText.split('\n').map(c => c.trim()).filter(Boolean).join(',')
            const r = await authFetch(`${API}/sentiment-analysis?comments=${encodeURIComponent(comments)}`)
            if (!r.ok) throw new Error('API error')
            const result = await r.json()
            setMlResult(result)

            // Add analyzed comments to view with per-comment sentiment
            const isPos = (result.sentiment_label || '').toLowerCase().includes('positive')
            const isNeg = (result.sentiment_label || '').toLowerCase().includes('negative')
            const newTweets = inputText.split('\n').filter(Boolean).slice(0, 5).map((text, i) => {
                const sev = isPos ? 'positive' : isNeg ? 'negative' : 'neutral'
                return { id: Date.now() + i, user: '@analyzed_input', text: text.trim(), severity: sev, time: 'just now' }
            })
            setTweets(prev => [...newTweets, ...prev.slice(0, 8)])
        } catch (e) {
            console.error(e)
            showToast('Sentiment analysis failed. Check the backend.', 'error')
        } finally {
            setAnalyzing(false)
        }
    }

    const pos = tweets.filter(t => t.severity === 'positive').length
    const neu = tweets.filter(t => t.severity === 'neutral').length
    const neg = tweets.filter(t => t.severity === 'negative').length
    const total = Math.max(tweets.length, 1)

    const hype = mlResult?.hype_score ?? Math.round((pos / total) * 74 + 20)

    const sentimentData = {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{ data: [pos, neu, neg], backgroundColor: ['#10B981', '#F5C842', '#EF4444'], borderWidth: 0, hoverOffset: 8 }]
    }

    const filtered = filter === 'all' ? tweets : tweets.filter(t => t.severity === filter)

    // Determine color for ML result label
    const getLabelColor = (label = '') => {
        const l = label.toLowerCase()
        if (l.includes('positive')) return '#10B981'
        if (l.includes('negative')) return '#EF4444'
        return '#F5C842'
    }

    return (
        <div className="page sentiment-page" style={{ background: 'var(--bg-primary)' }}>
            <div className="orb orb-cyan" style={{ width: 400, height: 400, top: 0, right: -100 }} />
            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40, paddingBottom: 60 }}>

                <div className="flex items-center justify-between mb-32">
                    <div>
                        <div className="section-label">Real-Time Sentiment Monitoring</div>
                        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800, marginBottom: 4 }}>Dynamic Social Feeds</h1>
                        <p className="text-secondary">Connected to Twitter/X, YouTube & Google Trends for live audience feedback.</p>
                    </div>
                    <div className="flex gap-12" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
                        <select className="form-select form-select-sm" value={selectedFilmId} onChange={e => setSelectedFilmId(e.target.value)}>
                            <option value="">Select Film...</option>
                            {films.map(f => (<option key={f.film_id} value={f.film_id}>{f.title}</option>))}
                        </select>
                        {(user?.role === 'admin' || user?.role === 'producer') && (
                            <button className="btn btn-purple btn-sm" onClick={triggerCollection} disabled={collecting || !selectedFilmId}>
                                {collecting ? <RefreshCw size={14} className="spin" /> : <Zap size={14} />}
                                {collecting ? 'Collecting...' : 'Trigger Scraper'}
                            </button>
                        )}
                        <button className="btn btn-outline btn-sm" onClick={() => fetchSocialComments()} disabled={refreshing}>
                            <RefreshCw size={14} className={refreshing ? 'spin' : ''} /> {refreshing ? 'Refreshing...' : 'Refresh Feed'}
                        </button>
                    </div>
                </div>

                {/* Toast notification */}
                <AnimatePresence>
                    {toast && (
                        <div style={{ marginBottom: 16 }}>
                            <Toast toast={toast} />
                        </div>
                    )}
                </AnimatePresence>

                {/* ML Input Panel */}
                <motion.div className="glass-card p-28 mb-24" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="flex items-center gap-8 mb-16">
                        <Brain size={16} color="#F5C842" />
                        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem' }}>Manual ML Analysis Override</span>
                    </div>
                    <textarea
                        style={{ width: '100%', minHeight: 100, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: 'var(--text-primary)', fontFamily: 'Inter', fontSize: '0.87rem', padding: '12px 14px', resize: 'vertical', outline: 'none', boxSizing: 'border-box' }}
                        placeholder={"Type or paste comments (one per line) to analyze their sentiment..."}
                        value={inputText}
                        onChange={e => setInputText(e.target.value)}
                    />
                    <div className="flex gap-12 mt-12" style={{ flexWrap: 'wrap' }}>
                        <button className="btn btn-primary btn-sm" onClick={runSentimentAnalysis} disabled={analyzing || !inputText.trim()}>
                            {analyzing ? <RefreshCw size={14} className="spin" /> : <Send size={14} />} {analyzing ? 'Analyzing...' : 'Analyze Now'}
                        </button>
                        {inputText && (
                            <button className="btn btn-outline btn-sm" onClick={() => { setInputText(''); setMlResult(null) }}>
                                Clear
                            </button>
                        )}
                    </div>
                </motion.div>

                {mlResult && (
                    <motion.div className="glass-card p-28 mb-24" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} style={{ borderColor: 'rgba(167, 139, 250, 0.3)', background: 'rgba(167, 139, 250, 0.05)' }}>
                        <div className="section-label mb-12">Batch Analysis Summary</div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 20 }}>
                            <div className="stat-item">
                                <div className="text-muted text-xs">Hype Score</div>
                                <div className="text-xl font-black grad-text-gold">{mlResult.hype_score}</div>
                            </div>
                            <div className="stat-item">
                                <div className="text-muted text-xs">Primary Sentiment</div>
                                <div className="text-xl font-black" style={{ color: getLabelColor(mlResult.sentiment_label) }}>{mlResult.sentiment_label}</div>
                            </div>
                            <div className="stat-item">
                                <div className="text-muted text-xs">Positive</div>
                                <div className="text-xl font-black" style={{ color: '#10B981' }}>{mlResult.positive_pct}%</div>
                            </div>
                            <div className="stat-item">
                                <div className="text-muted text-xs">Negative</div>
                                <div className="text-xl font-black" style={{ color: '#EF4444' }}>{mlResult.negative_pct}%</div>
                            </div>
                            {mlResult.top_keywords?.length > 0 && (
                                <div className="stat-item" style={{ gridColumn: '1 / -1' }}>
                                    <div className="text-muted text-xs mb-8">Top Keywords</div>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                        {mlResult.top_keywords.map(kw => (
                                            <span key={kw} style={{ padding: '3px 10px', borderRadius: 20, background: 'rgba(167,139,250,0.15)', border: '1px solid rgba(167,139,250,0.3)', fontSize: '0.78rem', color: '#A78BFA' }}>{kw}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* Score & Gauge Row */}
                <div className="sentiment-top mb-24">
                    <div className="sentiment-stats-col">
                        {[
                            { icon: Heart, label: 'Positive', count: pos, pct: Math.round(pos / total * 100), color: '#10B981' },
                            { icon: Minus, label: 'Neutral', count: neu, pct: Math.round(neu / total * 100), color: '#F5C842' },
                            { icon: ThumbsDown, label: 'Negative', count: neg, pct: Math.round(neg / total * 100), color: '#EF4444' },
                        ].map(s => (
                            <motion.div key={s.label} className="sentiment-stat glass-card" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
                                <div className="sentiment-stat-icon" style={{ background: `${s.color}18`, border: `1px solid ${s.color}40`, color: s.color }}>
                                    <s.icon size={18} />
                                </div>
                                <div>
                                    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem', color: s.color }}>{s.count}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>{s.label} ({s.pct}%)</div>
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    <div className="glass-card gauge-card">
                        <HypeGauge score={hype} />
                        <div className="divider" style={{ margin: '16px 0' }} />
                        <div style={{ height: 180 }}>
                            <Doughnut data={sentimentData} options={{ responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { color: '#94A3B8', font: { family: 'Inter', size: 10 }, boxWidth: 8 } } } }} />
                        </div>
                    </div>
                </div>

                {/* Tweet Feed */}
                <motion.div className="glass-card p-28" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="flex items-center justify-between mb-20">
                        <div className="flex items-center gap-12">
                            <MessageSquare size={18} color="#06B6D4" />
                            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem' }}>
                                Social Feed Insights
                                <span style={{ marginLeft: 8, fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                                    {tweets.length} posts
                                </span>
                            </h3>
                        </div>
                        <div className="feed-filters">
                            {['all', 'positive', 'neutral', 'negative'].map(f => (
                                <button key={f} className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-outline'}`} onClick={() => setFilter(f)} style={{ textTransform: 'capitalize' }}>{f}</button>
                            ))}
                        </div>
                    </div>

                    {filtered.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px 0', opacity: 0.5 }}>
                            No {filter !== 'all' ? filter : ''} comments found.
                            {filter !== 'all' && <span> <button className="btn btn-outline btn-sm" style={{ marginLeft: 8 }} onClick={() => setFilter('all')}>Show All</button></span>}
                        </div>
                    ) : (
                        <div className="tweet-feed">
                            <AnimatePresence>
                                {filtered.map((t, i) => (
                                    <motion.div key={t.id} className={`tweet-card glass-card tweet-${t.severity}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                                        <div className="tweet-top">
                                            <div className="flex items-center gap-8">
                                                <div className="tweet-avatar">{t.user[1].toUpperCase()}</div>
                                                <span className="tweet-user">{t.user}</span>
                                            </div>
                                            <div className="flex items-center gap-8">
                                                <span style={{
                                                    padding: '2px 8px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 600, textTransform: 'capitalize',
                                                    background: t.severity === 'positive' ? 'rgba(16,185,129,0.15)' : t.severity === 'negative' ? 'rgba(239,68,68,0.15)' : 'rgba(245,200,66,0.15)',
                                                    color: t.severity === 'positive' ? '#10B981' : t.severity === 'negative' ? '#EF4444' : '#F5C842',
                                                }}>{t.severity}</span>
                                                <span className="text-muted text-xs">{t.time}</span>
                                            </div>
                                        </div>
                                        <p className="tweet-text">{t.text}</p>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    )}
                </motion.div>
            </div>
        </div>
    )
}
