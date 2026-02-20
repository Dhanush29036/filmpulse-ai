import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import Dashboard from './pages/Dashboard'
import TrailerAnalysis from './pages/TrailerAnalysis'
import CampaignOptimizer from './pages/CampaignOptimizer'
import SentimentMonitor from './pages/SentimentMonitor'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import FilmsPage from './pages/FilmsPage'
import ChatPage from './pages/ChatPage'
import MarketIntelligence from './pages/MarketIntelligence'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <div style={{ textAlign: 'center' }}>
        <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3, margin: '0 auto 16px' }} />
        <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-display)' }}>Loading FilmPulse AI…</p>
      </div>
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AppRoutes() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/trailer" element={<ProtectedRoute><TrailerAnalysis /></ProtectedRoute>} />
        <Route path="/campaign" element={<ProtectedRoute><CampaignOptimizer /></ProtectedRoute>} />
        <Route path="/sentiment" element={<ProtectedRoute><SentimentMonitor /></ProtectedRoute>} />
        <Route path="/films" element={<ProtectedRoute><FilmsPage /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
        <Route path="/intelligence" element={<ProtectedRoute><MarketIntelligence /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
