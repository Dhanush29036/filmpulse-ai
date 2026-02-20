import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Map as MapIcon, Users, Trophy, Sparkles, TrendingUp, ChevronRight, Globe, Award, Share2, Instagram, Twitter, Youtube, Facebook, MessageCircle, RefreshCw } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './MarketIntelligence.css'

const API = 'http://localhost:8000/api/v1'

export default function MarketIntelligence() {
    const { authFetch } = useAuth()
    const [films, setFilms] = useState([])
    const [selectedFilmId, setSelectedFilmId] = useState('')
    const [loading, setLoading] = useState(false)
    const [data, setData] = useState(null)
    const [activeTab, setActiveTab] = useState('heatmap')
    const [platform, setPlatform] = useState('Instagram')

    // Fetch user's films for the dropdown
    useEffect(() => {
        authFetch(`${API}/films`)
            .then(r => r.json())
            .then(d => {
                setFilms(d)
                if (d.length > 0) setSelectedFilmId(d[0].id)
            })
            .catch(console.error)
    }, [])

    const fetchIntelligence = async () => {
        if (!selectedFilmId) return
        setLoading(true)
        try {
            const r = await authFetch(`${API}/advanced/market-intelligence?film_id=${selectedFilmId}`)
            if (r.ok) setData(await r.json())
        } catch (e) {
            console.error('Failed to fetch intelligence', e)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (selectedFilmId) fetchIntelligence()
    }, [selectedFilmId])

    const container = {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.1 } }
    }

    const item = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 }
    }

    const platformIcons = { Instagram, Twitter, Youtube, Facebook, MessageCircle }

    return (
        <div className="page intelligence-page">
            <div className="orb orb-purple" style={{ width: 600, height: 600, top: -200, left: -200 }} />
            <div className="orb orb-gold" style={{ width: 400, height: 400, bottom: -100, right: -100 }} />

            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40 }}>
                {/* Header */}
                <div className="flex items-center justify-between mb-32">
                    <div>
                        <div className="section-label">Phase 8 Advanced ML</div>
                        <h1 className="dash-title">Market Intelligence Engine</h1>
                        <p className="text-secondary">Strategic insights from regional demand, competitor similarity, and festival scoring.</p>
                    </div>
                    <div className="flex gap-16 items-center">
                        <div className="form-group mb-0">
                            <select
                                className="form-select"
                                value={selectedFilmId}
                                onChange={e => setSelectedFilmId(e.target.value)}
                                style={{ minWidth: 200 }}
                            >
                                <option value="">Select a Film...</option>
                                {films.map(f => <option key={f.id} value={f.id}>{f.title}</option>)}
                            </select>
                        </div>
                        <button className="btn btn-outline btn-sm" onClick={fetchIntelligence} disabled={loading}>
                            <RefreshCw size={14} className={loading ? 'spin' : ''} />
                        </button>
                    </div>
                </div>

                {!data && !loading && (
                    <div style={{ textAlign: 'center', padding: '100px 0', color: 'var(--text-muted)' }}>
                        <Brain size={48} style={{ margin: '0 auto 20px', opacity: 0.2 }} />
                        <p>Select a film to generate advanced market intelligence.</p>
                    </div>
                )}

                {loading && (
                    <div style={{ textAlign: 'center', padding: '100px 0' }}>
                        <div className="spinner" style={{ margin: '0 auto 20px' }} />
                        <p className="text-secondary">Generating Intelligence Grid... Calling Heatmap + Competitor + Festival Engines</p>
                    </div>
                )}

                {data && !loading && (
                    <motion.div className="intelligence-grid" variants={container} initial="hidden" animate="show">

                        {/* Heatmap Section */}
                        <motion.div className="glass-card heatmap-card overflow-hidden" variants={item}>
                            <div className="flex items-center gap-12 p-24 pb-0">
                                <div className="p-8 rounded-lg" style={{ background: 'rgba(245, 200, 66, 0.1)', color: '#F5C842' }}>
                                    <MapIcon size={20} />
                                </div>
                                <h3 className="card-subtitle">Regional Audience Heatmap</h3>
                            </div>

                            <div className="map-container">
                                {/* SVG India Map Placeholder / Stylized Visual */}
                                <div className="map-placeholder">
                                    <Globe size={120} />
                                    <p className="font-display font-bold mt-16 text-xl">India Audience Density</p>
                                    <p style={{ fontSize: '0.8rem' }}>State-Level Intensity Mapping (35 Regions)</p>
                                </div>

                                <div className="heatmap-overlay">
                                    <div className="font-bold font-display text-sm mb-4">Primary Growth Markets</div>
                                    <div className="flex flex-col gap-4">
                                        {data.regional_heatmap.primary_markets.slice(0, 3).map(m => (
                                            <div key={m} className="flex items-center justify-between gap-24">
                                                <span className="text-xs">{m}</span>
                                                <div className="badge badge-gold" style={{ fontSize: '0.6rem' }}>High Growth</div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="intensity-legend">
                                        <div className="legend-item"><div className="legend-color" style={{ background: '#F5C842' }} /> High Affinity</div>
                                        <div className="legend-item"><div className="legend-color" style={{ background: '#A78BFA' }} /> Target Growth</div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        <div className="heatmap-sidebar">
                            <motion.div className="glass-card p-24" variants={item}>
                                <div className="text-muted text-xs mb-8">Best Zone</div>
                                <div className="font-display font-black text-2xl grad-text-purple">{data.regional_heatmap.best_zone}</div>
                                <p className="text-xs text-muted mt-8">Highest genre-language synergy discovered in this cluster.</p>
                            </motion.div>

                            <motion.div className="glass-card p-24 flex-1" variants={item}>
                                <h4 className="text-sm font-bold mb-16">Regional Market Scores</h4>
                                <div className="flex flex-col gap-12">
                                    {data.regional_heatmap.states.slice(0, 5).map(s => (
                                        <div key={s.name} className="flex flex-col gap-4">
                                            <div className="flex justify-between text-xs">
                                                <span>{s.name}</span>
                                                <span className="font-bold">{s.total_score}</span>
                                            </div>
                                            <div className="progress-bar">
                                                <div className="progress-fill" style={{ width: `${s.total_score}%`, background: s.total_score > 70 ? '#F5C842' : '#8B5CF6' }} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        </div>

                        {/* Competitor Engine */}
                        <motion.div className="glass-card competitor-card p-24" variants={item}>
                            <div className="flex items-center justify-between mb-16">
                                <div className="flex items-center gap-12">
                                    <div className="p-8 rounded-lg" style={{ background: 'rgba(6, 182, 212, 0.1)', color: '#06B6D4' }}>
                                        <Users size={20} />
                                    </div>
                                    <div>
                                        <h3 className="card-subtitle">Competitor Comparison Engine</h3>
                                        <p className="text-xs text-muted">Similar films based on Budget, Genre, and Cast Power</p>
                                    </div>
                                </div>
                                <div className="badge badge-purple">Tier: {data.competitor_analysis.market_position}</div>
                            </div>

                            <div className="competitor-table-wrap">
                                <table className="competitor-table">
                                    <thead>
                                        <tr>
                                            <th>Comparable Film</th>
                                            <th>Genre / Year</th>
                                            <th>Budget / BO</th>
                                            <th>Similarity Score</th>
                                            <th>Market Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.competitor_analysis.comparable_films.map(comp => (
                                            <tr key={comp.title}>
                                                <td><div className="comp-film-title">{comp.title}</div></td>
                                                <td><div className="text-xs">{comp.genre} · {comp.release_year}</div></td>
                                                <td><div className="text-xs">₹{comp.budget_cr}Cr / ₹{comp.box_office_cr}Cr</div></td>
                                                <td>
                                                    <div className="flex items-center gap-8">
                                                        <div className="progress-bar" style={{ width: 60 }}><div className="progress-fill" style={{ width: `${comp.similarity_score * 100}%`, background: '#06B6D4' }} /></div>
                                                        <span className="text-xs font-bold">{Math.round(comp.similarity_score * 100)}%</span>
                                                    </div>
                                                </td>
                                                <td>
                                                    <span className="similarity-badge" style={{
                                                        background: comp.box_office_cr > comp.budget_cr * 2 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                                                        color: comp.box_office_cr > comp.budget_cr * 2 ? '#10B981' : '#EF4444',
                                                        border: `1px solid ${comp.box_office_cr > comp.budget_cr * 2 ? '#10B98140' : '#EF444440'}`
                                                    }}>
                                                        {comp.box_office_cr > comp.budget_cr * 2 ? 'Blockbuster' : 'Average'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </motion.div>

                        {/* Festival Scorer */}
                        <motion.div className="section-label mt-24" style={{ gridColumn: 'span 12' }}>Festival Success Probability</motion.div>
                        <motion.div className="festival-grid" variants={container}>
                            {data.festival_scoring.festivals.map(fest => (
                                <motion.div key={fest.name} className="glass-card festival-item" variants={item}>
                                    <div className="flex items-center justify-between">
                                        <div className="font-display font-bold text-sm">{fest.name}</div>
                                        <Award size={18} color="#F5C842" />
                                    </div>
                                    <div className="fest-prob-wrap">
                                        <div>
                                            <div className="text-muted text-xs">Selection Probability</div>
                                            <div className="fest-score grad-text-gold">{fest.selection_prob}%</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-muted text-xs">Win Prob.</div>
                                            <div style={{ fontWeight: 800 }}>{fest.win_prob}%</div>
                                        </div>
                                    </div>
                                    <div className="p-12 rounded-lg bg-white/5 border border-white/10 text-xs italic">
                                        "{fest.strategy_tip}"
                                    </div>
                                </motion.div>
                            ))}
                        </motion.div>

                        {/* Creative Hub */}
                        <motion.div className="section-label mt-32" style={{ gridColumn: 'span 12' }}>Creative & Tagline Hub</motion.div>
                        <div className="creative-hub">
                            <motion.div className="glass-card p-24" variants={item}>
                                <div className="flex items-center gap-12 mb-20">
                                    <Sparkles size={18} color="#F5C842" />
                                    <h3 className="card-subtitle">AI Poster Taglines</h3>
                                </div>
                                <div className="tagline-list">
                                    {Object.entries(data.taglines).map(([tone, lines]) => (
                                        <div key={tone} className="mb-16">
                                            <div className="text-xs uppercase tracking-widest text-muted mb-8 font-bold">{tone} Tone</div>
                                            {lines.map((l, idx) => (
                                                <div key={idx} className="tagline-card mb-8 text-sm font-display leading-tight">{l}</div>
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </motion.div>

                            <motion.div className="glass-card p-24 caption-card" variants={item}>
                                <div className="flex items-center gap-12 mb-20">
                                    <Share2 size={18} color="#8B5CF6" />
                                    <h3 className="card-subtitle">Marketing Captions</h3>
                                </div>
                                <div className="platform-tabs">
                                    {['Instagram', 'Twitter', 'YouTube', 'Facebook', 'WhatsApp'].map(p => (
                                        <div
                                            key={p}
                                            className={`platform-tab ${platform === p ? 'active' : ''}`}
                                            onClick={() => setPlatform(p)}
                                        >
                                            {p}
                                        </div>
                                    ))}
                                </div>
                                <AnimatePresence mode="wait">
                                    <motion.div
                                        key={platform}
                                        initial={{ opacity: 0, x: 10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -10 }}
                                        className="platform-content"
                                    >
                                        {data.marketing_captions.platforms[platform]?.map((c, i) => (
                                            <div key={i} className="glass-card mb-16 p-20" style={{ background: 'rgba(255,255,255,0.02)' }}>
                                                <div className="flex items-center gap-8 mb-12 text-muted">
                                                    {platform === 'Instagram' && <Instagram size={14} />}
                                                    {platform === 'Twitter' && <Twitter size={14} />}
                                                    {platform === 'YouTube' && <Youtube size={14} />}
                                                    {platform === 'Facebook' && <Facebook size={14} />}
                                                    {platform === 'WhatsApp' && <MessageCircle size={14} />}
                                                    <span className="text-xs font-bold">{platform} Variation {i + 1}</span>
                                                </div>
                                                <p className="text-sm leading-relaxed mb-12">{c.hook}</p>
                                                <p className="text-sm leading-relaxed mb-12" style={{ color: 'var(--text-muted)' }}>{c.body}</p>
                                                <div className="flex flex-wrap gap-4 mt-12">
                                                    {c.hashtags.map(h => <span key={h} className="text-xs text-purple-400">#{h}</span>)}
                                                </div>
                                            </div>
                                        ))}
                                    </motion.div>
                                </AnimatePresence>
                            </motion.div>
                        </div>

                    </motion.div>
                )}
            </div>
        </div>
    )
}
