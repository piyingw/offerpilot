import { Navigate, Route, Routes } from 'react-router-dom'
import RequireAuth from '@/components/RequireAuth'
import ComingSoon from '@/components/ComingSoon'
import BasicLayout from '@/layouts/BasicLayout'
import Dashboard from '@/pages/Dashboard'
import InterviewList from '@/pages/InterviewList'
import InterviewRoom from '@/pages/InterviewRoom'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import ResumeCenter from '@/pages/ResumeCenter'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <BasicLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="resume" element={<ResumeCenter />} />
        <Route path="interview" element={<InterviewList />} />
        <Route path="interview/:id" element={<InterviewRoom />} />
        <Route path="delivery" element={<ComingSoon title="投递中心" />} />
        <Route path="board" element={<ComingSoon title="进度看板" />} />
        <Route path="settings" element={<ComingSoon title="设置" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
