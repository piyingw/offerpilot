import client from './client'

export interface ApplicationEventItem {
  id: number
  from_status: string | null
  to_status: string
  happened_at: string
  note: string | null
}

export interface ApplicationItem {
  id: number
  company: string
  position: string
  channel: string
  current_status: string
  salary: string | null
  applied_at: string
  updated_at: string
}

export interface ApplicationDetail extends ApplicationItem {
  jd_url: string | null
  note: string | null
  resume_id: number | null
  created_at: string
  events: ApplicationEventItem[]
}

export interface FunnelItem {
  status: string
  label: string
  count: number
}

export interface StatusCount {
  status: string
  label: string
  count: number
}

export interface WeekCount {
  week: string
  count: number
}

export interface RecentEventItem {
  id: number
  company: string
  position: string
  from_status: string | null
  to_status: string
  happened_at: string
  note: string | null
}

export interface ApplicationPage {
  items: ApplicationItem[]
  total: number
  page: number
  page_size: number
}

export interface ApplicationStats {
  total: number
  active: number
  offers: number
  rejected: number
  funnel: FunnelItem[]
  distribution: StatusCount[]
  weekly: WeekCount[]
  recent_events: RecentEventItem[]
}

export interface ApplicationPayload {
  company: string
  position: string
  channel: string
  current_status?: string
  salary?: string | null
  jd_url?: string | null
  note?: string | null
  resume_id?: number | null
  applied_at?: string | null
  status?: string
  status_changed_at?: string | null
  status_note?: string | null
}

export const applicationApi = {
  create: (payload: ApplicationPayload) =>
    client.post<ApplicationDetail>('/applications', payload).then((r) => r.data),
  list: (params?: { q?: string; status_filter?: string; page?: number; page_size?: number }) =>
    client.get<ApplicationPage>('/applications', { params }).then((r) => r.data),
  stats: () => client.get<ApplicationStats>('/applications/stats').then((r) => r.data),
  get: (id: number) => client.get<ApplicationDetail>(`/applications/${id}`).then((r) => r.data),
  update: (id: number, payload: ApplicationPayload) =>
    client.patch<ApplicationDetail>(`/applications/${id}`, payload).then((r) => r.data),
  remove: (id: number) => client.delete(`/applications/${id}`),
}
