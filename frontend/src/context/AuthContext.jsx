import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const API = 'http://localhost:8000/api/v1'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(() => localStorage.getItem('fp_token'))
    const [loading, setLoading] = useState(true)

    // Validate token on mount
    useEffect(() => {
        if (!token) { setLoading(false); return }
        fetch(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(r => r.ok ? r.json() : Promise.reject())
            .then(u => setUser(u))
            .catch(() => { localStorage.removeItem('fp_token'); setToken(null) })
            .finally(() => setLoading(false))
    }, [token])

    const login = useCallback(async (email, password) => {
        const r = await fetch(`${API}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        })
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || 'Login failed')
        localStorage.setItem('fp_token', data.access_token)
        setToken(data.access_token)
        setUser(data.user)
        return data.user
    }, [])

    const register = useCallback(async (name, company, email, password) => {
        const r = await fetch(`${API}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, company, email, password }),
        })
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || 'Registration failed')
        localStorage.setItem('fp_token', data.access_token)
        setToken(data.access_token)
        setUser(data.user)
        return data.user
    }, [])

    const logout = useCallback(() => {
        localStorage.removeItem('fp_token')
        setToken(null)
        setUser(null)
    }, [])

    const authFetch = useCallback((url, opts = {}) => {
        return fetch(url, {
            ...opts,
            headers: {
                ...(opts.headers || {}),
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            }
        })
    }, [token])

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout, authFetch }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    return useContext(AuthContext)
}
