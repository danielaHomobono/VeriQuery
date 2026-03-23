import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import { motion } from 'framer-motion'
import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import AuditLog from './AuditLog'
import { Activity, BarChart3 } from 'lucide-react'

const accessData = [
  { dia: 'Lun', normal: 142, anomalo: 2 },
  { dia: 'Mar', normal: 158, anomalo: 0 },
  { dia: 'Mié', normal: 134, anomalo: 1 },
  { dia: 'Jue', normal: 167, anomalo: 3 },
  { dia: 'Vie', normal: 149, anomalo: 1 },
  { dia: 'Sáb', normal: 43,  anomalo: 2 },
  { dia: 'Dom', normal: 21,  anomalo: 1 },
]

const riskData = [
  { name: 'Crítico', value: 2,  color: '#ef4444' },
  { name: 'Alto',    value: 5,  color: '#f97316' },
  { name: 'Medio',   value: 12, color: '#eab308' },
  { name: 'Bajo',    value: 31, color: '#22c55e' },
]

const hourlyData = [
  { hora: '00', accesos: 3 },
  { hora: '03', accesos: 1 },
  { hora: '06', accesos: 8 },
  { hora: '09', accesos: 47 },
  { hora: '12', accesos: 62 },
  { hora: '15', accesos: 55 },
  { hora: '18', accesos: 38 },
  { hora: '21', accesos: 12 },
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bento-card px-3 py-2 text-xs">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>{p.name}: {p.value}</p>
      ))}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="flex flex-col gap-2">
      <p className="label-xs">{title}</p>
      {children}
    </div>
  )
}

export default function DataPreviewPanel() {
  const [activeTab, setActiveTab] = useState('audit')
  const total = riskData.reduce((s, d) => s + d.value, 0)
  const { auditEvents } = useAppStore()

  return (
    <div className="p-4 flex flex-col gap-4 overflow-y-auto scrollbar-thin h-full">
      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        <button 
          onClick={() => setActiveTab('audit')}
          className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === 'audit' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Activity className="w-4 h-4" />
          Auditoría
        </button>
        <button 
          onClick={() => setActiveTab('analytics')}
          className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === 'analytics' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Análisis
        </button>
      </div>

      {/* Audit Log Tab */}
      {activeTab === 'audit' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-1 min-h-0 flex flex-col"
        >
          <div className="flex items-center justify-between mb-3">
            <p className="label-xs">Registro de Auditoría</p>
            {auditEvents.length > 0 && (
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-xs bg-primary/20 text-primary px-2 py-1 rounded"
              >
                {auditEvents.length}
              </motion.span>
            )}
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            <AuditLog />
          </div>
        </motion.div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6 pb-4 overflow-y-auto scrollbar-thin"
        >
          {/* KPIs */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Anomalías', value: '10', sub: 'últimos 7 días', color: 'text-destructive' },
              { label: 'Riesgo Máx.', value: 'MEDIO', sub: 'evaluado por IA', color: 'text-warning' },
              { label: 'Consultas', value: '284', sub: 'esta semana', color: 'text-primary' },
              { label: 'IPs bloqueadas', value: '3', sub: 'en cuarentena', color: 'text-success' },
            ].map(k => (
              <div key={k.label} className="bento-card p-4">
                <p className="text-xs text-muted-foreground">{k.label}</p>
                <p className={`text-2xl font-bold mt-0.5 ${k.color}`}>{k.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{k.sub}</p>
              </div>
            ))}
          </div>

          {/* Accesos por día */}
          <Section title="Accesos diarios">
            <div className="bento-card p-3">
              <ResponsiveContainer width="100%" height={110}>
                <AreaChart data={accessData} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gNormal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#0284c7" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#0284c7" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gAnomalo" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="dia" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="normal"  name="Normal"  stroke="#0284c7" fill="url(#gNormal)"  strokeWidth={1.5} />
                  <Area type="monotone" dataKey="anomalo" name="Anómalo" stroke="#ef4444" fill="url(#gAnomalo)" strokeWidth={1.5} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Section>

          {/* Distribución de riesgo */}
          <Section title="Distribución de riesgo">
            <div className="bento-card p-3 flex items-center gap-4">
              <ResponsiveContainer width={90} height={90}>
                <PieChart>
                  <Pie data={riskData} cx="50%" cy="50%" innerRadius={26} outerRadius={42} dataKey="value" strokeWidth={0}>
                    {riskData.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col gap-1.5 flex-1">
                {riskData.map(d => (
                  <div key={d.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ background: d.color }} />
                      <span className="text-muted-foreground">{d.name}</span>
                    </div>
                    <span className="font-medium text-foreground">{Math.round(d.value / total * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </Section>

          {/* Accesos por hora */}
          <Section title="Accesos por hora del día">
            <div className="bento-card p-3">
              <ResponsiveContainer width="100%" height={90}>
                <BarChart data={hourlyData} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
                  <XAxis dataKey="hora" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="accesos" name="Accesos" fill="#0284c7" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Section>
        </motion.div>
      )}
    </div>
  )
}