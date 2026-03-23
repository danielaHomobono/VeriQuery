import AppLayout from './components/layout/AppLayout'
import ChatContainer from './components/chat/ChatContainer'
import DataPreviewPanel from './components/data/DataPreviewPanel'
import SecurityBadge from './components/security/SecurityBadge'
import WelcomeScreen from './components/layout/WelcomeScreen'
import { useAppStore } from './store/useAppStore'

export default function App() {
  const { selectedDatabase } = useAppStore()

  return (
    <>
      <AppLayout rightPanel={<DataPreviewPanel />}>
        {selectedDatabase ? <ChatContainer /> : <WelcomeScreen />}
      </AppLayout>
      <SecurityBadge />
    </>
  )
}
