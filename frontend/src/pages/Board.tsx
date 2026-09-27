import { useQuery } from '@tanstack/react-query'
import { Card, Col, Empty, Row, Space, Statistic, Tag, Typography } from 'antd'
import dayjs from 'dayjs'
import { Link } from 'react-router-dom'
import { applicationApi } from '@/api/application'
import EChart from '@/components/EChart'
import { STATUS_MAP } from '@/constants/application'
import type { EChartsCoreOption } from 'echarts/core'

export default function Board() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['applications', 'stats'],
    queryFn: applicationApi.stats,
  })

  if (isLoading || !stats) {
    return <Card loading style={{ minHeight: 300 }} />
  }

  if (stats.total === 0) {
    return (
      <Card>
        <Empty description="还没有投递记录">
          <Link to="/delivery">去投递中心添加第一条记录 →</Link>
        </Empty>
      </Card>
    )
  }

  const funnelOption: EChartsCoreOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    series: [
      {
        type: 'funnel',
        sort: 'none',
        gap: 2,
        minSize: '6%',
        label: { show: true, position: 'inside', formatter: '{b} {c}' },
        data: stats.funnel.map((f) => ({ name: f.label, value: f.count })),
      },
    ],
  }

  const pieOption: EChartsCoreOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}（{d}%）' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['38%', '66%'],
        center: ['50%', '44%'],
        label: { show: false },
        data: stats.distribution
          .filter((d) => d.count > 0)
          .map((d) => ({ name: d.label, value: d.count })),
      },
    ],
  }

  const barOption: EChartsCoreOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 24, top: 24, bottom: 32 },
    xAxis: { type: 'category', data: stats.weekly.map((w) => w.week) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        type: 'bar',
        name: '投递量',
        data: stats.weekly.map((w) => w.count),
        barMaxWidth: 32,
        itemStyle: { color: '#2563eb', borderRadius: [4, 4, 0, 0] },
      },
    ],
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="总投递" value={stats.total} suffix="条" />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="进行中" value={stats.active} suffix="条" />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="Offer"
              value={stats.offers}
              suffix="个"
              valueStyle={{ color: stats.offers > 0 ? '#3f8600' : undefined }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="已挂 / 终止"
              value={stats.rejected}
              suffix="条"
              valueStyle={{ color: stats.rejected > 0 ? '#cf1322' : undefined }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="投递漏斗（累计到达各阶段）">
            <EChart option={funnelOption} height={340} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="当前状态分布">
            <EChart option={pieOption} height={340} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="最近 8 周投递量">
            <EChart option={barOption} height={300} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="最近动态">
            {stats.recent_events.length === 0 ? (
              <Empty description="暂无动态" />
            ) : (
              <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                {stats.recent_events.map((e) => {
                  const to = STATUS_MAP[e.to_status]
                  return (
                    <div key={e.id} style={{ marginBottom: 12 }}>
                      <Space wrap>
                        <Typography.Text strong>
                          {e.company} · {e.position}
                        </Typography.Text>
                        {e.from_status && (
                          <>
                            <Tag>{STATUS_MAP[e.from_status]?.label ?? e.from_status}</Tag>
                            <span>→</span>
                          </>
                        )}
                        <Tag color={to?.color}>{to?.label ?? e.to_status}</Tag>
                        <Typography.Text type="secondary">
                          {dayjs(e.happened_at).format('MM-DD HH:mm')}
                        </Typography.Text>
                      </Space>
                      {e.note && (
                        <Typography.Paragraph
                          type="secondary"
                          style={{ marginBottom: 0, marginTop: 2 }}
                        >
                          {e.note}
                        </Typography.Paragraph>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
