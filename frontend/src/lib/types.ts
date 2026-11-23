export interface User {
  id: number
  email: string
  name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed'
export type BusinessStatus = 'pending' | 'researching' | 'done' | 'failed'
export type Level = 'high' | 'medium' | 'low'

export interface Job {
  id: string
  filename: string
  status: JobStatus
  total: number
  processed: number
  failed_count: number
  error: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
  owner: User
}

export interface UploadResult {
  job: Job
  ignored_columns: string[]
}

export interface OfferMatch {
  id: string
  name: string
  reason: string
}

export interface Business {
  id: number
  position: number
  status: BusinessStatus
  business_name: string
  website: string
  city: string
  country: string
  final_url: string | null
  site_status: string | null
  industry: string | null
  summary: string | null
  services: string[] | null
  size_estimate: string | null
  gaps: string[] | null
  offers: OfferMatch[] | null
  priority: Level | null
  outreach_angle: string | null
  confidence: Level | null
  mode: string | null
  error: string | null
}

export interface BusinessPage {
  items: Business[]
  total: number
}
