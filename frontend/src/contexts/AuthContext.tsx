import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface User {
  id: string
  email: string
  full_name: string
  company?: string
  membership_type: string
  created_at: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  googleLogin: (token: string) => Promise<void>
  register: (email: string, password: string, fullName: string, company?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const setAuthToken = (token: string) => {
    localStorage.setItem('token', token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  const removeAuthToken = () => {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        email,
        password
      })
      
      const { access_token, user: userData } = response.data
      setAuthToken(access_token)
      setUser(userData)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const googleLogin = async (token: string) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/google`, {
        token
      })
      
      const { access_token, user: userData } = response.data
      setAuthToken(access_token)
      setUser(userData)
    } catch (error) {
      console.error('Google login error:', error)
      throw error
    }
  }

  const register = async (email: string, password: string, fullName: string, company?: string) => {
    try {
      console.log('Attempting registration with:', { email, fullName, company, apiUrl: API_BASE_URL })
      
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
        email,
        password,
        full_name: fullName,
        company
      })
      
      console.log('Registration successful:', { userId: response.data.user?.id, email: response.data.user?.email })
      
      const { access_token, user: userData } = response.data
      setAuthToken(access_token)
      setUser(userData)
    } catch (error: any) {
      console.error('Registration error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        code: error.code,
        apiUrl: API_BASE_URL
      })
      throw error
    }
  }

  const logout = () => {
    removeAuthToken()
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/auth/me`)
      setUser(response.data)
    } catch (error) {
      console.error('Error refreshing user:', error)
      logout()
    }
  }

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token')
      if (token) {
        setAuthToken(token)
        try {
          await refreshUser()
        } catch (error) {
          removeAuthToken()
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const value = {
    user,
    loading,
    login,
    googleLogin,
    register,
    logout,
    refreshUser
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
