import client from './client'

export interface MessageItem {
  id: number
  role: 'interviewer' | 'candidate'
  content: string
  created_at: string
}

export interface QuestionReport {
  question: string
  answer_summary: string
  comment: string
  score: number
}

export interface ReportItem {
  id: number
  total_score: number | null
  dimensions: Record<string, number> | null
  summary: string | null
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  question_reviews: QuestionReport[]
  created_at: string
}

export interface InterviewSession {
  id: number
  resume_id: number | null
  interview_type: 'resume' | 'technical'
  difficulty: 'easy' | 'medium' | 'hard'
  position_name: string | null
  jd_text: string | null
  status: 'in_progress' | 'finished'
  started_at: string
  ended_at: string | null
  total_score: number | null
  messages: MessageItem[]
  report: ReportItem | null
}

export interface SessionListItem {
  id: number
  interview_type: string
  difficulty: string
  position_name: string | null
  status: string
  total_score: number | null
  started_at: string
  ended_at: string | null
}

export interface CreatePayload {
  resume_id: number
  interview_type: 'resume' | 'technical'
  difficulty: 'easy' | 'medium' | 'hard'
  position_name?: string
  jd_text?: string
}

export const interviewApi = {
  create: (payload: CreatePayload) =>
    client.post<InterviewSession>('/interviews', payload).then((r) => r.data),
  list: () => client.get<SessionListItem[]>('/interviews').then((r) => r.data),
  get: (id: number) => client.get<InterviewSession>(`/interviews/${id}`).then((r) => r.data),
  remove: (id: number) => client.delete(`/interviews/${id}`),
  finish: (id: number) =>
    client.post<ReportItem>(`/interviews/${id}/finish`).then((r) => r.data),
}
