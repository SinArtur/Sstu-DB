import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import PasswordResetRequestPage from './pages/PasswordResetRequestPage'
import PasswordResetConfirmPage from './pages/PasswordResetConfirmPage'
import DashboardPage from './pages/DashboardPage'
import BranchesPage from './pages/BranchesPage'
import MaterialsPage from './pages/MaterialsPage'
import ProfilePage from './pages/ProfilePage'
import ModerationPage from './pages/ModerationPage'
import AdminPage from './pages/AdminPage'
import SchedulePage from './pages/SchedulePage'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" />} />
        <Route path="/register" element={!isAuthenticated ? <RegisterPage /> : <Navigate to="/" />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/password-reset-request" element={<PasswordResetRequestPage />} />
        <Route path="/reset-password" element={<PasswordResetConfirmPage />} />
        
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/branches" element={<BranchesPage />} />
          <Route path="/branches/:branchId" element={<MaterialsPage />} />
          <Route path="/materials/:materialId" element={<MaterialsPage />} />
          <Route path="/schedule" element={<SchedulePage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/moderation" element={<ModerationPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

