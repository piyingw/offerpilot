import { ArrowLeftOutlined, SendOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  App as AntdApp,
  Button,
  Card,
  Collapse,
  Input,
  Popconfirm,
  Progress,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { interviewApi } from '@/api/interview'
import type { MessageItem, QuestionReport, ReportItem } from '@/api/interview'
import { streamSSE } from '@/lib/sse'

const TYPE_TEXT: Record<string, string> = { resume: '简历深挖', technical: '技术面' }
const DIFF_TEXT: Record<string, string> = { easy: '基础', medium: '进阶', hard: '硬核' }

function ReportCard({ report }: { report: ReportItem }) {
  const renderList = (items: string[]) =>
    items.length === 0 ? (
      <Typography.Text type="secondary">暂无</Typography.Text>
    ) : (
      items.map((s, i) => (
        <Typography.Paragraph key={i} style={{ marginBottom: 4 }}>
          · {s}
        </Typography.Paragraph>
      ))
    )

  return (
    <Card title="面试评估报告" style={{ marginTop: 16 }}>
      <Space size="large" align="center" wrap>
        <Statistic
          title="总分"
          value={report.total_score ?? '—'}
          suffix={report.total_score != null ? '/ 100' : undefined}
        />
        {report.dimensions &&
          Object.entries(report.dimensions).map(([name, value]) => (
            <div key={name} style={{ minWidth: 170 }}>
              <Typography.Text type="secondary">{name}</Typography.Text>
              <Progress percent={value} size="small" />
            </div>
          ))}
      </Space>
      {report.summary && (
        <Typography.Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
          {report.summary}
        </Typography.Paragraph>
      )}
      <Collapse
        style={{ marginTop: 16 }}
        items={[
          { key: 'strengths', label: `亮点（${report.strengths.length}）`, children: renderList(report.strengths) },
          { key: 'weaknesses', label: `不足（${report.weaknesses.length}）`, children: renderList(report.weaknesses) },
          { key: 'suggestions', label: `改进建议（${report.suggestions.length}）`, children: renderList(report.suggestions) },
          {
            key: 'reviews',
            label: `逐题点评（${report.question_reviews.length}）`,
            children:
              report.question_reviews.length === 0 ? (
                <Typography.Text type="secondary">暂无</Typography.Text>
              ) : (
                report.question_reviews.map((q: QuestionReport, i: number) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <Space style={{ justifyContent: 'space-between', width: '100%' }}>
                      <Typography.Text strong>{`Q${i + 1} ${q.question}`}</Typography.Text>
                      <Tag color={q.score >= 80 ? 'green' : q.score >= 60 ? 'orange' : 'red'}>
                        {q.score}
                      </Tag>
                    </Space>
                    <Typography.Paragraph type="secondary" style={{ marginBottom: 4 }}>
                      回答要点：{q.answer_summary}
                    </Typography.Paragraph>
                    <Typography.Paragraph style={{ marginBottom: 0 }}>{q.comment}</Typography.Paragraph>
                  </Card>
                ))
              ),
          },
        ]}
      />
    </Card>
  )
}

export default function InterviewRoom() {
  const { id } = useParams()
  const sessionId = Number(id)
  const { message } = AntdApp.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: session, isLoading } = useQuery({
    queryKey: ['interview', sessionId],
    queryFn: () => interviewApi.get(sessionId),
    enabled: Number.isFinite(sessionId),
  })

  const [localMsgs, setLocalMsgs] = useState<MessageItem[] | null>(null)
  const [streamingText, setStreamingText] = useState('')
  const [sending, setSending] = useState(false)
  const [finishing, setFinishing] = useState(false)
  const [input, setInput] = useState('')
  const chatRef = useRef<HTMLDivElement>(null)

  // 服务器数据每次刷新时以服务器为准（发送中的乐观消息随之清空）
  useEffect(() => {
    setLocalMsgs(null)
  }, [session])

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight })
  }, [localMsgs, streamingText])

  const msgs: MessageItem[] = localMsgs ?? session?.messages ?? []
  const finished = session?.status === 'finished'
  const shownReport: ReportItem | null = session?.report ?? null

  const send = async () => {
    const content = input.trim()
    if (!content || sending || finished) return
    setInput('')
    setSending(true)
    setLocalMsgs((prev) => [
      ...(prev ?? session?.messages ?? []),
      { id: -Date.now(), role: 'candidate', content, created_at: '' },
    ])
    let acc = ''
    setStreamingText('')
    try {
      await streamSSE(`/api/interviews/${sessionId}/answer`, { content }, (data) => {
        if (typeof data.delta === 'string') {
          acc += data.delta
          setStreamingText(acc)
        }
        if (typeof data.error === 'string') {
          message.error(data.error)
        }
      })
      if (acc) {
        setLocalMsgs((prev) => [
          ...(prev ?? session?.messages ?? []),
          { id: -Date.now(), role: 'interviewer', content: acc, created_at: '' },
        ])
      }
    } catch (err) {
      message.error((err as Error).message)
    } finally {
      setStreamingText('')
      setSending(false)
    }
  }

  const handleFinish = async () => {
    if (!session) return
    setFinishing(true)
    try {
      await interviewApi.finish(session.id)
      message.success('评估报告已生成')
      void queryClient.invalidateQueries({ queryKey: ['interview', sessionId] })
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
    } catch (err) {
      message.error((err as Error).message)
    } finally {
      setFinishing(false)
    }
  }

  if (isLoading || !session) {
    return <Spin style={{ display: 'block', margin: '80px auto' }} />
  }

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
        }}
      >
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/interview')} />
          <Typography.Title level={4} style={{ margin: 0 }}>
            {session.position_name || TYPE_TEXT[session.interview_type]}
          </Typography.Title>
          <Tag color="blue">{TYPE_TEXT[session.interview_type]}</Tag>
          <Tag>{DIFF_TEXT[session.difficulty]}</Tag>
          {session.status === 'in_progress' ? (
            <Tag color="processing">进行中</Tag>
          ) : (
            <Tag color="green">已结束</Tag>
          )}
        </Space>
        {session.status === 'in_progress' && (
          <Popconfirm
            title="确定结束面试？"
            description="结束后将生成评估报告，无法继续作答。"
            okText="结束并生成报告"
            cancelText="再想想"
            onConfirm={() => void handleFinish()}
          >
            <Button danger loading={finishing}>
              结束面试
            </Button>
          </Popconfirm>
        )}
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <div
          ref={chatRef}
          style={{
            height: 'calc(100vh - 340px)',
            minHeight: 320,
            overflowY: 'auto',
            padding: 16,
            background: '#f5f6f8',
            borderRadius: 8,
          }}
        >
          {msgs.map((m) => (
            <div
              key={m.id}
              style={{
                display: 'flex',
                justifyContent: m.role === 'candidate' ? 'flex-end' : 'flex-start',
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  maxWidth: '78%',
                  padding: '10px 14px',
                  borderRadius: 8,
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.7,
                  ...(m.role === 'candidate'
                    ? { background: '#2563eb', color: '#fff', borderBottomRightRadius: 2 }
                    : { background: '#fff', border: '1px solid #ececec', borderBottomLeftRadius: 2 }),
                }}
              >
                {m.content}
              </div>
            </div>
          ))}
          {sending && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 12 }}>
              <div
                style={{
                  maxWidth: '78%',
                  padding: '10px 14px',
                  borderRadius: 8,
                  background: '#fff',
                  border: '1px solid #ececec',
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.7,
                }}
              >
                {streamingText || '面试官正在输入…'}
              </div>
            </div>
          )}
        </div>
      </Card>

      {session.status === 'in_progress' && (
        <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
          <Input.TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault()
                void send()
              }
            }}
            placeholder="输入你的回答…（Enter 发送，Shift + Enter 换行）"
            autoSize={{ minRows: 2, maxRows: 5 }}
            disabled={sending}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            loading={sending}
            onClick={() => void send()}
          >
            发送
          </Button>
        </div>
      )}

      {finished && shownReport && <ReportCard report={shownReport} />}
    </div>
  )
}
