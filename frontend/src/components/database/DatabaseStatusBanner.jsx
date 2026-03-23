import { motion } from 'framer-motion'
import { CheckCircle, AlertCircle, Loader, Database, Clock, BarChart3 } from 'lucide-react'
import { useSchemaScanner } from '../../hooks/useSchemaScanner'
import { useAppStore } from '../../store/useAppStore'

export default function DatabaseStatusBanner() {
  const { selectedDatabase } = useAppStore()
  const { schema, loading, error } = useSchemaScanner()

  if (!selectedDatabase) {
    return null
  }

  // Determine status
  const isLoading = loading
  const hasError = !!error
  const isReady = schema && !error && !loading

  const getStatusContent = () => {
    if (isLoading) {
      return {
        icon: Loader,
        title: 'Escaneando schema...',
        description: 'Analizando tablas y datos',
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
      }
    }

    if (hasError) {
      return {
        icon: AlertCircle,
        title: 'Error al conectar',
        description: error,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
      }
    }

    if (isReady) {
      return {
        icon: CheckCircle,
        title: `${schema?.tables?.length || 0} tablas - ${schema?.total_records?.toLocaleString() || 0} registros`,
        description: `Listo para auditar ${selectedDatabase.display_name || selectedDatabase.db_name}`,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
      }
    }

    return null
  }

  const status = getStatusContent()
  if (!status) return null

  const StatusIcon = status.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${status.bgColor} ${status.borderColor} ${status.color}`}
    >
      {isLoading ? (
        <StatusIcon className="w-5 h-5 animate-spin" strokeWidth={1.5} />
      ) : (
        <StatusIcon className="w-5 h-5 flex-shrink-0" strokeWidth={1.5} />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold">{status.title}</p>
        <p className="text-xs opacity-75">{status.description}</p>
      </div>

      {isReady && (
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="text-xs font-medium px-2 py-1 rounded bg-white/50"
        >
          ✓ Conectado
        </motion.div>
      )}
    </motion.div>
  )
}
