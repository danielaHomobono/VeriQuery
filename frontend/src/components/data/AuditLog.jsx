import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../../store/useAppStore'
import { AlertCircle, CheckCircle, Clock, Database, Search, Zap } from 'lucide-react'

const getEventIcon = (type) => {
  switch (type) {
    case 'query':
      return <Search className="w-4 h-4" />
    case 'database':
      return <Database className="w-4 h-4" />
    case 'error':
      return <AlertCircle className="w-4 h-4" />
    case 'success':
      return <CheckCircle className="w-4 h-4" />
    default:
      return <Zap className="w-4 h-4" />
  }
}

const getEventColor = (type, status) => {
  if (type === 'error' || status === 'failed') {
    return 'bg-destructive/10 border-destructive/20 text-destructive'
  }
  if (status === 'success') {
    return 'bg-green-50/50 border-green-200/50 text-green-700'
  }
  if (status === 'processing') {
    return 'bg-blue-50/50 border-blue-200/50 text-blue-700'
  }
  return 'bg-muted/50 border-border/50 text-muted-foreground'
}

export default function AuditLog() {
  const { auditEvents } = useAppStore()

  // Mostrar los últimos 10 eventos
  const recentEvents = auditEvents.slice(0, 10)

  if (recentEvents.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-center">
        <div className="space-y-2">
          <Clock className="w-6 h-6 text-muted-foreground mx-auto opacity-50" />
          <p className="text-xs text-muted-foreground">Sin actividad aún</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <AnimatePresence mode="popLayout">
        {recentEvents.map((event, idx) => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ delay: idx * 0.05 }}
            className={`p-2.5 rounded-lg border flex items-start gap-2.5 transition-all hover:shadow-sm ${getEventColor(event.type, event.status)}`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {getEventIcon(event.type)}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">
                {event.type === 'query' ? '🔍 Query' : event.type === 'database' ? '📊 BD' : '⚠️ Error'}
              </p>
              {event.text && (
                <p className="text-xs line-clamp-2 opacity-75 mt-0.5">
                  {event.text}
                </p>
              )}
              {event.error && (
                <p className="text-xs opacity-60 mt-0.5">
                  {event.error}
                </p>
              )}
            </div>

            {event.timestamp && (
              <div className="flex-shrink-0 text-right">
                <p className="text-[10px] opacity-60">
                  {new Date(event.timestamp).toLocaleTimeString('es-ES', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
