import { defineStore } from 'pinia'
import { supabase, toEmail } from '../lib/supabase'

const IDLE_MS = 15 * 60 * 1000 // sign out after 15 minutes without activity

export const useAuth = defineStore('auth', {
  state: () => ({ profile: null, ready: false, idleTimer: null }),
  getters: {
    isAdmin: (s) => s.profile?.role === 'admin'
  },
  actions: {
    async init() {
      if (this.ready) return
      const { data } = await supabase.auth.getSession()
      if (data.session) await this.loadProfile(data.session.user.id)
      supabase.auth.onAuthStateChange((event) => {
        if (event === 'SIGNED_OUT') { this.profile = null; this.stopIdle() }
      })
      this.ready = true
      if (this.profile) this.startIdle()
    },
    async loadProfile(id) {
      const { data, error } = await supabase.from('profiles').select('*').eq('id', id).maybeSingle()
      if (error || !data || !data.active) { this.profile = null; return false }
      this.profile = data
      return true
    },
    // kind is 'staff' (Tourism / LGU officers) or 'admin'
    async login(username, password, kind) {
      const { data, error } = await supabase.auth.signInWithPassword({ email: toEmail(username), password })
      if (error) throw new Error('Invalid username or password.')
      const ok = await this.loadProfile(data.user.id)
      if (!ok) { await supabase.auth.signOut(); throw new Error('This account is disabled or has no profile.') }
      const isAdmin = this.profile.role === 'admin'
      if ((kind === 'admin') !== isAdmin) {
        await supabase.auth.signOut(); this.profile = null
        throw new Error(kind === 'admin'
          ? 'This page is for the System Admin only.'
          : 'System Admin must sign in on the admin login page.')
      }
      this.startIdle()
      return this.profile
    },
    async logout() {
      this.stopIdle()
      await supabase.auth.signOut()
      this.profile = null
    },
    startIdle() {
      this.stopIdle()
      const reset = () => {
        clearTimeout(this.idleTimer)
        this.idleTimer = setTimeout(async () => {
          await this.logout()
          window.location.href = '/login'
        }, IDLE_MS)
      }
      this._reset = reset
      ;['click', 'keydown', 'mousemove', 'touchstart'].forEach(e => window.addEventListener(e, reset, { passive: true }))
      reset()
    },
    stopIdle() {
      clearTimeout(this.idleTimer)
      if (this._reset) {
        ;['click', 'keydown', 'mousemove', 'touchstart'].forEach(e => window.removeEventListener(e, this._reset))
        this._reset = null
      }
    }
  }
})
