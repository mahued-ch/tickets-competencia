import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { meApi } from '../services/api'

const AuthContext = createContext(null)
const STORAGE_KEY = 'tickets_competencia_demo_user'

export function AuthProvider({ children }) {
  const [demoUser, setDemoUser] = useState(() => localStorage.getItem(STORAGE_KEY) || '')
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!demoUser) {
      setProfile(null)
      return
    }
    setLoading(true)
    meApi(demoUser)
      .then((res) => setProfile(res?.data?.data || null))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false))
  }, [demoUser])

  const login = async (selectedUser) => {
    localStorage.setItem(STORAGE_KEY, selectedUser)
    setDemoUser(selectedUser)
  }

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY)
    setDemoUser('')
    setProfile(null)
  }

  const value = useMemo(() => ({
    demoUser,
    currentUser: profile,
    loading,
    login,
    logout,
  }), [demoUser, profile, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
