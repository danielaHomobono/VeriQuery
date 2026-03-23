import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Database } from 'lucide-react'
import { useAppStore } from '../../store/useAppStore'
import MessageItem from './MessageItem'
import SuggestedPrompts from './SuggestedPrompts'
import DatabaseStatusBanner from '../database/DatabaseStatusBanner'
import { motion } from 'framer-motion'

export default function ChatContainer() {
  const [input, setInput] = useState('')
  const { messages, isLoading, sendQuery, selectedDatabase } = useAppStore()
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading) return
    setInput('')
    sendQuery(text)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!selectedDatabase) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <Database className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
          <p className="text-muted-foreground">Selecciona una base de datos para comenzar</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border shrink-0">
        <div className="space-y-3">
          <div>
            <h2 className="text-base font-semibold text-foreground">Auditoría Interactiva</h2>
            <p className="text-xs text-muted-foreground">Consulta forense con IA</p>
          </div>
          <DatabaseStatusBanner />
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-4">
        {messages.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto"
          >
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Send className="w-6 h-6 text-primary" strokeWidth={1.5} />
            </div>
            <h3 className="font-semibold text-foreground mb-2">Comienza a explorar</h3>
            <p className="text-sm text-muted-foreground mb-6">
              Haz preguntas en lenguaje natural sobre tu base de datos
            </p>
            <SuggestedPrompts onSelect={(text) => setInput(text)} />
          </motion.div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <MessageItem message={msg} />
              </motion.div>
            ))}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 text-muted-foreground"
              >
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Procesando...</span>
              </motion.div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-border shrink-0 space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Escribe tu pregunta aquí..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="px-4 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 font-medium"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Send className="w-4 h-4" strokeWidth={2} />
                <span className="hidden sm:inline">Enviar</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
