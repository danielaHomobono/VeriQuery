import { motion } from 'framer-motion'
import { Sparkles, MessageSquare, ChevronRight } from 'lucide-react'

/**
 * Genera sugerencias inteligentes de queries basadas en el schema
 */
export function generateSuggestedQueries(schema) {
  if (!schema || !schema.tables || schema.tables.length === 0) {
    return []
  }

  const queries = []
  const tables = schema.tables

  // Tabla principal (la primera con más registros)
  const mainTable = tables.reduce((max, t) => 
    (t.row_count || 0) > (max.row_count || 0) ? t : max
  )

  // 1. Recuento total
  queries.push({
    category: 'Conteo',
    text: `¿Cuántos ${mainTable.name} tenemos en total?`,
    icon: '📊',
  })

  // 2. Resumen general
  queries.push({
    category: 'Resumen',
    text: `Dame un resumen general de ${mainTable.name}`,
    icon: '📋',
  })

  // 3. Registros recientes (si tiene columna de fecha)
  const dateColumns = mainTable.columns?.filter(c => 
    c.type && (c.type.toLowerCase().includes('date') || c.type.toLowerCase().includes('time'))
  ) || []

  if (dateColumns.length > 0) {
    queries.push({
      category: 'Temporales',
      text: `¿Cuáles son los ${mainTable.name} más recientes?`,
      icon: '⏰',
    })

    queries.push({
      category: 'Análisis',
      text: `Cambios en ${mainTable.name} en los últimos 7 días`,
      icon: '📈',
    })
  }

  // 4. Si hay múltiples tablas, preguntar por relaciones
  if (tables.length > 1) {
    const secondTable = tables[1]
    queries.push({
      category: 'Relaciones',
      text: `Correlaciona datos entre ${mainTable.name} y ${secondTable.name}`,
      icon: '🔗',
    })
  }

  // 5. Análisis forense
  queries.push({
    category: 'Forense',
    text: `¿Hay patrones anómalos en ${mainTable.name}?`,
    icon: '🔍',
  })

  // 6. Duplicados/Integridad
  const primaryKeys = mainTable.columns?.filter(c => 
    c.name && (c.name.toLowerCase().includes('id') || c.name.toLowerCase().includes('pk'))
  ) || []

  if (primaryKeys.length > 0) {
    queries.push({
      category: 'Integridad',
      text: `¿Hay registros duplicados en ${mainTable.name}?`,
      icon: '⚠️',
    })
  }

  return queries.slice(0, 6) // Máximo 6 sugerencias
}

export default function SuggestedQueries({ schema, onSelectQuery }) {
  const queries = generateSuggestedQueries(schema)

  if (queries.length === 0) {
    return null
  }

  // Agrupar por categoría
  const grouped = queries.reduce((acc, q) => {
    if (!acc[q.category]) {
      acc[q.category] = []
    }
    acc[q.category].push(q)
    return acc
  }, {})

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="space-y-4"
    >
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-amber-500" />
        <h3 className="text-sm font-semibold text-foreground">Preguntas sugeridas para ti</h3>
      </div>

      <div className="space-y-3">
        {queries.map((query, idx) => (
          <motion.button
            key={idx}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 + idx * 0.05 }}
            onClick={() => onSelectQuery(query.text)}
            className="w-full text-left p-3 rounded-lg border border-border/50 bg-muted/20 hover:bg-muted/40 hover:border-primary/30 transition-all group"
          >
            <div className="flex items-start gap-3">
              <span className="text-lg flex-shrink-0">{query.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-primary/70 mb-1">{query.category}</p>
                <p className="text-sm text-foreground line-clamp-2">{query.text}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary flex-shrink-0 transition-colors" />
            </div>
          </motion.button>
        ))}
      </div>

      <div className="text-xs text-muted-foreground text-center pt-2">
        💡 O escribe tu propia pregunta en el campo inferior
      </div>
    </motion.div>
  )
}
