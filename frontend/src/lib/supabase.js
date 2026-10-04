import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const key = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!url || !key) {
  console.error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. Check your .env file or Vercel environment variables.')
}

export const supabase = createClient(url || 'http://invalid.local', key || 'missing')
export const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
export const ROLES = { tourism: 'Tourism Officer', lgu: 'LGU Officer', admin: 'System Admin' }

// Usernames are stored as a hidden email so Supabase Auth can be used.
export const EMAIL_DOMAIN = 'galawatch.app'
export const toEmail = (u) => {
  const v = String(u || '').trim().toLowerCase()
  return v.includes('@') ? v : `${v}@${EMAIL_DOMAIN}`
}

// Call the FastAPI service with the signed-in user's token.
export async function api(path, options = {}) {
  if (!API_URL) throw new Error('VITE_API_URL is not set.')
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  const res = await fetch(API_URL + path, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  })
  if (!res.ok) {
    let msg = `Request failed (${res.status})`
    try { const j = await res.json(); if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail) } catch {}
    throw new Error(msg)
  }
  return res
}
