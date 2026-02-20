import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Film, PlusCircle, Trash2, Zap, TrendingUp, Star, DollarSign, RefreshCw, ChevronRight, Calendar, Globe } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const API = 'http://localhost:8000/api/v1'

const GENRES = ['Action', 'Romance', 'Thriller', 'Comedy', 'Drama', 'Horror']
const LANGS = ['Hindi', 'English', 'Tamil', 'Telugu', 'Bengali', 'Marathi']
const PLATFORMS = ['Theatre', 'OTT', 'Both']

const gradeColor = { A: '#10B981', B: '#F5C842', C: '#06B6D4', D: '#EF4444' }

function FilmCard({ film, onDelete }) {
    const gc = gradeColor[film.grade] || '#94A3B8'
    return (
        <motion.div layout initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
            className="glass-card" style={{ padding: 24, position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: `linear-gradient(90deg, ${gc}, transparent)` }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div>
                    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.05rem', marginBottom: 4 }}>{film.title}</div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <span className="badge badge-gold" style={{ fontSize: '0.72rem' }}>{film.genre}</span>
                        <span className="badge" style={{ fontSize: '0.72rem', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>{film.language}</span>
                        <span className="badge" style={{ fontSize: '0.72rem', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>{film.platform}</span>
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.5rem', color: gc }}>{film.grade || '?'}</div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Grade</div>
                    </div>
                    <button className="btn btn-outline btn-sm" onClick={() => onDelete(film.film_id)} style={{ color: '#EF4444', borderColor: 'rgba(239,68,68,0.3)', padding: '6px 10px' }}>
                        <Trash2 size={14} />
                    </button>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 16 }}>
                {[
                    { label: 'Discoverability', value: film.discoverability, color: '#F5C842', icon: Star },
                    { label: 'Hype Score', value: film.hype_score, color: '#8B5CF6', icon: Zap },
                    { label: 'Revenue Est.', value: `₹${film.revenue_estimate}M`, color: '#10B981', icon: DollarSign },
                    { label: 'Budget', value: `₹${(film.budget / 1e6).toFixed(1)}M`, color: '#06B6D4', icon: TrendingUp },
                ].map(m => (
                    <div key={m.label} style={{ textAlign: 'center' }}>
                        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.1rem', color: m.color }}>{m.value ?? '—'}</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{m.label}</div>
                    </div>
                ))}
            </div>

            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                {film.status && (
                    <span className="badge badge-green" style={{ fontSize: '0.7rem' }}>✓ {film.status}</span>
                )}
                {film.release_date && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        <Calendar size={12} /> {film.release_date}
                    </span>
                )}
                {film.director && (
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Dir: {film.director}</span>
                )}
            </div>
        </motion.div>
    )
}

export default function FilmsPage() {
    const { authFetch, user } = useAuth()
    const [films, setFilms] = useState([])
    const [loadingFilms, setLoadingFilms] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')
    const [form, setForm] = useState({
        title: '', genre: 'Action', language: 'Hindi', budget: 5000000,
        release_date: '', platform: 'Both', cast_popularity: 7.0, director: '', production_house: ''
    })

    const fetchFilms = async () => {
        setLoadingFilms(true)
        try {
            const r = await authFetch(`${API}/films`)
            const data = await r.json()
            setFilms(Array.isArray(data) ? data : data.films || [])
        } catch (e) { console.error(e) }
        finally { setLoadingFilms(false) }
    }

    useEffect(() => { fetchFilms() }, [])

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!form.title.trim()) { setError('Title is required'); return }
        setSubmitting(true); setError('')
        try {
            const r = await authFetch(`${API}/upload-film`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            })
            if (!r.ok) { const d = await r.json(); throw new Error(d.detail || 'Upload failed') }
            const newFilm = await r.json()
            setSuccess(`"${form.title}" registered and analyzed by AI! Grade: ${newFilm.grade}`)
            setShowForm(false)
            setForm({ title: '', genre: 'Action', language: 'Hindi', budget: 5000000, release_date: '', platform: 'Both', cast_popularity: 7.0, director: '', production_house: '' })
            fetchFilms()
            setTimeout(() => setSuccess(''), 5000)
        } catch (e) { setError(e.message) }
        finally { setSubmitting(false) }
    }

    const handleDelete = async (film_id) => {
        if (!window.confirm('Remove this film?')) return
        try {
            await authFetch(`${API}/films/${film_id}`, { method: 'DELETE' })
            setFilms(prev => prev.filter(f => f.film_id !== film_id))
        } catch (e) { setError(e.message) }
    }

    return (
        <div className="page" style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
            <div className="orb orb-gold" style={{ width: 400, height: 400, top: 0, right: -100 }} />
            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40, paddingBottom: 60 }}>

                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
                    <div>
                        <div className="section-label">My Films</div>
                        <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '2rem', marginBottom: 4 }}>
                            Film Portfolio
                        </h1>
                        <p className="text-secondary">
                            Register your films and get instant AI-driven discoverability scores, revenue estimates, and marketing grades.
                        </p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowForm(v => !v)}>
                        <PlusCircle size={16} /> {showForm ? 'Cancel' : 'Register New Film'}
                    </button>
                </div>

                {/* Messages */}
                {success && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                        style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 10, padding: '12px 16px', color: '#10B981', marginBottom: 20, fontWeight: 600, fontSize: '0.88rem' }}>
                        🎬 {success}
                    </motion.div>
                )}
                {error && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                        style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '12px 16px', color: '#EF4444', marginBottom: 20, fontSize: '0.88rem' }}>
                        ⚠ {error}
                    </motion.div>
                )}

                {/* Register Form */}
                <AnimatePresence>
                    {showForm && (
                        <motion.div className="glass-card" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                            style={{ marginBottom: 24, overflow: 'hidden', padding: 32 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
                                <Film size={18} color="#F5C842" />
                                <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>Register New Film — AI Analysis on Submit</h3>
                            </div>
                            <form onSubmit={handleSubmit}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 20 }}>
                                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                        <label className="form-label">Film Title *</label>
                                        <input className="form-input" placeholder="e.g. Tiger Zinda Hai" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
                                    </div>
                                    {[
                                        { key: 'genre', label: 'Genre', type: 'select', opts: GENRES },
                                        { key: 'language', label: 'Language', type: 'select', opts: LANGS },
                                        { key: 'platform', label: 'Platform', type: 'select', opts: PLATFORMS },
                                    ].map(f => (
                                        <div key={f.key} className="form-group">
                                            <label className="form-label">{f.label}</label>
                                            <select className="form-select" value={form[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })}>
                                                {f.opts.map(o => <option key={o}>{o}</option>)}
                                            </select>
                                        </div>
                                    ))}
                                    <div className="form-group">
                                        <label className="form-label">Budget (₹)</label>
                                        <input type="number" className="form-input" value={form.budget} step={500000} min={100000} onChange={e => setForm({ ...form, budget: Number(e.target.value) })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Cast Popularity (1–10)</label>
                                        <input type="number" className="form-input" value={form.cast_popularity} step={0.5} min={1} max={10} onChange={e => setForm({ ...form, cast_popularity: Number(e.target.value) })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Release Date</label>
                                        <input type="date" className="form-input" value={form.release_date} onChange={e => setForm({ ...form, release_date: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Director</label>
                                        <input className="form-input" placeholder="Optional" value={form.director} onChange={e => setForm({ ...form, director: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Production House</label>
                                        <input className="form-input" placeholder="Optional" value={form.production_house} onChange={e => setForm({ ...form, production_house: e.target.value })} />
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: 12 }}>
                                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                                        {submitting ? <><RefreshCw size={16} className="spin" /> Analyzing with AI…</> : <><Zap size={16} /> Register & Analyze</>}
                                    </button>
                                    <button type="button" className="btn btn-outline" onClick={() => setShowForm(false)}>Cancel</button>
                                </div>
                            </form>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Films List */}
                {loadingFilms ? (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <RefreshCw size={32} className="spin" style={{ color: '#F5C842', margin: '0 auto 16px', display: 'block' }} />
                        <p style={{ color: 'var(--text-muted)' }}>Loading your film portfolio…</p>
                    </div>
                ) : films.length === 0 ? (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card"
                        style={{ padding: '60px 40px', textAlign: 'center' }}>
                        <Film size={48} style={{ color: 'var(--text-muted)', margin: '0 auto 16px' }} />
                        <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 8 }}>No films registered yet</h3>
                        <p className="text-secondary" style={{ marginBottom: 24 }}>Register your first film and get instant AI-powered insights.</p>
                        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
                            <PlusCircle size={16} /> Register Your First Film
                        </button>
                    </motion.div>
                ) : (
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                            <div className="text-secondary text-sm">{films.length} film{films.length !== 1 ? 's' : ''} in your portfolio</div>
                            <button className="btn btn-outline btn-sm" onClick={fetchFilms}><RefreshCw size={14} /> Refresh</button>
                        </div>
                        <div style={{ display: 'grid', gap: 16 }}>
                            <AnimatePresence>
                                {films.map(f => <FilmCard key={f.film_id} film={f} onDelete={handleDelete} />)}
                            </AnimatePresence>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
