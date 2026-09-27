import {
  BarChartOutlined,
  DashboardOutlined,
  FileTextOutlined,
  LogoutOutlined,
  MessageOutlined,
  SendOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Avatar, Dropdown, Layout, Menu, Space, Typography } from 'antd'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'

const { Sider, Header, Content } = Layout

const MENU_ITEMS = [
  { key: '/', icon: <DashboardOutlined />, label: '总览' },
  { key: '/resume', icon: <FileTextOutlined />, label: '简历中心' },
  { key: '/interview', icon: <MessageOutlined />, label: '模拟面试' },
  { key: '/delivery', icon: <SendOutlined />, label: '投递中心' },
  { key: '/board', icon: <BarChartOutlined />, label: '进度看板' },
  { key: '/settings', icon: <SettingOutlined />, label: '设置' },
]

export default function BasicLayout() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const handleLogout = () => {
    // 尽力吊销服务端的 refresh token，失败不阻塞本地登出
    const refreshToken = useAuthStore.getState().refreshToken
    if (refreshToken) {
      authApi.logout(refreshToken).catch(() => undefined)
    }
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220}>
        <div
          style={{
            height: 56,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
            OfferPilot
          </Typography.Title>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[pathname]}
          items={MENU_ITEMS}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            paddingInline: 24,
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
          }}
        >
          <Dropdown
            menu={{
              items: [
                {
                  key: 'logout',
                  icon: <LogoutOutlined />,
                  label: '退出登录',
                  onClick: handleLogout,
                },
              ],
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.username ?? '未登录'}</span>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
