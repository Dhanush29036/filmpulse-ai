import { useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Film, LayoutDashboard, PlayCircle, TrendingUp, MessageSquare, Menu, X, Zap, Clapperboard, MessageCircle, LogOut, LogIn, LayoutGrid } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

const links = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/films', label: 'My Films', icon: Clapperboard },
    { to: '/intelligence', label: 'Intelligence', icon: LayoutGrid },
    { to: '/trailer', label: 'Trailer AI', icon: PlayCircle },
    { to: '/campaign', label: 'Campaign', icon: TrendingUp },
    { to: '/sentiment', label: 'Sentiment', icon: MessageSquare },
    { to: '/chat', label: 'AI Chat', icon: MessageCircle },
]

export default function Navbar() {
    const [open, setOpen] = useState(false)
    const location = useLocation()
    const navigate = useNavigate()
    const { user, logout } = useAuth()
    const isLanding = location.pathname === '/'

    const handleLogout = () => {
        logout()
        navigate('/')
        setOpen(false)
    }

    return (
        <nav className={`navbar ${isLanding ? 'navbar-transparent' : 'navbar-solid'}`}>
            <div className="navbar-inner container">
                {/* Logo */}
                <NavLink to="/" className="navbar-logo">
                    <div className="logo-icon"><Film size={18} /></div>
                    <span className="logo-text">Film<span className="grad-text-gold">Pulse</span></span>
                    <span className="logo-badge"><Zap size={10} />AI</span>
                </NavLink>

                {/* Desktop Links */}
                <div className="navbar-links">
                    {links.map(({ to, label, icon: Icon }) => (
                        <NavLink
                            key={to}
                            to={to}
                            className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
                        >
                            <Icon size={15} />
                            {label}
                        </NavLink>
                    ))}
                </div>

                {/* CTA / User */}
                <div className="navbar-cta">
                    {user ? (
                        <div className="user-menu">
                            <div className="user-avatar" title={user.name}>
                                {user.avatar_initials || user.name?.[0]?.toUpperCase() || 'U'}
                            </div>
                            <div className="user-info">
                                <span className="user-name">{user.name}</span>
                                <span className="user-role">{user.company || user.role || 'Producer'}</span>
                            </div>
                            <button className="btn btn-outline btn-sm logout-btn" onClick={handleLogout} title="Logout">
                                <LogOut size={14} />
                            </button>
                        </div>
                    ) : (
                        <NavLink to="/login" className="btn btn-primary btn-sm">
                            <LogIn size={14} /> Sign In
                        </NavLink>
                    )}
                    <button className="hamburger" onClick={() => setOpen(!open)} aria-label="menu">
                        {open ? <X size={20} /> : <Menu size={20} />}
                    </button>
                </div>
            </div>

            {/* Mobile Menu */}
            {open && (
                <div className="mobile-menu">
                    {links.map(({ to, label, icon: Icon }) => (
                        <NavLink
                            key={to}
                            to={to}
                            className="mobile-link"
                            onClick={() => setOpen(false)}
                        >
                            <Icon size={16} /> {label}
                        </NavLink>
                    ))}
                    <div className="mobile-divider" />
                    {user ? (
                        <div>
                            <div className="mobile-user">
                                <div className="user-avatar sm">{user.avatar_initials || user.name?.[0]?.toUpperCase()}</div>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{user.name}</div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{user.email}</div>
                                </div>
                            </div>
                            <button className="mobile-link" onClick={handleLogout} style={{ color: '#EF4444', width: '100%' }}>
                                <LogOut size={16} /> Logout
                            </button>
                        </div>
                    ) : (
                        <NavLink to="/login" className="mobile-link" onClick={() => setOpen(false)}>
                            <LogIn size={16} /> Sign In
                        </NavLink>
                    )}
                </div>
            )}
        </nav>
    )
}
