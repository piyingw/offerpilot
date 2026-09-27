import client from './client'

export interface ResumeContent {
  basic_info?: { name?: string; email?: string; phone?: string }
  education?: { school?: string; major?: string; degree?: string; start?: string; end?: string }[]
  experiences?: {
    company?: string
    role?: string
    start?: string
    end?: string
    highlights?: string[]
  }[]
  projects?: { name?: string; role?: string; tech_stack?: string[]; highlights?: string[] }[]
  skills?: string[]
}

export type ParseStatus = 'success' | 'raw' | 'pending'

export interface ResumeItem {
  id: number
  filename: string
  parse_status: ParseStatus
  created_at: string
  content: ResumeContent | null
}

export const resumeApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post<ResumeItem>('/resumes', form).then((r) => r.data)
  },
  list: () => client.get<ResumeItem[]>('/resumes').then((r) => r.data),
  get: (id: number) => client.get<ResumeItem>(`/resumes/${id}`).then((r) => r.data),
  remove: (id: number) => client.delete(`/resumes/${id}`),
}
