import { useState, useEffect } from 'react'
import { AlertCircle, ChevronDown } from 'lucide-react'
import { API } from '../../config/endpoints'

export default function AmbiguityResolver({ question, onSelect, isLoading }) {
  const [ambiguity, setAmbiguity] = useState(null)
  const [error, setError] = useState('')
  const [selectedOption, setSelectedOption] = useState(null)

  useEffect(() => {
    if (!question) return

    const analyzeAmbiguity = async () => {
      try {
        setError('')
        setSelectedOption(null)
        
        const response = await fetch(API.ANALYZE_AMBIGUITY, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question }),
        })

        if (!response.ok) {
          throw new Error('Error analizando ambigüedad')
        }

        const data = await response.json()
        setAmbiguity(data)
      } catch (err) {
        console.error('Ambiguity analysis error:', err)
        // Si no es ambiguo o hay error, continuar normalmente
        setAmbiguity(null)
      }
    }

    analyzeAmbiguity()
  }, [question])

  if (!ambiguity || !ambiguity.is_ambiguous) {
    return null
  }

  const handleSelect = async (metric) => {
    setSelectedOption(metric)
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/query/select-clarification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          chosen_metric: metric,
        }),
      })

      if (!response.ok) {
        throw new Error('Error confirmando clarificación')
      }

      const data = await response.json()
      
      // Llamar callback con contexto de clarificación
      if (onSelect) {
        onSelect({
          original_question: question,
          chosen_metric: metric,
          clarified_question: data.message,
        })
      }
    } catch (err) {
      console.error('Selection error:', err)
      setError('Error al procesar la selección')
    }
  }

  return (
    <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="flex gap-3">
        <AlertCircle className="text-amber-600 shrink-0 mt-0.5" size={20} />
        <div className="flex-1">
          <p className="text-sm font-medium text-amber-900 mb-3">
            Tu pregunta es un poco ambigua. ¿Cuál de estas opciones te interesa?
          </p>

          <div className="space-y-2">
            {ambiguity.clarifications.map((clarif, idx) => (
              <button
                key={idx}
                onClick={() => handleSelect(clarif.metric)}
                disabled={isLoading || !!selectedOption}
                className={`w-full text-left px-3 py-2 rounded border transition-all ${
                  selectedOption === clarif.metric
                    ? 'bg-amber-100 border-amber-400'
                    : 'bg-white border-amber-200 hover:border-amber-400 hover:bg-amber-50'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-lg">{clarif.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">{clarif.label}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{clarif.description}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {selectedOption && (
            <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded text-xs text-green-800">
              ✓ Opción seleccionada. Procesando...
            </div>
          )}

          {error && (
            <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
              ✗ {error}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
