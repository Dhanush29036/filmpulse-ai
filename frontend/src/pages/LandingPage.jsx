import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Film, TrendingUp, Target, Zap, Star, ArrowRight, Play, BarChart2, Globe, Award } from 'lucide-react'
import './LandingPage.css'

const stats = [
    { value: '94%', label: 'Prediction Accuracy' },
    { value: '3.2x', label: 'Average ROI Uplift' },
    { value: '500+', label: 'Films Analyzed' },
    { value: '$2B+', label: 'Box Office Tracked' },
]

const features = [
    {
        icon: Target,
        color: 'gold',
        title: 'Audience Prediction',
        desc: 'XGBoost-powered model predicts your target demographics, regional demand, and revenue range before release.',
    },
    {
        icon: Film,
        color: 'purple',
        title: 'Trailer AI Analyzer',
        desc: 'Deep learning extracts emotional curves, scene intensity, and viral potential from your trailer in seconds.',
    },
    {
        icon: BarChart2,
        color: 'cyan',
        title: 'Budget Optimizer',
        desc: 'Allocate marketing spend across channels with AI-powered ROI predictions to maximize every rupee.',
    },
    {
        icon: TrendingUp,
        color: 'green',
        title: 'Sentiment Engine',
        desc: 'BERT-powered real-time tracking of social buzz converts audience chatter into a 0–100 Hype Score.',
    },
    {
        icon: Globe,
        color: 'gold',
        title: 'Release Strategy',
        desc: 'Discoverability Score combines 5 weighted signals to pinpoint the perfect release date and platform.',
    },
    {
        icon: Award,
        color: 'purple',
        title: 'Festival Matcher',
        desc: 'AI matches your film against historical festival data to predict selection probability for top circuits.',
    },
]

const steps = [
    { num: '01', title: 'Upload Film Details', desc: 'Enter metadata, budget, language, genre and upload your trailer.' },
    { num: '02', title: 'AI Analysis Runs', desc: 'Five parallel ML models process every signal simultaneously.' },
    { num: '03', title: 'Get Your Strategy', desc: 'Receive your Discoverability Score, budget plan, and release playbook.' },
]

const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
}
const stagger = { show: { transition: { staggerChildren: 0.1 } } }

export default function LandingPage() {
    const navigate = useNavigate()

    return (
        <div className="landing">
            {/* ── Hero ── */}
            <section className="hero">
                <div className="orb orb-purple" style={{ width: 600, height: 600, top: -100, left: -100 }} />
                <div className="orb orb-gold" style={{ width: 400, height: 400, top: 100, right: -50 }} />

                <div className="container hero-inner">
                    <motion.div
                        className="hero-content"
                        initial="hidden"
                        animate="show"
                        variants={stagger}
                    >
                        <motion.div variants={fadeUp}>
                            <span className="badge badge-purple mb-24">
                                <Zap size={12} /> Powered by AI &amp; Machine Learning
                            </span>
                        </motion.div>

                        <motion.h1 variants={fadeUp} className="hero-title">
                            Turn Creative Vision Into<br />
                            <span className="grad-text-gold">Data-Driven</span> Success
                        </motion.h1>

                        <motion.p variants={fadeUp} className="hero-subtitle">
                            FilmPulse AI gives film producers real-time audience intelligence,
                            budget optimization, trailer analysis, and release strategy — all powered
                            by advanced machine learning.
                        </motion.p>

                        <motion.div variants={fadeUp} className="hero-actions">
                            <button className="btn btn-primary btn-lg" onClick={() => navigate('/dashboard')}>
                                Launch Dashboard <ArrowRight size={18} />
                            </button>
                            <button className="btn btn-outline btn-lg hero-play-btn">
                                <div className="play-icon"><Play size={14} /></div>
                                See It In Action
                            </button>
                        </motion.div>

                        <motion.div variants={fadeUp} className="hero-stats">
                            {stats.map(s => (
                                <div key={s.label} className="hero-stat">
                                    <div className="hero-stat-value grad-text-gold">{s.value}</div>
                                    <div className="hero-stat-label">{s.label}</div>
                                </div>
                            ))}
                        </motion.div>
                    </motion.div>

                    {/* Dashboard Preview Card */}
                    <motion.div
                        className="hero-visual"
                        initial={{ opacity: 0, x: 60 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
                    >
                        <div className="preview-card glass-card">
                            <div className="preview-header">
                                <div className="preview-dot red" />
                                <div className="preview-dot yellow" />
                                <div className="preview-dot green" />
                                <span className="preview-title">FilmPulse Dashboard</span>
                            </div>
                            <div className="preview-metrics">
                                {[
                                    { label: 'Discoverability', value: '87', color: '#F5C842', pct: 87 },
                                    { label: 'Hype Score', value: '73', color: '#8B5CF6', pct: 73 },
                                    { label: 'Revenue Est.', value: '91', color: '#06B6D4', pct: 91 },
                                    { label: 'Budget Efficiency', value: '68', color: '#10B981', pct: 68 },
                                ].map(m => (
                                    <div key={m.label} className="preview-metric">
                                        <div className="preview-metric-top">
                                            <span className="preview-metric-label">{m.label}</span>
                                            <span className="preview-metric-value" style={{ color: m.color }}>{m.value}</span>
                                        </div>
                                        <div className="progress-bar">
                                            <div className="progress-fill" style={{ width: `${m.pct}%`, background: m.color }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="preview-footer">
                                <span className="badge badge-green"><span className="pulse-dot" /> Live Analysis</span>
                                <span className="text-muted text-xs">Action · $8M Budget · Q2 2025</span>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* ── Features ── */}
            <section className="section">
                <div className="container">
                    <motion.div
                        className="text-center mb-32"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <div className="section-label">Features</div>
                        <h2 className="section-title">Everything a Producer Needs</h2>
                        <p className="section-subtitle" style={{ margin: '0 auto' }}>
                            From pre-production analytics to release-day sentiment tracking,
                            FilmPulse has your entire decision lifecycle covered.
                        </p>
                    </motion.div>

                    <motion.div
                        className="grid-3 features-grid"
                        initial="hidden"
                        whileInView="show"
                        viewport={{ once: true }}
                        variants={stagger}
                    >
                        {features.map((f) => (
                            <motion.div key={f.title} variants={fadeUp} className={`feature-card glass-card feature-${f.color}`}>
                                <div className={`feature-icon feature-icon-${f.color}`}>
                                    <f.icon size={22} />
                                </div>
                                <h3 className="feature-title">{f.title}</h3>
                                <p className="feature-desc">{f.desc}</p>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* ── How It Works ── */}
            <section className="section how-section">
                <div className="container">
                    <motion.div
                        className="text-center mb-32"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <div className="section-label">Workflow</div>
                        <h2 className="section-title">How FilmPulse Works</h2>
                    </motion.div>

                    <div className="steps-row">
                        {steps.map((s, i) => (
                            <motion.div
                                key={s.num}
                                className="step-card glass-card"
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.15 }}
                            >
                                <div className="step-num grad-text-gold">{s.num}</div>
                                <h3 className="step-title">{s.title}</h3>
                                <p className="step-desc">{s.desc}</p>
                                {i < steps.length - 1 && <div className="step-arrow"><ArrowRight size={20} /></div>}
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── CTA Banner ── */}
            <section className="section cta-section">
                <div className="container">
                    <motion.div
                        className="cta-banner glass-card"
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                    >
                        <div className="orb orb-purple" style={{ width: 300, height: 300, top: -50, right: 100 }} />
                        <div className="orb orb-gold" style={{ width: 200, height: 200, bottom: -50, left: 50 }} />
                        <div className="cta-content">
                            <Star size={32} color="#F5C842" style={{ marginBottom: 16 }} />
                            <h2 className="cta-title">Ready to Greenlight Your Next Hit?</h2>
                            <p className="cta-sub">Join hundreds of producers using AI to make smarter film decisions.</p>
                            <button className="btn btn-primary btn-lg mt-24" onClick={() => navigate('/dashboard')}>
                                Start Free Analysis <ArrowRight size={18} />
                            </button>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="landing-footer">
                <div className="container footer-inner">
                    <div className="footer-logo">
                        <Film size={16} /> FilmPulse AI
                    </div>
                    <p className="text-muted text-sm">© 2025 FilmPulse AI. Turning Creative Vision into Data-Driven Success.</p>
                </div>
            </footer>
        </div>
    )
}
