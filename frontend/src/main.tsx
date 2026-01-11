import React from 'react'
import ReactDOM from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import AppRouter from './AppRouter'
import './index.css'

// Clerk Publishable Key (환경변수에서 가져오기)
const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || 'pk_test_Y2FyZWZ1bC1zbmlwZS04My5jbGVyay5hY2NvdW50cy5kZXYk'

if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error('VITE_CLERK_PUBLISHABLE_KEY가 설정되지 않았습니다.')
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <AppRouter />
    </ClerkProvider>
  </React.StrictMode>,
)
