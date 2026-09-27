/** 与后端 app/core/status.py 保持一致 */

export interface StatusOption {
  value: string
  label: string
  color: string
}

export const STATUS_OPTIONS: StatusOption[] = [
  { value: 'applied', label: '已投递', color: 'blue' },
  { value: 'viewed', label: '已查看', color: 'cyan' },
  { value: 'written_test', label: '笔试', color: 'geekblue' },
  { value: 'interview_1', label: '一面', color: 'purple' },
  { value: 'interview_2', label: '二面', color: 'magenta' },
  { value: 'interview_3', label: '三面', color: 'volcano' },
  { value: 'hr_interview', label: 'HR面', color: 'gold' },
  { value: 'offer', label: 'Offer', color: 'green' },
  { value: 'rejected', label: '已挂', color: 'red' },
  { value: 'closed', label: '流程终止', color: 'default' },
]

export const STATUS_MAP: Record<string, StatusOption> = Object.fromEntries(
  STATUS_OPTIONS.map((s) => [s.value, s]),
)

export const CHANNEL_OPTIONS: { value: string; label: string }[] = [
  { value: 'boss', label: 'Boss直聘' },
  { value: 'zhilian', label: '智联招聘' },
  { value: '51job', label: '前程无忧' },
  { value: 'liepin', label: '猎聘' },
  { value: 'niuke', label: '牛客' },
  { value: 'official', label: '官网网申' },
  { value: 'referral', label: '内推' },
  { value: 'other', label: '其他' },
]

export const CHANNEL_MAP: Record<string, string> = Object.fromEntries(
  CHANNEL_OPTIONS.map((c) => [c.value, c.label]),
)
