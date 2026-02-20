import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Film, Mail, Lock, Zap, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './AuthPages.css'

export default function LoginPage() {
    const { login } = useAuth()
    const navigate = useNavigate()
    const [form, setForm] = useState({ email: '', password: '' })
    const [showPass, setShowPass] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            await login(form.email, form.password)
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
            >
                {/* Logo */}
                <div className="auth-logo">
                    <div className="logo-icon"><Film size={20} /></div>
                    <span className="logo-text">Film<span className="grad-text-gold">Pulse</span></span>
                    <span className="logo-badge"><Zap size={10} />AI</span>
                </div>

                <h1 className="auth-title">Welcome back</h1>
                <p className="auth-subtitle">Sign in to your producer dashboard</p>

                <form onSubmit={handleSubmit} className="auth-form">
                    {error && (
                        <motion.div className="auth-error" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                            <AlertCircle size={16} /> {error}
                        </motion.div>
                    )}

                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <div className="input-icon-wrap">
                            <Mail size={16} className="input-icon" />
                            <input
                                type="email"
                                className="form-input input-with-icon"
                                placeholder="producer@studio.com"
                                value={form.email}
                                onChange={e => setForm({ ...form, email: e.target.value })}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <div className="input-icon-wrap">
                            <Lock size={16} className="input-icon" />
                            <input
                                type={showPass ? 'text' : 'password'}
                                className="form-input input-with-icon input-with-eye"
                                placeholder="••••••••"
                                value={form.password}
                                onChange={e => setForm({ ...form, password: e.target.value })}
                                required
                            />
                            <button type="button" className="eye-btn" onClick={() => setShowPass(v => !v)}>
                                {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                            </button>
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary w-full" disabled={loading}>
                        {loading ? <><span className="spinner" />Signing in…</> : <><Zap size={16} />Sign In</>}
                    </button>
                </form>

                <p className="auth-switch">
                    New producer? <Link to="/register" className="auth-link">Create account</Link>
                </p>

                {/* Demo credentials hint */}
                <div className="demo-hint">
                    <span>🎬 Demo:</span> Register a free account to get started instantly
                </div>
            </motion.div>
        </div>
    )
}
