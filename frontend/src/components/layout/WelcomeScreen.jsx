import { Database, Plus, ArrowRight } from 'lucide-react'
import { useAppStore } from '../../store/useAppStore'
import DatabaseModal from '../database/DatabaseModal'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

export default function WelcomeScreen() {
  const { userDatabases, selectedDatabase, fetchUserDatabases, selectDatabase } = useAppStore()
  const [isModalOpen, setIsModalOpen] = useState(false)

  useEffect(() => {
    fetchUserDatabases()
  }, [])

  if (selectedDatabase) {
    return null // Hide welcome screen if database is selected
  }

  const handleSelectDatabase = async (dbName) => {
    await selectDatabase(dbName)
  }

  const handleAddDatabase = async (config) => {
    // Backend already saved the database via DatabaseWizard
    // Just close the modal and refresh the list
    setIsModalOpen(false)
    await fetchUserDatabases()
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex-1 flex items-center justify-center p-8 overflow-y-auto"
    >
      <div className="w-full max-w-2xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="mb-6 flex justify-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
              <Database className="w-8 h-8 text-primary" strokeWidth={1.5} />
            </div>
          </div>
          <h2 className="text-4xl font-bold text-foreground mb-2">Select a Database</h2>
          <p className="text-lg text-muted-foreground">Choose or add a database to begin forensic analysis</p>
        </div>

        {/* Available Databases */}
        {userDatabases.length > 0 && (
          <div className="mb-12">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">Available Databases</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {userDatabases.map((db, idx) => (
                <motion.button
                  key={db.db_name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  onClick={() => handleSelectDatabase(db.db_name)}
                  className="p-4 rounded-xl border border-border glass-surface hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 text-left group"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-2xl">
                      {db.db_type === 'postgresql' ? '🐘' : db.db_type === 'sqlserver' ? '🔵' : '📊'}
                    </span>
                    <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors opacity-0 group-hover:opacity-100" strokeWidth={2} />
                  </div>
                  <p className="font-semibold text-foreground">{db.db_name}</p>
                  <p className="text-xs text-muted-foreground mt-1">{db.host}</p>
                </motion.button>
              ))}
            </div>
          </div>
        )}

        {/* Add New Database */}
        <div className="border-t border-border pt-8">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">Add New Database</h3>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setIsModalOpen(true)}
            className="w-full p-6 rounded-xl border-2 border-dashed border-border hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 flex items-center justify-center gap-3 group"
          >
            <Plus className="w-6 h-6 text-muted-foreground group-hover:text-primary transition-colors" strokeWidth={1.5} />
            <div className="text-left">
              <p className="font-semibold text-foreground">Connect a New Database</p>
              <p className="text-xs text-muted-foreground">Add SQL Server or PostgreSQL/Supabase</p>
            </div>
          </motion.button>
        </div>

        {/* Modal */}
        <DatabaseModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSuccess={handleAddDatabase}
        />
      </div>
    </motion.div>
  )
}
