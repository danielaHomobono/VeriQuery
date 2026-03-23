import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  Database,
  Zap,
  Lock,
  BarChart3,
  ChevronRight,
  Sparkles,
  MessageSquare,
  Eye,
  Clock
} from 'lucide-react'

export default function WelcomeScreen() {
  const [step, setStep] = useState(0)

  const features = [
    {
      icon: Shield,
      title: 'Auditoría Segura',
      desc: 'Credenciales almacenadas en Azure Key Vault',
    },
    {
      icon: Database,
      title: 'Multi-BD',
      desc: 'Conecta PostgreSQL, SQL Server y más',
    },
    {
      icon: Zap,
      title: 'Queries IA',
      desc: 'Pregunta en lenguaje natural',
    },
    {
      icon: BarChart3,
      title: 'Análisis Forense',
      desc: 'Detecta patrones y anomalías',
    },
  ]

  const steps = [
    {
      number: '1',
      title: 'Agrega tu primera BD',
      description: 'Haz clic en el botón + en el panel izquierdo',
      icon: Database,
      highlight: 'Elige PostgreSQL, SQL Server o cualquier BD',
    },
    {
      number: '2',
      title: 'Verifica conexión',
      description: 'Guardian probará acceso a tu BD',
      icon: Lock,
      highlight: 'Tus credenciales se guardan de forma segura',
    },
    {
      number: '3',
      title: 'Explora schema',
      description: 'Visualiza tablas y datos disponibles',
      icon: Eye,
      highlight: 'Entiende tu estructura de datos',
    },
    {
      number: '4',
      title: 'Haz preguntas',
      description: 'Escribe tu pregunta de auditoría',
      icon: MessageSquare,
      highlight: 'Ejemplo: "¿Cuántos cambios hubo en users hoy?"',
    },
  ]

  const currentStep = steps[step]
  const CurrentIcon = currentStep.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl mx-auto p-6 space-y-8"
    >
      {/* Header */}
      <div className="text-center space-y-3">
        <motion.div
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          className="flex justify-center"
        >
          <div className="w-16 h-16 bg-gradient-to-br from-primary/20 to-primary/5 rounded-xl flex items-center justify-center">
            <Shield className="w-8 h-8 text-primary" strokeWidth={1.5} />
          </div>
        </motion.div>

        <h1 className="text-3xl font-bold text-foreground">
          Bienvenido a Guardian
        </h1>
        <p className="text-lg text-muted-foreground">
          Auditoría forense inteligente con IA
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {features.map((feature, idx) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="p-4 rounded-lg border border-border/50 hover:border-border bg-muted/20 hover:bg-muted/40 transition-all"
          >
            <div className="flex items-start gap-3">
              <feature.icon className="w-5 h-5 text-primary flex-shrink-0 mt-1" strokeWidth={1.5} />
              <div className="flex-1">
                <h3 className="font-semibold text-foreground text-sm">{feature.title}</h3>
                <p className="text-xs text-muted-foreground mt-1">{feature.desc}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border/20"></div>
        </div>
        <div className="relative flex justify-center">
          <span className="px-3 bg-background text-xs text-muted-foreground">Paso a paso</span>
        </div>
      </div>

      {/* Step-by-Step */}
      <motion.div
        key={`step-${step}`}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="bg-muted/20 rounded-xl border border-border/50 p-8 space-y-6"
      >
        {/* Step Number & Icon */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-primary/30 to-primary/10 flex items-center justify-center flex-shrink-0">
            <CurrentIcon className="w-7 h-7 text-primary" strokeWidth={1.5} />
          </div>
          <div>
            <div className="text-sm font-semibold text-primary">
              Paso {currentStep.number} de 4
            </div>
            <h2 className="text-2xl font-bold text-foreground">{currentStep.title}</h2>
          </div>
        </div>

        {/* Description */}
        <div className="space-y-3">
          <p className="text-base text-foreground">{currentStep.description}</p>
          <div className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/10 border border-primary/20">
            <Sparkles className="w-4 h-4 text-primary" />
            <p className="text-sm text-primary font-medium">{currentStep.highlight}</p>
          </div>
        </div>

        {/* Timeline indicator */}
        <div className="flex gap-2 pt-4">
          {steps.map((_, idx) => (
            <motion.button
              key={idx}
              onClick={() => setStep(idx)}
              className={`h-2 rounded-full transition-all cursor-pointer ${
                idx === step
                  ? 'bg-primary w-8'
                  : idx < step
                    ? 'bg-primary/40 w-2'
                    : 'bg-muted/40 w-2'
              }`}
              whileHover={{ scaleY: 1.5 }}
            />
          ))}
        </div>
      </motion.div>

      {/* Navigation */}
      <div className="flex gap-3 justify-between">
        <button
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
          className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          ← Anterior
        </button>

        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <Clock className="w-4 h-4" />
          ~5 min de setup
        </div>

        <button
          onClick={() => setStep(Math.min(steps.length - 1, step + 1))}
          disabled={step === steps.length - 1}
          className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center gap-2"
        >
          Siguiente
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Footer info */}
      <div className="text-center text-xs text-muted-foreground space-y-2">
        <p>💡 Tip: Puedes pausar este onboarding en cualquier momento</p>
        <p>Accede de nuevo desde el menú de ayuda</p>
      </div>
    </motion.div>
  )
}
