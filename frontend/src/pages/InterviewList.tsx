import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  App as AntdApp,
  Button,
  Card,
  Form,
  Input,
  Popconfirm,
  Radio,
  Select,
  Space,
  Table,
  Tag,
} from 'antd'
import dayjs from 'dayjs'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { interviewApi } from '@/api/interview'
import { resumeApi } from '@/api/resume'
import type { SessionListItem } from '@/api/interview'

const TYPE_TEXT: Record<string, string> = { resume: '简历深挖', technical: '技术面' }
const DIFF_TEXT: Record<string, string> = { easy: '基础', medium: '进阶', hard: '硬核' }

interface FormValues {
  resume_id: number
  interview_type: 'resume' | 'technical'
  difficulty: 'easy' | 'medium' | 'hard'
  position_name?: string
  jd_text?: string
}

export default function InterviewList() {
  const { message } = AntdApp.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [submitting, setSubmitting] = useState(false)

  const { data: resumes = [] } = useQuery({ queryKey: ['resumes'], queryFn: resumeApi.list })
  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['interviews'],
    queryFn: interviewApi.list,
  })

  const onFinish = async (values: FormValues) => {
    setSubmitting(true)
    try {
      const session = await interviewApi.create(values)
      message.success('面试已创建，面试官已就位')
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
      navigate(`/interview/${session.id}`)
    } catch (err) {
      const msg =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        '创建失败，请稍后再试'
      message.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await interviewApi.remove(id)
      message.success('已删除')
      void queryClient.invalidateQueries({ queryKey: ['interviews'] })
    } catch {
      message.error('删除失败')
    }
  }

  return (
    <div>
      <Card title="发起新面试" style={{ marginBottom: 16 }}>
        {resumes.length === 0 ? (
          <Alert
            type="warning"
            showIcon
            message="还没有简历"
            description={
              <span>
                请先到 <Link to="/resume">简历中心</Link> 上传一份简历，AI 面试官将基于简历内容提问。
              </span>
            }
          />
        ) : (
          <Form<FormValues>
            layout="vertical"
            onFinish={onFinish}
            initialValues={{ interview_type: 'resume', difficulty: 'medium' }}
            style={{ maxWidth: 720 }}
          >
            <Form.Item name="resume_id" label="选择简历" rules={[{ required: true, message: '请选择简历' }]}>
              <Select
                placeholder="选择要面试的简历版本"
                options={resumes.map((r) => ({ value: r.id, label: r.filename }))}
              />
            </Form.Item>
            <Space size="large" wrap>
              <Form.Item name="interview_type" label="面试类型">
                <Radio.Group
                  options={[
                    { value: 'resume', label: '简历项目深挖' },
                    { value: 'technical', label: '技术面' },
                  ]}
                  optionType="button"
                  buttonStyle="solid"
                />
              </Form.Item>
              <Form.Item name="difficulty" label="难度">
                <Radio.Group
                  options={[
                    { value: 'easy', label: '基础' },
                    { value: 'medium', label: '进阶' },
                    { value: 'hard', label: '硬核' },
                  ]}
                  optionType="button"
                />
              </Form.Item>
            </Space>
            <Form.Item name="position_name" label="目标岗位（可选）">
              <Input placeholder="例如：后端开发工程师（Java）" maxLength={120} />
            </Form.Item>
            <Form.Item name="jd_text" label="岗位 JD（可选，粘贴后提问会更有针对性）">
              <Input.TextArea rows={4} maxLength={8000} showCount placeholder="粘贴招聘 JD 全文…" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={submitting}>
              开始面试
            </Button>
          </Form>
        )}
      </Card>

      <Card title="面试记录">
        <Table<SessionListItem>
          rowKey="id"
          loading={isLoading}
          dataSource={sessions}
          pagination={false}
          columns={[
            {
              title: '类型 / 难度',
              render: (_, record) => (
                <Space>
                  <Tag color="blue">{TYPE_TEXT[record.interview_type] ?? record.interview_type}</Tag>
                  {DIFF_TEXT[record.difficulty] ?? record.difficulty}
                </Space>
              ),
            },
            {
              title: '目标岗位',
              render: (_, record) => record.position_name || '—',
            },
            {
              title: '状态',
              width: 110,
              render: (_, record) =>
                record.status === 'in_progress' ? (
                  <Tag color="processing">进行中</Tag>
                ) : (
                  <Tag color="green">已结束</Tag>
                ),
            },
            {
              title: '总分',
              width: 90,
              render: (_, record) => record.total_score ?? '—',
            },
            {
              title: '开始时间',
              width: 170,
              render: (_, record) => dayjs(record.started_at).format('YYYY-MM-DD HH:mm'),
            },
            {
              title: '操作',
              width: 170,
              render: (_, record) => (
                <Space>
                  <Button type="link" size="small" onClick={() => navigate(`/interview/${record.id}`)}>
                    {record.status === 'in_progress' ? '继续面试' : '查看回顾'}
                  </Button>
                  <Popconfirm title="确定删除该面试记录？" onConfirm={() => void handleDelete(record.id)}>
                    <Button type="link" size="small" danger>
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}
