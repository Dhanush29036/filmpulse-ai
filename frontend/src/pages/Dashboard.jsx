import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import { Target, TrendingUp, Zap, DollarSign, Calendar, Film, RefreshCw, Download, Users, Star } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './Dashboard.css'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend, Filler)

const API = 'http://localhost:8000/api/v1'

function ScoreRing({ score, size = 140, label, color = '#F5C842', max = 100 }) {
    const r = size / 2 - 14
    const circ = 2 * Math.PI * r
    const offset = circ - (score / max) * circ
    return (
        <div className="score-ring-wrap" style={{ width: size, height: size }}>
            <svg width={size} height={size}>
                <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
                <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={10}
                    strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.34,1.56,0.64,1)', filter: `drop-shadow(0 0 8px ${color}80)` }} />
            </svg>
            <div className="score-ring-value">
                <div className="score-num" style={{ color }}>{score}</div>
                <div className="score-label">{label}</div>
            </div>
        </div>
    )
}

function MetricCard({ icon: Icon, label, value, unit, sub, color, idx }) {
    return (
        <motion.div className="metric-card glass-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.08 }} style={{ '--accent': color }}>
            <div className="metric-icon" style={{ background: `${color}18`, border: `1px solid ${color}40`, color }}>
                <Icon size={20} />
            </div>
            <div className="metric-label">{label}</div>
            <div className="metric-value" style={{ color }}>{value}<span className="metric-unit">{unit}</span></div>
            <div className="metric-sub">{sub}</div>
        </motion.div>
    )
}

const chartOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#0D1526', borderColor: '#ffffff18', borderWidth: 1 } },
    scales: {
        x: { grid: { color: '#ffffff0a' }, ticks: { color: '#94A3B8', font: { family: 'Inter', size: 11 } } },
        y: { grid: { color: '#ffffff0a' }, ticks: { color: '#94A3B8', font: { family: 'Inter', size: 11 } } },
    }
}

export default function Dashboard() {
    const { authFetch, user } = useAuth()
    const [form, setForm] = useState({ genre: 'Action', budget: 8000000, language: 'Hindi', platform: 'Both', cast_popularity: 7.5, trailer_sentiment: 0.75 })
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const fetchDashboard = async (params = form) => {
        setLoading(true); setError('')
        try {
            const q = new URLSearchParams({
                genre: params.genre, budget: params.budget, language: params.language,
                platform: params.platform, cast_popularity: params.cast_popularity,
                trailer_sentiment: params.trailer_sentiment,
            })
            const r = await authFetch(`${API}/dashboard-summary?${q}`)
            if (!r.ok) throw new Error('Analysis failed')
            setData(await r.json())
        } catch (e) { setError(e.message) }
        finally { setLoading(false) }
    }

    useEffect(() => { fetchDashboard() }, [])

    const handleAnalyze = () => fetchDashboard(form)

    // Build chart data from API response
    const audienceData = data ? {
        labels: Object.keys(data.audience_prediction?.age_group_distribution || { '18-24': 28, '25-34': 35, '35-44': 20, '45+': 17 }),
        datasets: [{
            label: 'Audience %',
            data: Object.values(data.audience_prediction?.age_group_distribution || { '18-24': 28, '25-34': 35, '35-44': 20, '45+': 17 }),
            backgroundColor: ['#8B5CF6', '#F5C842', '#06B6D4', '#10B981', '#EF4444'],
            borderRadius: 8, borderWidth: 0,
        }]
    } : null

    const revEst = data?.audience_prediction?.revenue_estimate || {}
    const revenueData = data ? {
        labels: ['Low', 'Mid', 'High'],
        datasets: [{
            label: 'Revenue (₹M)',
            data: [revEst.low || 0, revEst.mid || 0, revEst.high || 0],
            fill: true,
            borderColor: '#F5C842',
            backgroundColor: 'rgba(245,200,66,0.08)',
            pointBackgroundColor: '#F5C842',
            tension: 0.4,
        }]
    } : null

    const platformData = data?.platform_distribution ? {
        labels: Object.keys(data.platform_distribution),
        datasets: [{
            data: Object.values(data.platform_distribution),
            backgroundColor: ['#EF4444', '#8B5CF6', '#06B6D4', '#3B82F6', '#F5C842', '#10B981'],
            borderWidth: 0, hoverOffset: 8,
        }]
    } : null

    const ds = data?.discoverability_score || 0
    const hype = data?.sentiment?.hype_score || 0
    const revMid = data?.audience_prediction?.revenue_estimate?.mid || 0
    const revFit = Math.min(Math.round((revMid / 1000) * 10), 100)

    const rec = data?.release_recommendation || {}
    const breakdown = data?.discoverability_breakdown || {}
    const gradeColor = { A: '#10B981', B: '#F5C842', C: '#06B6D4', D: '#EF4444' }[data?.discoverability_grade] || '#94A3B8'

    const metrics = [
        { icon: Target, label: 'Discoverability', value: ds, unit: '/100', sub: `Grade: ${data?.discoverability_grade || '…'}`, color: '#F5C842' },
        { icon: TrendingUp, label: 'Revenue Est.', value: `₹${revMid}M`, unit: '', sub: 'Projected box office (mid)', color: '#8B5CF6' },
        { icon: Zap, label: 'Hype Score', value: hype, unit: '/100', sub: data?.sentiment?.sentiment_label || 'Buzz analysis', color: '#06B6D4' },
        { icon: DollarSign, label: 'ROI Potential', value: `${((data?.budget_optimization?.blended_roi || 1.5)).toFixed(1)}x`, unit: '', sub: 'Blended marketing ROI', color: '#10B981' },
        { icon: Calendar, label: 'Best Release', value: rec.window || '…', unit: '', sub: `Confidence: ${rec.confidence || '…'}`, color: '#F5C842' },
        { icon: Users, label: 'Primary Age', value: data?.audience_prediction?.primary_age_group || '…', unit: '', sub: 'Core audience group', color: '#A78BFA' },
    ]

    return (
        <div className="page dashboard-page" style={{ background: 'var(--bg-primary)' }}>
            <div className="orb orb-purple" style={{ width: 500, height: 500, top: 0, right: -200 }} />
            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40 }}>

                {/* Header */}
                <div className="flex items-center justify-between mb-32">
                    <div>
                        <div className="section-label">Producer Dashboard</div>
                        <h1 className="dash-title">Film Intelligence Center</h1>
                        <p className="text-secondary">Welcome back, <span style={{ color: '#F5C842', fontWeight: 600 }}>{user?.name}</span>. Configure your film and run AI analysis.</p>
                    </div>
                    <div className="flex gap-12">
                        <button className="btn btn-outline btn-sm" onClick={handleAnalyze} disabled={loading}>
                            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Re-Analyze
                        </button>
                        <button className="btn btn-outline btn-sm" onClick={() => {
                            if (!data) return
                            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
                            const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
                            a.download = `filmpulse-analysis-${form.genre}.json`; a.click()
                        }}><Download size={14} /> Export</button>
                    </div>
                </div>

                {/* Film Input Form */}
                <motion.div className="glass-card form-panel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="flex items-center gap-8 mb-24">
                        <Film size={18} color="#F5C842" />
                        <span className="font-display font-bold">Film Configuration</span>
                        {data && <span className="badge badge-green ml-auto">✓ Last analyzed: {form.genre} · {form.language}</span>}
                    </div>
                    <div className="form-grid">
                        {[
                            { key: 'genre', label: 'Genre', type: 'select', opts: ['Action', 'Romance', 'Thriller', 'Comedy', 'Drama', 'Horror'] },
                            { key: 'language', label: 'Language', type: 'select', opts: ['Hindi', 'English', 'Tamil', 'Telugu', 'Bengali', 'Marathi'] },
                            { key: 'platform', label: 'Platform', type: 'select', opts: ['Theatre', 'OTT', 'Both'] },
                        ].map(f => (
                            <div key={f.key} className="form-group">
                                <label className="form-label">{f.label}</label>
                                <select className="form-select" value={form[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })}>
                                    {f.opts.map(o => <option key={o} value={o}>{o}</option>)}
                                </select>
                            </div>
                        ))}
                        <div className="form-group">
                            <label className="form-label">Budget (₹)</label>
                            <input type="number" className="form-input" value={form.budget} onChange={e => setForm({ ...form, budget: +e.target.value })} step={500000} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Cast Popularity (1–10)</label>
                            <input type="number" className="form-input" value={form.cast_popularity} min={1} max={10} step={0.5} onChange={e => setForm({ ...form, cast_popularity: +e.target.value })} />
                        </div>
                        <div className="form-group" style={{ alignSelf: 'flex-end' }}>
                            <button className="btn btn-primary w-full" onClick={handleAnalyze} disabled={loading}>
                                {loading ? <><RefreshCw size={16} className="spin" /> Analyzing…</> : <><Zap size={16} /> Run AI Analysis</>}
                            </button>
                        </div>
                    </div>
                    {error && <div style={{ marginTop: 12, color: '#EF4444', fontSize: '0.85rem' }}>⚠ {error}</div>}
                </motion.div>

                {!data && !loading && (
                    <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>Click "Run AI Analysis" to get your film's AI insights.</div>
                )}

                {loading && (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <RefreshCw size={32} className="spin" style={{ color: '#F5C842', margin: '0 auto 16px', display: 'block' }} />
                        <p style={{ color: 'var(--text-muted)' }}>Running ML models… GBR + RF + Ridge Regression</p>
                    </div>
                )}

                {data && !loading && (
                    <>
                        {/* Score Rings */}
                        <div className="rings-row mt-32">
                            <motion.div className="glass-card rings-card" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }}>
                                <div className="flex items-center justify-between mb-24">
                                    <h3 className="card-subtitle">Core AI Scores</h3>
                                    <span className="badge" style={{ background: `${gradeColor}18`, border: `1px solid ${gradeColor}40`, color: gradeColor }}>
                                        Grade {data.discoverability_grade}
                                    </span>
                                </div>
                                <div className="rings-flex">
                                    <div className="ring-item"><ScoreRing score={ds} label="Discovery" color="#F5C842" /></div>
                                    <div className="ring-item"><ScoreRing score={hype} label="Hype" color="#8B5CF6" /></div>
                                    <div className="ring-item"><ScoreRing score={revFit} label="Revenue Fit" color="#06B6D4" /></div>
                                </div>
                            </motion.div>

                            {platformData && (
                                <motion.div className="glass-card audience-card" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }}>
                                    <h3 className="card-subtitle mb-16">Marketing Channel Mix</h3>
                                    <div className="chart-container" style={{ height: 200 }}>
                                        <Doughnut data={platformData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#94A3B8', font: { family: 'Inter', size: 10 }, boxWidth: 8 } }, tooltip: { backgroundColor: '#0D1526' } } }} />
                                    </div>
                                </motion.div>
                            )}
                        </div>

                        {/* Metric Cards */}
                        <div className="metrics-row mt-24">
                            {metrics.map((m, i) => <MetricCard key={m.label} {...m} idx={i} />)}
                        </div>

                        {/* Charts Row */}
                        <div className="charts-row mt-24">
                            {revenueData && (
                                <motion.div className="glass-card chart-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                                    <h3 className="card-subtitle mb-20">Revenue Scenario (₹M) — Low / Mid / High</h3>
                                    <div className="chart-container" style={{ height: 240 }}>
                                        <Bar data={revenueData} options={chartOpts} />
                                    </div>
                                </motion.div>
                            )}
                            {audienceData && (
                                <motion.div className="glass-card chart-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                                    <h3 className="card-subtitle mb-20">Audience Age Demographics (%)</h3>
                                    <div className="chart-container" style={{ height: 240 }}>
                                        <Bar data={audienceData} options={chartOpts} />
                                    </div>
                                </motion.div>
                            )}
                        </div>

                        {/* Audience Split */}
                        {data.audience_prediction && (
                            <motion.div className="glass-card mt-24" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
                                style={{ padding: 28, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 24 }}>
                                <div>
                                    <div className="text-muted text-xs mb-8">Gender Split</div>
                                    <div className="flex gap-16">
                                        <div>
                                            <div style={{ color: '#06B6D4', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem' }}>{data.audience_prediction.gender_split?.male}%</div>
                                            <div className="text-muted text-xs">Male</div>
                                        </div>
                                        <div>
                                            <div style={{ color: '#8B5CF6', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem' }}>{data.audience_prediction.gender_split?.female}%</div>
                                            <div className="text-muted text-xs">Female</div>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <div className="text-muted text-xs mb-8">Urban / Rural</div>
                                    <div className="flex gap-16">
                                        <div>
                                            <div style={{ color: '#F5C842', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem' }}>{data.audience_prediction.urban_rural_split?.urban}%</div>
                                            <div className="text-muted text-xs">Urban</div>
                                        </div>
                                        <div>
                                            <div style={{ color: '#10B981', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem' }}>{data.audience_prediction.urban_rural_split?.rural}%</div>
                                            <div className="text-muted text-xs">Rural</div>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <div className="text-muted text-xs mb-8">Pan-India Reach</div>
                                    <div style={{ color: '#EF4444', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem' }}>{Math.round((data.audience_prediction.pan_india_reach_pct || 0) * 100)}%</div>
                                    <div className="text-muted text-xs">of all-India audience</div>
                                </div>
                                <div>
                                    <div className="text-muted text-xs mb-8">OTT Week-1 Est.</div>
                                    <div style={{ color: '#A78BFA', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem' }}>{((data.audience_prediction.ott_views_estimate?.week_1 || 0) / 1000).toFixed(0)}K</div>
                                    <div className="text-muted text-xs">streamed views</div>
                                </div>
                                <div>
                                    <div className="text-muted text-xs mb-8">Revenue Multiplier</div>
                                    <div style={{ color: '#10B981', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem' }}>{data.audience_prediction.revenue_multiplier}x</div>
                                    <div className="text-muted text-xs">budget return (GBR model)</div>
                                </div>
                                <div>
                                    <div className="text-muted text-xs mb-8">Platform Strategy</div>
                                    <div style={{ color: '#F5C842', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.85rem' }}>{data.release_recommendation?.platform_strategy}</div>
                                </div>
                            </motion.div>
                        )}

                        {/* Discoverability Breakdown */}
                        {Object.keys(breakdown).length > 0 && (
                            <motion.div className="glass-card formula-card mt-24 mb-40" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                                <div className="section-label mb-16">Signature Metric — Real ML Output</div>
                                <h3 className="card-subtitle mb-20">Discoverability Score Breakdown</h3>
                                <div className="formula-grid">
                                    {[
                                        { label: 'Audience Match', key: 'audience_match', weight: '25%', color: '#F5C842' },
                                        { label: 'Buzz Score', key: 'buzz_score', weight: '20%', color: '#8B5CF6' },
                                        { label: 'Competition Index', key: 'competition_index', weight: '15%', color: '#06B6D4' },
                                        { label: 'Budget Efficiency', key: 'budget_efficiency', weight: '20%', color: '#10B981' },
                                        { label: 'Release Timing', key: 'release_timing', weight: '20%', color: '#EF4444' },
                                    ].map(f => {
                                        const rawScore = breakdown[f.key] || 0
                                        const displayScore = Math.round(rawScore * 100)
                                        return (
                                            <div key={f.label} className="formula-item">
                                                <div className="flex justify-between items-center mb-8">
                                                    <span className="font-display text-sm" style={{ color: f.color }}>{f.label}</span>
                                                    <div className="flex items-center gap-8">
                                                        <span className="badge badge-gold text-xs">{f.weight}</span>
                                                        <span className="font-display font-bold" style={{ color: f.color }}>{displayScore}</span>
                                                    </div>
                                                </div>
                                                <div className="progress-bar">
                                                    <div className="progress-fill" style={{ width: `${displayScore}%`, background: f.color }} />
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                                <div className="formula-total">
                                    <span className="text-secondary">Total Discoverability Score</span>
                                    <span className="formula-score grad-text-gold">{ds} / 100</span>
                                </div>
                                <div style={{ marginTop: 12, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    🤖 {data.audience_prediction?.model}
                                </div>
                            </motion.div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
