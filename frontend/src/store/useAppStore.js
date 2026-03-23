import { create } from 'zustand'
import { API } from '../config/endpoints'

const TEST_USER = 'test_user@forensic.guardian'

export const useAppStore = create((set, get) => ({
  // UI state
  sidebarOpen: true,
  previewOpen: true,
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),
  togglePreview: () => set(s => ({ previewOpen: !s.previewOpen })),

  // Connection
  connectionStatus: 'connected', // 'connected' | 'disconnected' | 'loading'

  // Chat
  messages: [],
  isLoading: false,
  addMessage: (msg) => set(s => ({ messages: [...s.messages, { id: Date.now(), ...msg }] })),
  setLoading: (v) => set({ isLoading: v }),

  // Data preview
  queryResult: null,
  setQueryResult: (data) => set({ queryResult: data }),

  // Audit log
  auditEvents: [],
  addAuditEvent: (event) => set(s => ({
    auditEvents: [{ id: Date.now(), timestamp: new Date().toISOString(), ...event }, ...s.auditEvents]
  })),

  // Database Management (Guardian DB)
  sessionId: null,
  selectedDatabase: null,
  userDatabases: [],
  loadingDatabases: false,
  databaseError: null,
  
  setSessionId: (id) => set({ sessionId: id }),
  setSelectedDatabase: (db) => set({ selectedDatabase: db }),
  
  // Fetch databases for current user
  fetchUserDatabases: async () => {
    set({ loadingDatabases: true, databaseError: null })
    try {
      const response = await fetch(API.DATABASE_LIST())
      if (!response.ok) throw new Error('Failed to fetch databases')
      const data = await response.json()
      set({ userDatabases: data.databases || [] })
      return data.databases || []
    } catch (err) {
      set({ databaseError: err.message })
      return []
    } finally {
      set({ loadingDatabases: false })
    }
  },

  // Add new database configuration
  addDatabase: async (config) => {
    set({ loadingDatabases: true, databaseError: null })
    try {
      // Map frontend form fields to backend API schema
      // Use null instead of undefined for proper JSON serialization
      const requestBody = {
        name: config.db_name || config.name,  // Support both field names (required)
        db_type: config.db_type,  // required
        host: config.host || null,
        port: config.port ? parseInt(config.port) : null,
        database: config.database_name || config.database || "",  // default empty string
        username: config.username || null,
        password: config.password || null,
        filepath: config.filepath || null  // SQLite field
      }
      
      console.log('📤 Adding database:', requestBody)
      
      const response = await fetch(API.DATABASE_ADD(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })
      if (!response.ok) throw new Error('Failed to add database')
      const data = await response.json()
      set(s => ({ userDatabases: [...s.userDatabases, data] }))
      return data
    } catch (err) {
      set({ databaseError: err.message })
      throw err
    } finally {
      set({ loadingDatabases: false })
    }
  },

  // Select database and create session
  selectDatabase: async (dbName) => {
    set({ loadingDatabases: true, databaseError: null })
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/databases/select/${dbName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: TEST_USER })
      })
      if (!response.ok) throw new Error('Failed to select database')
      const data = await response.json()
      set({ 
        sessionId: data.session_id,
        selectedDatabase: dbName 
      })
      return data
    } catch (err) {
      set({ databaseError: err.message })
      throw err
    } finally {
      set({ loadingDatabases: false })
    }
  },

  // Send query (with persistent session)
  sendQuery: async (text) => {
    const { addMessage, setLoading, setQueryResult, addAuditEvent, sessionId, selectedDatabase } = get()
    addMessage({ role: 'user', text })
    setLoading(true)
    addAuditEvent({ type: 'query', text, status: 'processing' })
    try {
      const payload = { 
        question: text,
        ...(sessionId && { session_id: sessionId }),
        ...(selectedDatabase && { database_name: selectedDatabase })
      }
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      // Map 'answer' to 'text' for consistency in UI
      addMessage({ role: 'assistant', text: data.answer, ...data })
      if (data.data) setQueryResult(data.data)
      addAuditEvent({ type: 'query', text, status: 'success', confidence: data.confidence })
    } catch (err) {
      const errorMsg = err.message || 'Error al procesar la consulta.'
      addMessage({ role: 'assistant', text: errorMsg, confidence: 0, error: true })
      addAuditEvent({ type: 'error', text, status: 'failed', error: err.message })
    } finally {
      setLoading(false)
    }
  },
}))
