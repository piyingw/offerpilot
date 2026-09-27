import { Card, Col, Row, Statistic, Timeline, Typography } from 'antd'
import { useAuthStore } from '@/stores/authStore'

const MILESTONES: { label: string; desc: string; state: 'finish' | 'processing' | 'pending' }[] = [
  { label: 'M0 项目脚手架', desc: 'monorepo · Docker Compose · CI · JWT 认证', state: 'finish' },
  { label: 'M1 模拟面试 MVP', desc: '简历解析 · AI 面试官 · 评分复盘报告', state: 'processing' },
  { label: 'M2 进度看板', desc: '投递漏斗 · 时间线 · 统计', state: 'pending' },
  { label: 'M3 自动投递', desc: '岗位抓取 · 匹配打分 · 确认队列 · Playwright 执行器', state: 'pending' },
  { label: 'M4 语音面试', desc: 'TTS + ASR 实时语音对话', state: 'pending' },
  { label: 'M5 开源打磨', desc: '文档 · 一键部署 · 发布', state: 'pending' },
]

const TIMELINE_COLOR = { finish: 'green', processing: 'blue', pending: 'gray' } as const

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)

  return (
    <div>
      <Typography.Title level={4}>
        你好，{user?.username ?? '求职者'} 👋
      </Typography.Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="简历" value={0} suffix="份" />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="模拟面试" value={0} suffix="场" />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="投递记录" value={0} suffix="条" />
          </Card>
        </Col>
        <Col span={24}>
          <Card title="开发路线">
            <Timeline
              items={MILESTONES.map((m) => ({
                color: TIMELINE_COLOR[m.state],
                children: (
                  <>
                    <Typography.Text strong>{m.label}</Typography.Text>
                    <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                      {m.desc}
                    </Typography.Paragraph>
                  </>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
