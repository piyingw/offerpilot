import { DeleteOutlined, FileTextOutlined, InboxOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  App as AntdApp,
  Button,
  Collapse,
  Descriptions,
  Drawer,
  List,
  Popconfirm,
  Space,
  Table,
  Tag,
  Typography,
  Upload,
} from 'antd'
import type { UploadProps } from 'antd'
import dayjs from 'dayjs'
import { useState } from 'react'
import { resumeApi } from '@/api/resume'
import type { ResumeItem } from '@/api/resume'

const STATUS_TAG: Record<string, { color: string; text: string }> = {
  success: { color: 'green', text: '已解析' },
  raw: { color: 'orange', text: '仅原文' },
  pending: { color: 'blue', text: '解析中' },
}

export default function ResumeCenter() {
  const { message } = AntdApp.useApp()
  const queryClient = useQueryClient()
  const { data: resumes = [], isLoading } = useQuery({
    queryKey: ['resumes'],
    queryFn: resumeApi.list,
  })
  const [detail, setDetail] = useState<ResumeItem | null>(null)

  const customRequest: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options
    try {
      await resumeApi.upload(file as File)
      message.success('上传成功，简历已解析')
      onSuccess?.(file)
      void queryClient.invalidateQueries({ queryKey: ['resumes'] })
    } catch (err) {
      const msg =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        '上传失败，请稍后再试'
      message.error(msg)
      onError?.(err as Error)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await resumeApi.remove(id)
      message.success('已删除')
      setDetail(null)
      void queryClient.invalidateQueries({ queryKey: ['resumes'] })
    } catch {
      message.error('删除失败')
    }
  }

  const content = detail?.content

  return (
    <div>
      <Upload.Dragger
        accept=".pdf,.docx"
        multiple={false}
        showUploadList={false}
        customRequest={customRequest}
        style={{ marginBottom: 16 }}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽上传简历（PDF / DOCX，10MB 以内）</p>
        <p className="ant-upload-hint">上传后 AI 会自动解析出教育、经历、项目、技能等结构化信息</p>
      </Upload.Dragger>

      <Table<ResumeItem>
        rowKey="id"
        loading={isLoading}
        dataSource={resumes}
        pagination={false}
        columns={[
          {
            title: '文件名',
            render: (_, record) => (
              <Space>
                <FileTextOutlined />
                {record.filename}
              </Space>
            ),
          },
          {
            title: '解析状态',
            width: 120,
            render: (_, record) => {
              const tag = STATUS_TAG[record.parse_status] ?? STATUS_TAG.pending
              return <Tag color={tag.color}>{tag.text}</Tag>
            },
          },
          {
            title: '上传时间',
            width: 180,
            render: (_, record) => dayjs(record.created_at).format('YYYY-MM-DD HH:mm'),
          },
          {
            title: '操作',
            width: 160,
            render: (_, record) => (
              <Space>
                <Button type="link" size="small" onClick={() => setDetail(record)}>
                  查看
                </Button>
                <Popconfirm
                  title="确定删除该简历？"
                  onConfirm={() => void handleDelete(record.id)}
                >
                  <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Drawer
        open={!!detail}
        onClose={() => setDetail(null)}
        title={detail?.filename}
        width={540}
      >
        {content ? (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Descriptions
              size="small"
              column={1}
              bordered
              items={[
                { key: 'name', label: '姓名', children: content.basic_info?.name || '—' },
                { key: 'email', label: '邮箱', children: content.basic_info?.email || '—' },
                { key: 'phone', label: '电话', children: content.basic_info?.phone || '—' },
              ]}
            />
            <Typography.Title level={5} style={{ marginBottom: 0 }}>
              教育经历
            </Typography.Title>
            <List
              size="small"
              bordered
              dataSource={content.education ?? []}
              locale={{ emptyText: '未识别到教育经历' }}
              renderItem={(e) => (
                <List.Item>
                  {e.school} · {e.major} · {e.degree || ''} {e.start || ''}~{e.end || ''}
                </List.Item>
              )}
            />
            <Typography.Title level={5} style={{ marginBottom: 0 }}>
              工作 / 实习经历
            </Typography.Title>
            <List
              size="small"
              bordered
              dataSource={content.experiences ?? []}
              locale={{ emptyText: '未识别到工作经历' }}
              renderItem={(e) => (
                <List.Item>
                  <List.Item.Meta
                    title={`${e.company || ''} ${e.role || ''}（${e.start || ''}~${e.end || ''}）`}
                    description={(e.highlights ?? []).join('；')}
                  />
                </List.Item>
              )}
            />
            <Typography.Title level={5} style={{ marginBottom: 0 }}>
              项目经历
            </Typography.Title>
            <Collapse
              items={(content.projects ?? []).map((p, i) => ({
                key: i,
                label: (
                  <Space wrap>
                    {p.name || `项目 ${i + 1}`}
                    {(p.tech_stack ?? []).map((t) => (
                      <Tag key={t} style={{ marginInlineEnd: 0 }}>
                        {t}
                      </Tag>
                    ))}
                  </Space>
                ),
                children: (
                  <Typography.Paragraph style={{ marginBottom: 0 }}>
                    {p.role ? `角色：${p.role}。` : ''}
                    {(p.highlights ?? []).join('；')}
                  </Typography.Paragraph>
                ),
              }))}
            />
            <Typography.Title level={5} style={{ marginBottom: 0 }}>
              技能
            </Typography.Title>
            <Space wrap>
              {(content.skills ?? []).map((s) => (
                <Tag key={s} color="blue">
                  {s}
                </Tag>
              ))}
            </Space>
          </Space>
        ) : (
          <Typography.Text type="secondary">
            该简历未能结构化解析（仅保存原文），仍可在发起面试时作为 AI 上下文使用。
          </Typography.Text>
        )}
      </Drawer>
    </div>
  )
}
