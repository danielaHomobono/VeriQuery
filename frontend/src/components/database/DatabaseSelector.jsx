import { useEffect, useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { Database, Plus, Check, AlertCircle, Loader } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import DatabaseModal from './DatabaseModal'

/**
 * DatabaseSelector Component
 * Shows list of user's databases and allows selection/creation
 * Integrates with Guardian DB for persistent session management
 */

export default function DatabaseSelector() {
  const {
    userDatabases,
    selectedDatabase,
    loadingDatabases,
    databaseError,
    fetchUserDatabases,
    selectDatabase,
    addDatabase: addDatabaseToStore,
  } = useAppStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectingDb, setSelectingDb] = useState(null)

  // Load databases on mount
  useEffect(() => {
    fetchUserDatabases()
  }, [])

  const handleSelectDatabase = async (dbName) => {
    setSelectingDb(dbName)
    try {
      await selectDatabase(dbName)
    } finally {
      setSelectingDb(null)
    }
  }

  const handleAddDatabase = async (config) => {
    try {
      await addDatabaseToStore(config)
      setIsModalOpen(false)
      // Refresh list
      fetchUserDatabases()
    } catch (err) {
      console.error('Error adding database:', err)
    }
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-primary" strokeWidth={1.5} />
          <h3 className="font-semibold text-foreground">
            Databases
          </h3>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          title="Add database"
          disabled={loadingDatabases}
        >
          <Plus className="w-4 h-4" strokeWidth={2} />
        </button>
      </div>

      {/* Error state */}
      {databaseError && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 flex gap-2">
          <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" strokeWidth={2} />
          <p className="text-xs text-destructive">{databaseError}</p>
        </div>
      )}

      {/* Loading state */}
      {loadingDatabases && userDatabases.length === 0 && (
        <div className="py-8 flex flex-col items-center justify-center">
          <Loader className="w-5 h-5 animate-spin text-muted-foreground mb-2" />
          <p className="text-xs text-muted-foreground">Loading databases...</p>
        </div>
      )}

      {/* Empty state */}
      {!loadingDatabases && userDatabases.length === 0 && (
        <div className="py-4 px-3 rounded-lg border border-dashed border-border text-center">
          <p className="text-xs text-muted-foreground mb-2">No databases yet</p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="text-xs text-primary hover:underline font-medium"
          >
            Add your first database
          </button>
        </div>
      )}

      {/* Database list */}
      <div className="space-y-2">
        <AnimatePresence>
          {userDatabases.map((db, idx) => (
            <motion.button
              key={db.db_name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => handleSelectDatabase(db.db_name)}
              disabled={selectingDb === db.db_name || loadingDatabases}
              className={`w-full p-2.5 rounded-lg text-left transition-all duration-200 flex items-center justify-between group
                ${selectedDatabase === db.db_name
                  ? 'bg-primary text-primary-foreground shadow-md'
                  : 'bg-muted/40 hover:bg-muted/60 text-foreground/70'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-sm flex-shrink-0">
                  {db.db_type === 'postgresql' ? '🐘' : db.db_type === 'sqlserver' ? '🔵' : '📊'}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium truncate">{db.db_name}</p>
                  <p className="text-[10px] opacity-60 truncate">{db.host}</p>
                </div>
              </div>

              {/* Selection indicator */}
              <div className="flex-shrink-0 ml-2">
                {selectingDb === db.db_name ? (
                  <Loader className="w-4 h-4 animate-spin" strokeWidth={2} />
                ) : selectedDatabase === db.db_name ? (
                  <Check className="w-4 h-4" strokeWidth={2.5} />
                ) : null}
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>

      {/* Modal para añadir BD */}
      <DatabaseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleAddDatabase}
      />
    </div>
  )
}
