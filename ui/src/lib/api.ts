const BASE = ''

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new ApiError(res.status, text || `HTTP ${res.status}`)
  }
  return res.json()
}

export interface Post {
  id: number
  text: string
  image_path: string
  scheduled_at: string | null
  status: 'draft' | 'scheduled' | 'scheduling' | 'scheduled_on_x' | 'posting' | 'posted' | 'error'
  created_at: string
  updated_at: string
  posted_at: string | null
  error_message: string | null
  retries_count: number
  tweet_url: string | null
}

export interface Profile {
  display_name: string
  username: string
  has_picture: boolean
  is_verified: boolean
  verified_type: '' | 'blue' | 'business' | 'government'
  followers_count: number
  following_count: number
  bio: string
  join_date: string
}

export interface FollowerSnapshot {
  id: number
  followers_count: number
  following_count: number
  recorded_at: string
}

export interface ProfileStats {
  profile: Omit<Profile, 'has_picture'>
  history: FollowerSnapshot[]
}

export async function fetchPosts(status?: string): Promise<Post[]> {
  const url = status ? `${BASE}/api/posts?status=${status}` : `${BASE}/api/posts`
  const res = await fetch(url)
  return handleResponse<Post[]>(res)
}

export async function fetchPost(id: number): Promise<Post> {
  const res = await fetch(`${BASE}/api/posts/${id}`)
  return handleResponse<Post>(res)
}

export async function createPost(formData: FormData): Promise<Post & { error?: string }> {
  const res = await fetch(`${BASE}/api/posts`, { method: 'POST', body: formData })
  return handleResponse<Post & { error?: string }>(res)
}

export async function updatePost(id: number, data: Partial<Post>): Promise<Post> {
  const res = await fetch(`${BASE}/api/posts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Post>(res)
}

export async function deletePost(id: number): Promise<void> {
  const res = await fetch(`${BASE}/api/posts/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new ApiError(res.status, res.statusText)
}

export async function postNow(id: number): Promise<{ success: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/posts/${id}/post-now`, { method: 'POST' })
  return handleResponse<{ success: boolean; error?: string }>(res)
}

export async function scheduleNow(id: number): Promise<{ success: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/posts/${id}/schedule-now`, { method: 'POST' })
  return handleResponse<{ success: boolean; error?: string }>(res)
}

export async function retryPost(id: number): Promise<{ success: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/posts/${id}/retry`, { method: 'POST' })
  return handleResponse<{ success: boolean; error?: string }>(res)
}

export async function removeMedia(id: number): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE}/api/posts/${id}/remove-media`, { method: 'POST' })
  return handleResponse<{ success: boolean }>(res)
}

export async function duplicatePost(id: number): Promise<Post> {
  const res = await fetch(`${BASE}/api/posts/${id}/duplicate`, { method: 'POST' })
  return handleResponse<Post>(res)
}

export async function deleteFromX(id: number): Promise<{ success: boolean; error?: string; already_deleted?: boolean }> {
  const res = await fetch(`${BASE}/api/posts/${id}/delete-from-x`, { method: 'POST' })
  return handleResponse<{ success: boolean; error?: string; already_deleted?: boolean }>(res)
}

export async function deleteScheduledFromX(id: number): Promise<{ success: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/posts/${id}/delete-scheduled-from-x`, { method: 'POST' })
  return handleResponse<{ success: boolean; error?: string }>(res)
}

export async function testConnection(): Promise<{ success: boolean; error?: string; needs_manual_intervention?: boolean }> {
  const res = await fetch(`${BASE}/api/settings/test-connection`)
  return handleResponse<{ success: boolean; error?: string; needs_manual_intervention?: boolean }>(res)
}

export async function fetchProfile(): Promise<Profile> {
  const res = await fetch(`${BASE}/api/profile`)
  return handleResponse<Profile>(res)
}

export async function fetchProfileFromX(): Promise<{ success: boolean; display_name?: string; username?: string; error?: string }> {
  const res = await fetch(`${BASE}/api/profile/fetch`, { method: 'POST' })
  return handleResponse<{ success: boolean; display_name?: string; username?: string; error?: string }>(res)
}

export async function fetchProfileStats(): Promise<ProfileStats> {
  const res = await fetch(`${BASE}/api/profile/stats`)
  return handleResponse<ProfileStats>(res)
}

export async function fetchLogs(): Promise<{ logs: string }> {
  const res = await fetch(`${BASE}/api/logs`)
  return handleResponse<{ logs: string }>(res)
}

export async function fetchPreferences(): Promise<Record<string, string>> {
  const res = await fetch(`${BASE}/api/settings/preferences`)
  return handleResponse<Record<string, string>>(res)
}

export async function savePreferences(data: Record<string, string>): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE}/api/settings/preferences`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<{ success: boolean }>(res)
}

export async function fetchEnvSettings(): Promise<Record<string, string>> {
  const res = await fetch(`${BASE}/api/settings/env`)
  return handleResponse<Record<string, string>>(res)
}

export async function saveEnvSettings(data: Record<string, string>): Promise<{ success?: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/settings/env`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<{ success?: boolean; error?: string }>(res)
}

export function profilePictureUrl(): string {
  return `${BASE}/api/profile/picture?t=${Math.floor(Date.now() / 60000)}`
}

export function uploadUrl(filename: string): string {
  return `${BASE}/uploads/${filename}`
}

export async function browseFolder(): Promise<{ path: string | null; error?: string }> {
  const res = await fetch(`${BASE}/api/browse/folder`, { method: 'POST' })
  return handleResponse<{ path: string | null; error?: string }>(res)
}

export async function browseFile(): Promise<{ path: string | null; error?: string }> {
  const res = await fetch(`${BASE}/api/browse/file`, { method: 'POST' })
  return handleResponse<{ path: string | null; error?: string }>(res)
}

export async function detectChrome(): Promise<{ chrome_path: string | null; profile_dir: string | null; detected: boolean }> {
  const res = await fetch(`${BASE}/api/detect-chrome`)
  return handleResponse<{ chrome_path: string | null; profile_dir: string | null; detected: boolean }>(res)
}

export async function connectGoogle(): Promise<{ success: boolean; error?: string; message?: string }> {
  const res = await fetch(`${BASE}/api/settings/connect-google`, { method: 'POST' })
  return handleResponse<{ success: boolean; error?: string; message?: string }>(res)
}

export async function checkGoogleConnected(): Promise<{ connected: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/settings/check-google`)
  return handleResponse<{ connected: boolean; error?: string }>(res)
}
