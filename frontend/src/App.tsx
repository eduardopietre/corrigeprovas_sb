import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AuthProvider } from '@/contexts/AuthContext'
import {
  AnswerKeysListPage,
  CorrectionProgressPage,
  CorrectionsListPage,
  DashboardPage,
  ForgotPasswordPage,
  LoginPage,
  NewAnswerKeyPage,
  NewCorrectionPage,
  RegisterPage,
  TemplatesListPage,
} from '@/pages'

function HomePage() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold mb-4">CorrigeProvas</h1>
      <p className="text-muted-foreground mb-8">Sistema de correção automatizada de provas</p>
      <div className="flex gap-4">
        <Link
          to="/login"
          className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          Entrar
        </Link>
        <Link
          to="/register"
          className="px-6 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 transition-colors"
        >
          Cadastrar
        </Link>
      </div>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          {/* Correction routes */}
          <Route
            path="/corrections"
            element={
              <ProtectedRoute>
                <CorrectionsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/corrections/new"
            element={
              <ProtectedRoute>
                <NewCorrectionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/corrections/:jobId"
            element={
              <ProtectedRoute>
                <CorrectionProgressPage />
              </ProtectedRoute>
            }
          />
          {/* Answer key routes */}
          <Route
            path="/answer-keys"
            element={
              <ProtectedRoute>
                <AnswerKeysListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/answer-keys/new"
            element={
              <ProtectedRoute>
                <NewAnswerKeyPage />
              </ProtectedRoute>
            }
          />
          {/* Template routes */}
          <Route
            path="/templates"
            element={
              <ProtectedRoute>
                <TemplatesListPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
