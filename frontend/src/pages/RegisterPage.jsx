import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Film, Mail, Lock, Zap, User, Building2, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './AuthPages.css'

export default function RegisterPage() {
    const { register } = useAuth()
    const navigate = useNavigate()
    const [form, setForm] = useState({ name: '', company: '', email: '', password: '', confirmPassword: '' })
    const [showPass, setShowPass] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const pwStrength = (p) => {
        if (!p) return { level: 0, label: '' }
        let score = 0
        if (p.length >= 8) score++
        if (/[A-Z]/.test(p)) score++
        if (/[0-9]/.test(p)) score++
        if (/[^A-Za-z0-9]/.test(p)) score++
        return [
            { level: 1, label: 'Weak', color: '#EF4444' },
            { level: 2, label: 'Fair', color: '#F5C842' },
            { level: 3, label: 'Good', color: '#06B6D4' },
            { level: 4, label: 'Strong', color: '#10B981' },
        ][score - 1] || { level: 0, label: '' }
    }
    const strength = pwStrength(form.password)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        if (form.password !== form.confirmPassword) {
            setError('Passwords do not match')
            return
        }
        if (form.password.length < 6) {
            setError('Password must be at least 6 characters')
            return
        }
        setLoading(true)
        try {
            await register(form.name, form.company, form.email, form.password)
            navigate('/dashboard', { replace: true })
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-orb auth-orb-1" />
            <div className="auth-orb auth-orb-2" />

            <motion.div
                className="auth-card glass-card"
                initial={{ opacity: 0, y: 40, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                style={{ maxWidth: 480 }}
            >
                <div className="auth-logo">
                    <div className="logo-icon"><Film size={20} /></div>
                    <span className="logo-text">Film<span className="grad-text-gold">Pulse</span></span>
                    <span className="logo-badge"><Zap size={10} />AI</span>
                </div>

                <h1 className="auth-title">Create account</h1>
                <p className="auth-subtitle">Start your AI-powered film journey</p>

                <form onSubmit={handleSubmit} className="auth-form">
                    {error && (
                        <motion.div className="auth-error" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                            <AlertCircle size={16} /> {error}
                        </motion.div>
                    )}

                    <div className="auth-form-row">
                        <div className="form-group">
                            <label className="form-label">Full Name</label>
                            <div className="input-icon-wrap">
                                <User size={16} className="input-icon" />
                                <input type="text" className="form-input input-with-icon" placeholder="Karan Johar"
                                    value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Studio / Company</label>
                            <div className="input-icon-wrap">
                                <Building2 size={16} className="input-icon" />
                                <input type="text" className="form-input input-with-icon" placeholder="Dharma Productions"
                                    value={form.company} onChange={e => setForm({ ...form, company: e.target.value })} />
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <div className="input-icon-wrap">
                            <Mail size={16} className="input-icon" />
                            <input type="email" className="form-input input-with-icon" placeholder="producer@studio.com"
                                value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <div className="input-icon-wrap">
                            <Lock size={16} className="input-icon" />
                            <input type={showPass ? 'text' : 'password'} className="form-input input-with-icon input-with-eye"
                                placeholder="Min. 6 characters" value={form.password}
                                onChange={e => setForm({ ...form, password: e.target.value })} required />
                            <button type="button" className="eye-btn" onClick={() => setShowPass(v => !v)}>
                                {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                            </button>
                        </div>
                        {form.password && (
                            <div className="pw-strength">
                                <div className="pw-bars">
                                    {[1, 2, 3, 4].map(i => (
                                        <div key={i} className="pw-bar" style={{ background: i <= strength.level ? strength.color : 'rgba(255,255,255,0.08)' }} />
                                    ))}
                                </div>
                                <span style={{ color: strength.color, fontSize: '0.72rem', fontWeight: 600 }}>{strength.label}</span>
                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label className="form-label">Confirm Password</label>
                        <div className="input-icon-wrap">
                            <Lock size={16} className="input-icon" />
                            <input type="password" className="form-input input-with-icon" placeholder="Re-enter password"
                                value={form.confirmPassword} onChange={e => setForm({ ...form, confirmPassword: e.target.value })} required />
                            {form.confirmPassword && (
                                <span className="input-check" style={{ color: form.password === form.confirmPassword ? '#10B981' : '#EF4444' }}>
                                    <CheckCircle size={14} />
                                </span>
                            )}
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary w-full" disabled={loading}>
                        {loading ? <><span className="spinner" />Creating account…</> : <><Zap size={16} />Create Account</>}
                    </button>
                </form>

                <p className="auth-switch">
                    Already have an account? <Link to="/login" className="auth-link">Sign in</Link>
                </p>
            </motion.div>
        </div>
    )
}
