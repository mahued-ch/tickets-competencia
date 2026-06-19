import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react'
import { meApi, loginApi } from '../services/api'

const AuthContext = createContext(null)
const TOKEN_KEY = 'tickets_competencia_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) {
      setProfile(null)
      return
    }
    setLoading(true)
    meApi()
      .then((res) => setProfile(res?.data?.data || null))
      .catch(() => { setProfile(null); setToken(''); localStorage.removeItem(TOKEN_KEY) })
      .finally(() => setLoading(false))
  }, [token])

  const login = useCallback(async (loginName, password) => {
    setError('')
    setLoading(true)
    try {
      const res = await loginApi(loginName, password)
      const data = res?.data?.data
      if (!data?.token) throw new Error('No token received')
      localStorage.setItem(TOKEN_KEY, data.token)
      setToken(data.token)
      setProfile({
        userId: data.userId,
        loginName: data.loginName,
        displayName: data.displayName,
        roleCode: data.roleCode,
        storeCodes: data.storeCodes,
      })
      return true
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Error de conexión'
      setError(msg)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken('')
    setProfile(null)
    setError('')
  }, [])

  const value = useMemo(() => ({
    token,
    currentUser: profile,
    loading,
    error,
    login,
    logout,
  }), [token, profile, loading, error, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
