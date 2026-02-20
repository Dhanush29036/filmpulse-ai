import { useState } from 'react'
import { motion } from 'framer-motion'
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { Doughnut, Bar } from 'react-chartjs-2'
import { DollarSign, TrendingUp, Target, Zap, ArrowRight, RefreshCw, Star } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './CampaignOptimizer.css'

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const API = 'http://localhost:8000/api/v1'

const CHANNEL_COLORS = {
    'YouTube Ads': '#EF4444', 'Instagram': '#8B5CF6',
    'Google Ads': '#3B82F6', 'TV Spots': '#F5C842',
    'Outdoor': '#10B981', 'Influencers': '#06B6D4',
}

const doughnutOpts = {
    responsive: true, maintainAspectRatio: false, cutout: '68%',
    plugins: {
        legend: { position: 'right', labels: { color: '#94A3B8', font: { family: 'Inter', size: 11 }, boxWidth: 10, padding: 12 } },
        tooltip: { backgroundColor: '#0D1526', borderColor: '#ffffff18', borderWidth: 1 }
    }
}

const barOpts = {
    responsive: true, maintainAspectRatio: false, indexAxis: 'y',
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#0D1526', borderColor: '#ffffff18', borderWidth: 1 } },
    scales: {
        x: { grid: { color: '#ffffff08' }, ticks: { color: '#94A3B8', callback: v => `${v}x` } },
        y: { grid: { display: false }, ticks: { color: '#94A3B8', font: { family: 'Inter', size: 11 } } },
    }
}

export default function CampaignOptimizer() {
    const { authFetch } = useAuth()
    const [form, setForm] = useState({ budget: 5000000, region: 'Pan-India', genre: 'Action' })
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const optimize = async () => {
        setLoading(true); setError('')
        try {
            const q = new URLSearchParams({ total_budget: form.budget, target_region: form.region, genre: form.genre })
            const r = await authFetch(`${API}/budget-optimization?${q}`)
            if (!r.ok) throw new Error('Optimization failed')
            setResult(await r.json())
        } catch (e) { setError(e.message) }
        finally { setLoading(false) }
    }

    const channels = result?.channels || []
    const colors = channels.map(c => CHANNEL_COLORS[c.name] || '#94A3B8')

    const doughnut = {
        labels: channels.map(c => c.name),
        datasets: [{ data: channels.map(c => c.allocation_pct), backgroundColor: colors, borderWidth: 0, hoverOffset: 10 }]
    }
    const roiBar = {
        labels: channels.map(c => c.name),
        datasets: [{ data: channels.map(c => c.estimated_roi), backgroundColor: colors.map(c => `${c}CC`), borderRadius: 6, borderWidth: 0 }]
    }


    return (
        <div className="page campaign-page" style={{ background: 'var(--bg-primary)' }}>
            <div className="orb orb-gold" style={{ width: 400, height: 400, top: 50, left: -100 }} />
            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40, paddingBottom: 60 }}>

                <div className="mb-32">
                    <div className="section-label">Campaign Optimizer</div>
                    <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800, marginBottom: 4 }}>Budget Intelligence Engine</h1>
                    <p className="text-secondary">Input your marketing budget and get AI-optimized channel allocation with ROI projections.</p>
                </div>

                {/* Input Panel */}
                <motion.div className="glass-card p-32 mb-24" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="campaign-form">
                        <div className="form-group">
                            <label className="form-label">Total Marketing Budget (₹)</label>
                            <input type="number" className="form-input" value={form.budget}
                                onChange={e => setForm({ ...form, budget: +e.target.value })} step={500000} min={100000} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Target Region</label>
                            <select className="form-select" value={form.region} onChange={e => setForm({ ...form, region: e.target.value })}>
                                {['Pan-India', 'North India', 'South India', 'Metro Cities', 'Tier 2 Cities'].map(r => <option key={r}>{r}</option>)}
                            </select>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Film Genre</label>
                            <select className="form-select" value={form.genre} onChange={e => setForm({ ...form, genre: e.target.value })}>
                                {['Action', 'Romance', 'Thriller', 'Comedy', 'Drama', 'Horror'].map(g => <option key={g}>{g}</option>)}
                            </select>
                        </div>
                        <div className="form-group" style={{ alignSelf: 'flex-end' }}>
                            <button className="btn btn-primary w-full" onClick={optimize} disabled={loading}>
                                {loading ? <><RefreshCw size={16} className="spin" /> Computing…</> : <><Zap size={16} /> Optimize Budget</>}
                            </button>
                        </div>
                    </div>
                    {error && <div style={{ marginTop: 12, color: '#EF4444', fontSize: '0.85rem' }}>⚠ {error}</div>}
                </motion.div>

                {/* Summary Stats */}
                {result && (
                    <div className="campaign-stats mb-24">
                        {[
                            { icon: DollarSign, label: 'Total Budget', value: `₹${(form.budget / 1e6).toFixed(1)}M`, color: '#F5C842' },
                            { icon: TrendingUp, label: 'Blended ROI', value: `${result.blended_roi}x`, color: '#10B981' },
                            { icon: Target, label: 'Top Channel', value: result.top_channel, color: '#8B5CF6' },
                            { icon: Star, label: 'Predicted Return', value: `₹${(result.total_predicted_return / 1e6).toFixed(1)}M`, color: '#06B6D4' },
                        ].map((s, i) => (
                            <motion.div key={s.label} className="campaign-stat glass-card" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
                                <div className="stat-icon" style={{ background: `${s.color}18`, border: `1px solid ${s.color}40`, color: s.color }}>
                                    <s.icon size={18} />
                                </div>
                                <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
                                <div className="stat-label">{s.label}</div>
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* Charts */}
                {result && (
                    <div className="campaign-charts mb-24">
                        <motion.div className="glass-card p-28" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', marginBottom: 20 }}>Budget Allocation by Channel</h3>
                            <div style={{ height: 280 }}>
                                <Doughnut data={doughnut} options={doughnutOpts} />
                            </div>
                        </motion.div>

                        <motion.div className="glass-card p-28" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
                            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', marginBottom: 20 }}>Projected ROI per Channel</h3>
                            <div style={{ height: 280 }}>
                                <Bar data={roiBar} options={barOpts} />
                            </div>
                        </motion.div>
                    </div>
                )}

                {/* Channel Table */}
                {result && (
                    <motion.div className="glass-card p-32 mb-16" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                        <div className="flex items-center justify-between mb-20">
                            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem' }}>Detailed Channel Plan — Ridge Regression Model</h3>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>🤖 {result.model}</div>
                        </div>
                        <div className="channel-table">
                            <div className="channel-header">
                                <span>Channel</span><span>Allocation %</span>
                                <span>Budget (₹)</span><span>Est. ROI</span><span>Status</span>
                            </div>
                            {channels.map(c => (
                                <div key={c.name} className="channel-row">
                                    <div className="flex items-center gap-10">
                                        <div className="channel-dot" style={{ background: CHANNEL_COLORS[c.name] || '#94A3B8' }} />
                                        <span className="font-display" style={{ fontWeight: 600, fontSize: '0.9rem' }}>{c.name}</span>
                                    </div>
                                    <div>
                                        <div className="progress-bar mt-0" style={{ marginTop: 0 }}>
                                            <div className="progress-fill" style={{ width: `${c.allocation_pct}%`, background: CHANNEL_COLORS[c.name] || '#94A3B8' }} />
                                        </div>
                                        <span className="text-sm" style={{ color: CHANNEL_COLORS[c.name], fontWeight: 700 }}>{c.allocation_pct}%</span>
                                    </div>
                                    <span className="font-display font-bold text-sm">₹{(c.budget_inr / 1000).toFixed(0)}K</span>
                                    <span className="font-display font-bold" style={{ color: c.estimated_roi > 2 ? '#10B981' : c.estimated_roi > 1.5 ? '#F5C842' : '#94A3B8' }}>{c.estimated_roi}x</span>
                                    <span>{c.recommended ? <span className="badge badge-green" style={{ fontSize: '0.7rem' }}>⭐ Best</span> : ''}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}

                {!result && !loading && (
                    <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
                        Click "Optimize Budget" to get AI-powered channel allocation from the Ridge Regression model.
                    </div>
                )}
                {loading && (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <RefreshCw size={32} className="spin" style={{ color: '#F5C842', margin: '0 auto 16px', display: 'block' }} />
                        <p style={{ color: 'var(--text-muted)' }}>Running Ridge Regression model…</p>
                    </div>
                )}
            </div>
        </div>
    )
}
