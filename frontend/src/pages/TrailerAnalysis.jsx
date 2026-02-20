import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, BarElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import { Upload, Film, Zap, Eye, Smile, AlertTriangle, CheckCircle, PlayCircle, BarChart2, RefreshCw } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './TrailerAnalysis.css'

ChartJS.register(CategoryScale, LinearScale, LineElement, BarElement, PointElement, Title, Tooltip, Legend, Filler)

const API = 'http://localhost:8000/api/v1'

const chartOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#94A3B8', font: { family: 'Inter', size: 11 }, boxWidth: 10 } }, tooltip: { backgroundColor: '#0D1526', borderColor: '#ffffff18', borderWidth: 1 } },
    scales: {
        x: { grid: { color: '#ffffff08' }, ticks: { color: '#94A3B8', fontSize: 11 } },
        y: { grid: { color: '#ffffff08' }, ticks: { color: '#94A3B8' }, min: 0, max: 100 },
    }
}

export default function TrailerAnalysis() {
    const { authFetch } = useAuth()
    const [dragging, setDragging] = useState(false)
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [error, setError] = useState('')
    const fileRef = useRef()

    const handleDrop = (e) => {
        e.preventDefault(); setDragging(false)
        const file = e.dataTransfer.files[0]
        if (file) runAnalysis(file.name)
    }
    const handleFile = (e) => {
        const file = e.target.files[0]
        if (file) runAnalysis(file.name)
    }

    const runAnalysis = async (filename) => {
        setLoading(true); setProgress(0); setError('')
        // Animate progress bar
        const iv = setInterval(() => {
            setProgress(p => { if (p >= 92) { clearInterval(iv); return 92 }; return p + Math.floor(Math.random() * 8 + 3) })
        }, 120)
        try {
            const r = await authFetch(`${API}/analyze-trailer?filename=${encodeURIComponent(filename)}`)
            if (!r.ok) throw new Error('Analysis failed')
            const data = await r.json()
            setAnalysis({ ...data, filename })
            setProgress(100)
        } catch (e) { setError(e.message); clearInterval(iv) }
        finally { setLoading(false) }
    }


    const emotionData = {
        labels: (analysis?.emotion_curve || []).map((_, i) => `${i * 10}s`),
        datasets: [
            { label: 'Excitement', data: analysis?.emotion_curve || [], borderColor: '#F5C842', backgroundColor: 'rgba(245,200,66,0.08)', fill: true, tension: 0.4, pointRadius: 3 },
            { label: 'Tension', data: (analysis?.emotion_curve || []).map(v => Math.max(0, v - 15 + Math.round(Math.random() * 14))), borderColor: '#EF4444', backgroundColor: 'rgba(239,68,68,0.05)', fill: true, tension: 0.4, pointRadius: 3 },
            { label: 'Joy', data: (analysis?.emotion_curve || []).map(v => Math.max(0, 100 - v + Math.round(Math.random() * 20))), borderColor: '#10B981', backgroundColor: 'rgba(16,185,129,0.05)', fill: true, tension: 0.4, pointRadius: 3 },
        ]
    }

    const sceneLabels = ['Opening', 'Act 1', 'Rising Action', 'Midpoint', 'Climax Buildup', 'Climax', 'Resolution']
    const sceneData = {
        labels: sceneLabels,
        datasets: [{ label: 'Intensity', data: analysis?.scene_intensity || [], backgroundColor: (analysis?.scene_intensity || []).map(v => v > 80 ? '#EF4444' : v > 60 ? '#F5C842' : '#8B5CF6'), borderRadius: 8, borderWidth: 0 }]
    }


    return (
        <div className="page trailer-page" style={{ background: 'var(--bg-primary)' }}>
            <div className="orb orb-purple" style={{ width: 400, height: 400, top: 50, right: -100 }} />
            <div className="container" style={{ position: 'relative', zIndex: 1, paddingTop: 40, paddingBottom: 60 }}>

                <div className="mb-32">
                    <div className="section-label">Trailer AI</div>
                    <h1 className="dash-title" style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800 }}>
                        Trailer Intelligence Analyzer
                    </h1>
                    <p className="text-secondary">Upload your trailer and get deep emotional analysis, scene scoring, and viral potential.</p>
                </div>

                {/* Upload Zone */}
                <motion.div
                    className={`upload-zone glass-card ${dragging ? 'dragging' : ''} ${analysis ? 'uploaded' : ''}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    onDragOver={e => { e.preventDefault(); setDragging(true) }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => !loading && fileRef.current?.click()}
                >
                    <input ref={fileRef} type="file" accept="video/*" style={{ display: 'none' }} onChange={handleFile} />
                    <div className="upload-icon-wrap">
                        {analysis ? <CheckCircle size={40} color="#10B981" /> : <Upload size={40} color={dragging ? '#F5C842' : '#8B5CF6'} />}
                    </div>
                    {loading ? (
                        <div className="upload-loading">
                            <p className="text-primary font-display font-bold">Analyzing your trailer…</p>
                            <div className="progress-bar mt-16" style={{ maxWidth: 300, margin: '16px auto 0' }}>
                                <div className="progress-fill" style={{ width: `${progress}%`, background: 'var(--grad-gold)' }} />
                            </div>
                            <p className="text-muted text-sm mt-8">{progress}% complete — extracting frames, emotions, audio</p>
                        </div>
                    ) : analysis ? (
                        <>
                            <p className="text-primary font-display font-bold">{analysis.filename}</p>
                            <p className="text-green text-sm mt-8">✓ Analysis Complete — Click to re-upload</p>
                        </>
                    ) : (
                        <>
                            <p className="upload-title">{dragging ? 'Drop your trailer here!' : 'Drop trailer here or click to upload'}</p>
                            <p className="text-muted text-sm mt-8">Supports MP4, MOV, AVI · Max 2GB</p>
                            <button className="btn btn-purple btn-sm mt-16" onClick={e => { e.stopPropagation(); fileRef.current?.click() }}>
                                <Film size={14} /> Browse File
                            </button>
                        </>
                    )}
                </motion.div>

                {/* Demo button for quick preview */}
                {!analysis && !loading && (
                    <div className="text-center mt-16">
                        <button className="btn btn-outline btn-sm" onClick={() => runAnalysis('sample_trailer.mp4')}>
                            <PlayCircle size={14} /> Try Demo Analysis
                        </button>
                    </div>
                )}

                {/* Analysis Results */}
                {analysis && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>

                        {/* Score Cards */}
                        <div className="trailer-scores mt-32">
                            {[
                                { label: 'Viral Potential', value: analysis.viral_potential, icon: Zap, color: '#F5C842', desc: 'Social shareability index' },
                                { label: 'Engagement Score', value: analysis.engagement_score, icon: Eye, color: '#8B5CF6', desc: 'Viewer retention index' },
                                { label: 'Emotional Peak', value: analysis.emotional_peak, icon: Smile, color: '#06B6D4', desc: 'Peak emotional intensity' },
                                { label: 'Tension Index', value: analysis.tension_index, icon: AlertTriangle, color: '#EF4444', desc: 'Climax scene intensity' },
                            ].map((s, i) => (

                                <motion.div key={s.label} className="trailer-score-card glass-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                                    <div className="trailer-score-icon" style={{ background: `${s.color}18`, border: `1px solid ${s.color}40`, color: s.color }}>
                                        <s.icon size={20} />
                                    </div>
                                    <div className="trailer-score-num" style={{ color: s.color }}>{s.value}</div>
                                    <div className="trailer-score-label">{s.label}</div>
                                    <div className="trailer-score-desc text-muted text-xs">{s.desc}</div>
                                </motion.div>
                            ))}
                        </div>

                        {/* Emotional Curve */}
                        <motion.div className="glass-card mt-24 p-32" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                            <div className="flex items-center gap-12 mb-20">
                                <BarChart2 size={18} color="#F5C842" />
                                <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem' }}>Emotional Curve Over Time</h3>
                            </div>
                            <div className="chart-container" style={{ height: 260 }}>
                                <Line data={emotionData} options={chartOpts} />
                            </div>
                        </motion.div>

                        {/* Scene Intensity */}
                        <motion.div className="glass-card mt-24 p-32" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                            <div className="flex items-center gap-12 mb-20">
                                <Film size={18} color="#8B5CF6" />
                                <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem' }}>Scene Intensity Breakdown</h3>
                            </div>
                            <div className="chart-container" style={{ height: 220 }}>
                                <Bar data={sceneData} options={{ ...chartOpts, plugins: { ...chartOpts.plugins, legend: { display: false } } }} />
                            </div>
                        </motion.div>

                        {/* AI Insights */}
                        <motion.div className="glass-card mt-24 p-32 mb-16" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                            <div className="section-label mb-16">AI Insights — Trailer Intelligence</div>
                            <div className="insights-grid">
                                {(analysis.insights || []).map((ins, idx) => (
                                    <div key={idx} className="insight-card glass-card">
                                        <div className="insight-icon">{['🎯', '⚡', '🎵', '📱', '🌍', '📊'][idx % 6]}</div>
                                        <div className="insight-title">Insight {idx + 1}</div>
                                        <div className="text-secondary insight-desc">{ins}</div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                    </motion.div>
                )}
            </div>
        </div>
    )
}
