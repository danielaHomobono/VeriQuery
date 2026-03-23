import { useEffect } from 'react'
import AppLayout from './components/layout/AppLayout'
import ChatContainer from './components/chat/ChatContainer'
import DataPreviewPanel from './components/data/DataPreviewPanel'
import SecurityBadge from './components/security/SecurityBadge'
import WelcomeScreen from './components/layout/WelcomeScreen'
import { useAppStore } from './store/useAppStore'
import { useBackendConnection } from './hooks/useBackend'

export default function App() {
  const { selectedDatabase } = useAppStore()
  const { isConnected, loading, error, backendStatus } = useBackendConnection()

  useEffect(() => {
    if (isConnected) {
      console.log('✅ VeriQuery ready - Backend connected')
    } else if (!loading) {
      console.warn('⚠️ Backend not connected:', error)
    }
  }, [isConnected, loading, error])

  return (
    <>
      <AppLayout rightPanel={<DataPreviewPanel />}>
        {isConnected ? (
          selectedDatabase ? <ChatContainer /> : <WelcomeScreen />
        ) : (
          <div style={{ padding: '20px', textAlign: 'center' }}>
            {loading ? (
              <p>🔄 Conectando al backend...</p>
            ) : (
              <p style={{ color: 'red' }}>❌ Error: No se puede conectar al backend ({error})</p>
            )}
          </div>
        )}
      </AppLayout>
      <SecurityBadge />
    </>
  )
}
