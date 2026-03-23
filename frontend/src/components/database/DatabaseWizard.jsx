import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, AlertCircle, Check, Loader } from 'lucide-react'
import { API } from '../../config/endpoints'

/**
 * DatabaseWizard Component
 * Simplified database connection wizard
 * Sends credentials to backend which stores them in Azure Key Vault
 * Steps: 1. Input → 2. Save (Key Vault)
 */

const TEST_USER = 'test_user@forensic.guardian'

export default function DatabaseWizard({ onSuccess = () => {}, onCancel = () => {} }) {
  const [step, setStep] = useState(1) // 1: Input, 2: Loading, 3: Success
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const [formData, setFormData] = useState({
    db_name: '',
    db_type: 'sqlserver',
    display_name: '',
    host: '',
    port: '',
    database_name: '',
    username: '',
    password: ''
  })

  const dbTypeDefaults = {
    sqlserver: { port: 1433, label: 'Azure SQL' },
    postgresql: { port: 5432, label: 'Supabase / PostgreSQL' }
  }

  const handleDbTypeChange = (type) => {
    setFormData(prev => ({
      ...prev,
      db_type: type,
      port: dbTypeDefaults[type]?.port || ''
    }))
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSaveDatabase = async () => {
    // Validate required fields
    if (!formData.db_name || !formData.display_name || !formData.host || !formData.port || 
        !formData.database_name || !formData.username || !formData.password) {
      setError('All fields are required')
      return
    }

    setIsLoading(true)
    setError(null)
    setStep(2)

    try {
      // Map frontend form fields to backend API schema
      // Only include defined values - Pydantic will handle Optional fields
      const requestBody = {
        name: formData.db_name,  // Map: db_name → name (required)
        db_type: formData.db_type,  // required
        host: formData.host || null,
        port: formData.port ? parseInt(formData.port) : null,
        database: formData.database_name || "",  // default empty string
        username: formData.username || null,
        password: formData.password || null,
        filepath: null  // SQLite field
      }

      console.log('📤 Sending database config:', requestBody)

      const response = await fetch(API.DATABASE_ADD(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to add database')
      }

      const data = await response.json()
      setStep(3)
      
      // Notify parent after success animation
      setTimeout(() => onSuccess(data), 1500)

    } catch (err) {
      setError(err.message)
      setStep(1)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setStep(1)
    setError(null)
    setFormData({
      db_name: '',
      db_type: 'sqlserver',
      display_name: '',
      host: '',
      port: 1433,
      database_name: '',
      username: '',
      password: ''
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="w-full"
    >
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-foreground flex items-center gap-2">
          <Database className="w-6 h-6" strokeWidth={1.5} />
          Add Database
        </h2>
        <p className="text-sm text-foreground/60 mt-1">
          Connect your database. Credentials are stored securely in Azure Key Vault.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 flex gap-2">
          <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" strokeWidth={2} />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      <AnimatePresence mode="wait">
        {/* Step 1: Input Form */}
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            {/* Database Type */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Database Type
              </label>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(dbTypeDefaults).map(([type, { label }]) => (
                  <button
                    key={type}
                    onClick={() => handleDbTypeChange(type)}
                    className={`p-3 rounded-lg border-2 transition-all text-sm font-medium ${
                      formData.db_type === type
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border bg-muted/30 text-foreground hover:border-border/80'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Name Fields */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Connection Name
                </label>
                <input
                  type="text"
                  name="db_name"
                  value={formData.db_name}
                  onChange={handleInputChange}
                  placeholder="my_database"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  placeholder="My Database"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
              </div>
            </div>

            {/* Connection Details */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Host
                </label>
                <input
                  type="text"
                  name="host"
                  value={formData.host}
                  onChange={handleInputChange}
                  placeholder="server.database.windows.net"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Port
                </label>
                <input
                  type="number"
                  name="port"
                  value={formData.port}
                  onChange={handleInputChange}
                  placeholder={dbTypeDefaults[formData.db_type]?.port}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
              </div>
            </div>

            {/* Database Name */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Database Name
              </label>
              <input
                type="text"
                name="database_name"
                value={formData.database_name}
                onChange={handleInputChange}
                placeholder="ContosoV210k"
                className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
              />
            </div>

            {/* Credentials */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Username
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  placeholder="admin@company"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Password
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-muted/30 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
              </div>
            </div>

            {/* Info box */}
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-xs text-foreground/70">
              <p className="font-medium mb-1">🔒 Security</p>
              <p>Your credentials will be encrypted and stored in Azure Key Vault, not in the database.</p>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                onClick={onCancel}
                className="flex-1 px-4 py-2 rounded-lg border border-border bg-muted/30 text-foreground hover:bg-muted/50 transition-colors font-medium text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveDatabase}
                disabled={isLoading}
                className="flex-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add Database
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: Saving */}
        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="py-12 flex flex-col items-center justify-center"
          >
            <Loader className="w-8 h-8 animate-spin text-primary mb-4" strokeWidth={1.5} />
            <p className="text-foreground font-medium">Saving to Azure Key Vault...</p>
            <p className="text-xs text-muted-foreground mt-1">This may take a few seconds</p>
          </motion.div>
        )}

        {/* Step 3: Success */}
        {step === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="py-12 flex flex-col items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', damping: 15 }}
              className="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center mb-4"
            >
              <Check className="w-6 h-6 text-success" strokeWidth={2.5} />
            </motion.div>
            <p className="text-foreground font-semibold">Database Added Successfully!</p>
            <p className="text-xs text-muted-foreground mt-1">
              Your database is now configured and ready to use.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
