import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, Database, ChevronDown, Eye, Settings, Sparkles, ArrowRight, Plus
} from 'lucide-react';
import { useSchemaScanner } from '../hooks/useSchemaScanner';
import { useAppStore } from '../store/useAppStore';

export default function SchemaOverview() {
  const { schema, loading, error } = useSchemaScanner();
  const { selectedDatabase } = useAppStore();
  const [expandedTable, setExpandedTable] = useState(null);
  const [showMoreQueries, setShowMoreQueries] = useState(false);

  if (!selectedDatabase) return null;

  // Loading state
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-6 space-y-4"
      >
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
          <div className="flex items-center gap-3">
            <div className="animate-spin">
              <Database className="text-blue-600" size={24} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Escaneando schema...</h3>
              <p className="text-sm text-gray-600">Analizando tablas y datos</p>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Error state
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-6"
      >
        <div className="bg-red-50 rounded-lg p-6 border border-red-200">
          <p className="text-red-700 font-semibold">Error al conectar</p>
          <p className="text-red-600 text-sm mt-2">{error}</p>
        </div>
      </motion.div>
    );
  }

  if (!schema) return null;

  // Calculate totals
  const tableCount = schema.tables?.length || 0;
  const totalRecords = schema.tables?.reduce((sum, table) => sum + (table.record_count || 0), 0) || 0;

  // Suggested queries based on schema
  const suggestedQueries = generateSuggestedQueries(schema.tables || []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4 pb-6"
    >
      {/* Connection Status Banner */}
      <div className="mx-6 mt-6 border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-green-50 border-b border-green-200 p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="text-green-600" size={20} />
            <div>
              <p className="font-semibold text-gray-900">
                ✅ {selectedDatabase} conectado exitosamente
              </p>
              <p className="text-sm text-gray-600">
                📊 {tableCount} tablas encontradas • {totalRecords.toLocaleString()} registros totales
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Data Overview Section */}
      <div className="mx-6 border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
          <p className="font-semibold text-gray-900">📋 TUS DATOS</p>
        </div>
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
          <p className="text-sm text-gray-600 px-2">
            Guardian puede consultar estas tablas:
          </p>

          {schema.tables?.map((table, idx) => (
            <motion.div
              key={table.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="border border-gray-200 rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setExpandedTable(expandedTable === table.name ? null : table.name)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600 flex-shrink-0" />
                    <span className="truncate">{table.name}</span>
                    <span className="text-xs text-gray-500 ml-auto flex-shrink-0">
                      {table.record_count?.toLocaleString()} registros
                    </span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    └─ {table.columns?.slice(0, 3).map(c => c.name).join(', ')}
                    {table.columns && table.columns.length > 3 ? '...' : ''}
                  </p>
                </div>
                <ChevronDown
                  size={18}
                  className={`flex-shrink-0 text-gray-400 transition-transform ${
                    expandedTable === table.name ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {/* Expanded Details */}
              <AnimatePresence>
                {expandedTable === table.name && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-gray-200 bg-gray-50 p-4 space-y-3"
                  >
                    {/* Column Info */}
                    <div>
                      <p className="text-xs font-semibold text-gray-700 mb-2">Columnas:</p>
                      <div className="grid grid-cols-2 gap-2">
                        {table.columns?.slice(0, 6).map(col => (
                          <div key={col.name} className="text-xs bg-white p-2 rounded border border-gray-200">
                            <p className="font-mono text-gray-700">{col.name}</p>
                            <p className="text-gray-500">{col.type}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Sample Data Preview */}
                    {table.sample_data && table.sample_data.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1">
                          <Eye size={14} /> Vista previa:
                        </p>
                        <div className="text-xs bg-white p-3 rounded border border-gray-200 text-gray-600 max-h-24 overflow-y-auto font-mono">
                          {Object.entries(table.sample_data[0])
                            .slice(0, 3)
                            .map(([key, val]) => (
                              <p key={key}>
                                <span className="text-gray-700">{key}:</span> {String(val).substring(0, 40)}
                              </p>
                            ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}

          {/* Configure Access Button */}
          <button className="w-full mt-4 px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 hover:bg-gray-50 transition-colors flex items-center justify-center gap-2 text-gray-700 font-medium">
            <Settings size={18} />
            ⚙️ Configurar acceso
          </button>
        </div>
      </div>

      {/* Suggested Queries Section */}
      <div className="mx-6 border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
          <p className="font-semibold text-gray-900">💡 PRUEBA ESTAS PREGUNTAS</p>
        </div>
        <div className="p-4 space-y-2">
          <p className="text-sm text-gray-600">
            Generadas automáticamente para TU base de datos:
          </p>

          {suggestedQueries.slice(0, showMoreQueries ? suggestedQueries.length : 4).map((query, idx) => (
            <motion.button
              key={idx}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="w-full px-3 py-2 text-left text-sm border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors bg-white text-gray-700 truncate"
            >
              {query.emoji} {query.text}
            </motion.button>
          ))}

          {suggestedQueries.length > 4 && (
            <button
              onClick={() => setShowMoreQueries(!showMoreQueries)}
              className="w-full px-3 py-2 text-sm text-blue-600 font-medium hover:text-blue-700 flex items-center justify-center gap-1 mt-2"
            >
              {showMoreQueries ? '- Ver menos' : '+ Ver más ejemplos'}
            </button>
          )}
        </div>
      </div>

      {/* Start Button */}
      <div className="mx-6 mb-6 border border-gray-200 rounded-lg overflow-hidden">
        <button className="w-full px-4 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold flex items-center justify-center gap-2 transition-all">
          <Sparkles size={20} />
          🚀 Empezar a preguntar
        </button>
        <div className="bg-blue-50 border-t border-gray-200 px-4 py-3">
          <p className="text-xs text-gray-600 mb-2">O escribe tu pregunta aquí:</p>
          <div className="border border-gray-300 rounded-lg p-3 bg-white text-sm text-gray-500">
            Pregúntale cualquier cosa a tus datos...
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/**
 * Generate intelligent query suggestions based on schema
 */
function generateSuggestedQueries(tables) {
  const queries = [];
  
  // Count queries
  const countTable = tables.find(t => t.name.toLowerCase().includes('beneficiario') || t.name.toLowerCase().includes('usuario'));
  if (countTable) {
    queries.push({
      emoji: '📊',
      text: `¿Cuántos ${countTable.name.toLowerCase()} tenemos activos?`
    });
  }

  // Date-based queries
  const dateTable = tables.find(t => t.columns?.some(c => 
    c.name.toLowerCase().includes('fecha') || c.name.toLowerCase().includes('date')
  ));
  if (dateTable) {
    queries.push({
      emoji: '📅',
      text: `¿Cuántos registros tenemos este mes en ${dateTable.name}?`
    });
  }

  // Location/Zone queries
  const locationTable = tables.find(t => t.columns?.some(c => 
    c.name.toLowerCase().includes('zona') || c.name.toLowerCase().includes('region')
  ));
  if (locationTable) {
    queries.push({
      emoji: '🗺️',
      text: `¿Qué zona tiene más registros en ${locationTable.name}?`
    });
  }

  // Growth queries
  queries.push({
    emoji: '📈',
    text: '¿Cómo ha crecido nuestro programa este año?'
  });

  // Additional intelligent queries
  queries.push({
    emoji: '🎯',
    text: '¿Cuáles son nuestras principales métricas?'
  });

  queries.push({
    emoji: '⚠️',
    text: '¿Hay anomalías o valores atípicos en los datos?'
  });

  queries.push({
    emoji: '🔍',
    text: '¿Cuál es la distribución de nuestros datos?'
  });

  return queries;
}
