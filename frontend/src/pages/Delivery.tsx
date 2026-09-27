import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  App as AntdApp,
  Button,
  DatePicker,
  Descriptions,
  Drawer,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Timeline,
  Typography,
} from 'antd'
import dayjs, { type Dayjs } from 'dayjs'
import { useState } from 'react'
import { applicationApi } from '@/api/application'
import type { ApplicationDetail, ApplicationItem, ApplicationPayload } from '@/api/application'
import { resumeApi } from '@/api/resume'
import { CHANNEL_MAP, CHANNEL_OPTIONS, STATUS_MAP, STATUS_OPTIONS } from '@/constants/application'

interface FormValues {
  company: string
  position: string
  channel: string
  current_status?: string
  salary?: string
  jd_url?: string
  note?: string
  resume_id?: number
  applied_at?: Dayjs
  status_changed_at?: Dayjs
  status_note?: string
}

function toLocalIso(d: Dayjs): string {
  // 后端存本地朴素时间，避免 toISOString 的 UTC 偏移
  return d.format('YYYY-MM-DDTHH:mm:ss')
}

export default function Delivery() {
  const { message } = AntdApp.useApp()
  const queryClient = useQueryClient()
  const [form] = Form.useForm<FormValues>()

  const [q, setQ] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<ApplicationDetail | null>(null)
  const [saving, setSaving] = useState(false)
  const [detailId, setDetailId] = useState<number | null>(null)

  const { data: pageData, isLoading } = useQuery({
    queryKey: ['applications', q, statusFilter, page, pageSize],
    queryFn: () =>
      applicationApi.list({ q: q || undefined, status_filter: statusFilter, page, page_size: pageSize }),
  })
  const items = pageData?.items ?? []
  const { data: resumes = [] } = useQuery({ queryKey: ['resumes'], queryFn: resumeApi.list })
  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['application', detailId],
    queryFn: () => applicationApi.get(detailId!),
    enabled: detailId != null,
  })

  const watchedStatus = Form.useWatch('current_status', form)

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ channel: 'other', current_status: 'applied', applied_at: dayjs() })
    setModalOpen(true)
  }

  const openEdit = async (record: ApplicationItem) => {
    const full = await applicationApi.get(record.id)
    setEditing(full)
    form.resetFields()
    form.setFieldsValue({
      company: full.company,
      position: full.position,
      channel: full.channel,
      current_status: full.current_status,
      salary: full.salary ?? undefined,
      jd_url: full.jd_url ?? undefined,
      note: full.note ?? undefined,
      resume_id: full.resume_id ?? undefined,
      applied_at: dayjs(full.applied_at),
    })
    setModalOpen(true)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      const payload: ApplicationPayload = {
        company: values.company,
        position: values.position,
        channel: values.channel,
        salary: values.salary || null,
        jd_url: values.jd_url || null,
        note: values.note || null,
        resume_id: values.resume_id ?? null,
        applied_at: values.applied_at ? toLocalIso(values.applied_at) : null,
      }
      if (editing) {
        payload.status = values.current_status
        if (values.current_status !== editing.current_status) {
          payload.status_changed_at = values.status_changed_at
            ? toLocalIso(values.status_changed_at)
            : null
          payload.status_note = values.status_note || null
        }
        await applicationApi.update(editing.id, payload)
        message.success('已保存')
      } else {
        payload.current_status = values.current_status
        await applicationApi.create(payload)
        message.success('已添加投递记录')
      }
      setModalOpen(false)
      void queryClient.invalidateQueries({ queryKey: ['applications'] })
    } catch (err) {
      const msg =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        '保存失败，请稍后再试'
      message.error(msg)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await applicationApi.remove(id)
      message.success('已删除')
      void queryClient.invalidateQueries({ queryKey: ['applications'] })
    } catch {
      message.error('删除失败')
    }
  }

  const statusChanged = editing != null && watchedStatus !== editing.current_status

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input.Search
          placeholder="搜索公司 / 岗位"
          allowClear
          onSearch={(v) => {
            setQ(v.trim())
            setPage(1)
          }}
          style={{ width: 240 }}
        />
        <Select
          placeholder="状态筛选"
          allowClear
          style={{ width: 160 }}
          options={STATUS_OPTIONS}
          value={statusFilter}
          onChange={(v) => {
            setStatusFilter(v)
            setPage(1)
          }}
        />
        <Button type="primary" onClick={() => void openCreate()}>
          新增投递
        </Button>
      </Space>

      <Table<ApplicationItem>
        rowKey="id"
        loading={isLoading}
        dataSource={items}
        pagination={{
          current: page,
          pageSize,
          total: pageData?.total ?? 0,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => {
            setPage(p)
            setPageSize(ps)
          },
        }}
        columns={[
          { title: '公司', dataIndex: 'company' },
          { title: '岗位', dataIndex: 'position' },
          {
            title: '渠道',
            width: 110,
            render: (_, r) => CHANNEL_MAP[r.channel] ?? r.channel,
          },
          {
            title: '状态',
            width: 100,
            render: (_, r) => {
              const s = STATUS_MAP[r.current_status]
              return s ? <Tag color={s.color}>{s.label}</Tag> : r.current_status
            },
          },
          { title: '薪资', width: 120, render: (_, r) => r.salary || '—' },
          {
            title: '投递时间',
            width: 120,
            render: (_, r) => dayjs(r.applied_at).format('YYYY-MM-DD'),
          },
          {
            title: '更新时间',
            width: 120,
            render: (_, r) => dayjs(r.updated_at).format('YYYY-MM-DD'),
          },
          {
            title: '操作',
            width: 190,
            render: (_, r) => (
              <Space>
                <Button type="link" size="small" onClick={() => setDetailId(r.id)}>
                  详情
                </Button>
                <Button type="link" size="small" onClick={() => void openEdit(r)}>
                  编辑
                </Button>
                <Popconfirm title="确定删除该投递记录？" onConfirm={() => void handleDelete(r.id)}>
                  <Button type="link" size="small" danger>
                    删除
                  </Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? `编辑：${editing.company}` : '新增投递'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => void handleSave()}
        confirmLoading={saving}
        width={560}
        destroyOnHidden
      >
        <Form<FormValues> form={form} layout="vertical">
          <Space size="middle" style={{ display: 'flex' }}>
            <Form.Item
              name="company"
              label="公司"
              rules={[{ required: true, message: '请输入公司名' }]}
              style={{ flex: 1, minWidth: 220 }}
            >
              <Input placeholder="公司名称" maxLength={120} />
            </Form.Item>
            <Form.Item
              name="position"
              label="岗位"
              rules={[{ required: true, message: '请输入岗位' }]}
              style={{ flex: 1, minWidth: 220 }}
            >
              <Input placeholder="岗位名称" maxLength={120} />
            </Form.Item>
          </Space>
          <Space size="middle" style={{ display: 'flex' }} align="start">
            <Form.Item name="channel" label="渠道" style={{ minWidth: 140 }}>
              <Select options={CHANNEL_OPTIONS} />
            </Form.Item>
            <Form.Item name="current_status" label="当前状态" style={{ minWidth: 140 }}>
              <Select options={STATUS_OPTIONS} />
            </Form.Item>
            <Form.Item name="applied_at" label="投递时间">
              <DatePicker showTime={{ format: 'HH:mm' }} format="YYYY-MM-DD HH:mm" />
            </Form.Item>
          </Space>
          <Space size="middle" style={{ display: 'flex' }}>
            <Form.Item name="salary" label="薪资" style={{ flex: 1, minWidth: 200 }}>
              <Input placeholder="例如：15k-25k · 14薪" maxLength={60} />
            </Form.Item>
            <Form.Item name="resume_id" label="投递简历" style={{ flex: 1, minWidth: 200 }}>
              <Select
                allowClear
                placeholder="可选关联简历版本"
                options={resumes.map((r) => ({ value: r.id, label: r.filename }))}
              />
            </Form.Item>
          </Space>
          <Form.Item name="jd_url" label="JD 链接">
            <Input placeholder="https://…" maxLength={512} />
          </Form.Item>
          {statusChanged && (
            <Space size="middle" style={{ display: 'flex' }} align="start">
              <Form.Item name="status_changed_at" label="状态变更时间">
                <DatePicker showTime={{ format: 'HH:mm' }} format="YYYY-MM-DD HH:mm" />
              </Form.Item>
              <Form.Item name="status_note" label="备注" style={{ flex: 1, minWidth: 240 }}>
                <Input placeholder="例如：一面通过，约下周三二面" maxLength={255} />
              </Form.Item>
            </Space>
          )}
          <Form.Item name="note" label="笔记">
            <Input.TextArea rows={3} maxLength={2000} placeholder="面试体验、聊到的知识点、待跟进事项…" />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        open={detailId != null}
        onClose={() => setDetailId(null)}
        title={detail ? `${detail.company} · ${detail.position}` : '投递详情'}
        width={520}
      >
        {detailLoading || !detail ? null : (
          <div>
            <Descriptions
              column={1}
              bordered
              size="small"
              items={[
                {
                  key: 'status',
                  label: '当前状态',
                  children: (() => {
                    const s = STATUS_MAP[detail.current_status]
                    return s ? <Tag color={s.color}>{s.label}</Tag> : detail.current_status
                  })(),
                },
                { key: 'channel', label: '渠道', children: CHANNEL_MAP[detail.channel] ?? detail.channel },
                { key: 'salary', label: '薪资', children: detail.salary || '—' },
                {
                  key: 'applied_at',
                  label: '投递时间',
                  children: dayjs(detail.applied_at).format('YYYY-MM-DD HH:mm'),
                },
                { key: 'jd_url', label: 'JD 链接', children: detail.jd_url || '—' },
                { key: 'note', label: '笔记', children: detail.note || '—' },
              ]}
            />
            <Typography.Title level={5} style={{ marginTop: 24 }}>
              状态时间线
            </Typography.Title>
            <Timeline
              items={detail.events.map((e) => {
                const to = STATUS_MAP[e.to_status]
                return {
                  color: to?.color ?? 'blue',
                  children: (
                    <>
                      <Space>
                        <Typography.Text strong>
                          {e.from_status
                            ? `${STATUS_MAP[e.from_status]?.label ?? e.from_status} → ${to?.label ?? e.to_status}`
                            : (to?.label ?? e.to_status)}
                        </Typography.Text>
                        <Typography.Text type="secondary">
                          {dayjs(e.happened_at).format('YYYY-MM-DD HH:mm')}
                        </Typography.Text>
                      </Space>
                      {e.note && (
                        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                          {e.note}
                        </Typography.Paragraph>
                      )}
                    </>
                  ),
                }
              })}
            />
          </div>
        )}
      </Drawer>
    </div>
  )
}
