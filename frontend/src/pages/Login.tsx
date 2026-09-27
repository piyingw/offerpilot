import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { App as AntdApp, Button, Card, Form, Input, Typography } from 'antd'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'

interface LoginForm {
  username: string
  password: string
}

export default function Login() {
  const { message } = AntdApp.useApp()
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)
  const setAuth = useAuthStore((s) => s.setAuth)

  if (token) {
    return <Navigate to="/" replace />
  }

  const onFinish = async (values: LoginForm) => {
    try {
      const data = await authApi.login(values)
      setAuth(data.access_token, data.user)
      message.success('登录成功')
      navigate('/', { replace: true })
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      message.error(detail ?? '登录失败，请稍后再试')
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f2f5',
      }}
    >
      <Card style={{ width: 400 }}>
        <Typography.Title level={3} style={{ textAlign: 'center', marginBottom: 4 }}>
          OfferPilot
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ textAlign: 'center' }}>
          秋招求职助手 · 模拟面试 / 半自动投递 / 进度看板
        </Typography.Paragraph>
        <Form<LoginForm> onFinish={onFinish} size="large" autoComplete="off">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名或邮箱' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名或邮箱" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 8 }}>
            <Button type="primary" htmlType="submit" block>
              登录
            </Button>
          </Form.Item>
          <Link to="/register">还没有账号？去注册</Link>
        </Form>
      </Card>
    </div>
  )
}
