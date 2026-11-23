import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'
import type { BusinessPage, Job, UploadResult } from '@/lib/types'

const POLL_MS = 1500

export const isActive = (job?: Pick<Job, 'status'>) => job?.status === 'queued' || job?.status === 'running'

export const jobKeys = {
  all: ['jobs'] as const,
  detail: (id: string) => ['jobs', id] as const,
  businesses: (id: string, page: number, version: number) => ['jobs', id, 'businesses', page, version] as const,
}

export function useJobs() {
  return useQuery({
    queryKey: jobKeys.all,
    queryFn: () => api.get<Job[]>('/jobs'),
    refetchInterval: (query) => (query.state.data?.some(isActive) ? POLL_MS * 2 : false),
  })
}

export function useJob(id: string) {
  return useQuery({
    queryKey: jobKeys.detail(id),
    queryFn: () => api.get<Job>(`/jobs/${id}`),
    refetchInterval: (query) => (isActive(query.state.data) ? POLL_MS : false),
  })
}

/**
 * `job.processed` is part of the key, so the table reloads whenever progress moves —
 * including the final update when the job completes. While live we also poll, to show
 * rows switching to "researching".
 */
export function useBusinesses(id: string, page: number, pageSize: number, job?: Job) {
  const live = isActive(job)
  return useQuery({
    queryKey: jobKeys.businesses(id, page, job?.processed ?? 0),
    enabled: Boolean(job),
    queryFn: () => api.get<BusinessPage>(`/jobs/${id}/businesses?offset=${page * pageSize}&limit=${pageSize}`),
    refetchInterval: live ? POLL_MS : false,
    placeholderData: keepPreviousData,
  })
}

export function useUploadJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return api.postForm<UploadResult>('/jobs', form)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: jobKeys.all }),
  })
}

export function useDeleteJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/jobs/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: jobKeys.all }),
  })
}
