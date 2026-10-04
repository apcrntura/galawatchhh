import { defineStore } from 'pinia'
import { supabase } from '../lib/supabase'
import { derive } from '../lib/derive'

const dayFmt = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila' })

export const useData = defineStore('data', {
  state: () => ({
    destinations: [], cameras: [], counts: {}, trends: {}, alerts: [],
    settings: { medium: 40, high: 70 },
    selectedId: null, periodMult: 1, now: Date.now(),
    toast: '', toastTimer: null, warning: '', warningTimer: null, loaded: false, error: '',
    channel: null, pollTimer: null, tickTimer: null, trendTimer: null
  }),
  getters: {
    items(s) {
      return s.destinations.map(d => {
        const it = derive(d, s.counts[d.id], s.settings, s.trends[d.id], s.cameras, s.now)
        if (!it.live) it.trend = it.trend.map(v => Math.round(v * s.periodMult))
        return it
      })
    },
    selected() { return this.items.find(i => i.id === this.selectedId) || null },
    highs() { return this.items.filter(i => i.high) }
  },
  actions: {
    showToast(msg) {
      showWarning(msg) {
      this.warning = msg
      clearTimeout(this.warningTimer)
      this.warningTimer = setTimeout(() => { this.warning = '' }, 3000)
        },
      this.toast = msg
      clearTimeout(this.toastTimer)
      this.toastTimer = setTimeout(() => { this.toast = '' }, 3500)
    },
    async load() {
      this.error = ''
      const [d, c, s] = await Promise.all([
        supabase.from('destinations').select('*').order('name'),
        supabase.from('cameras').select('*'),
        supabase.from('app_settings').select('*').eq('id', 1).maybeSingle()
      ])
      if (d.error) { this.error = 'Could not load destinations: ' + d.error.message; return }
      this.destinations = d.data
      this.cameras = c.data || []
      if (s.data) this.settings = { medium: s.data.medium, high: s.data.high }
      await Promise.all([this.loadCounts(), this.loadAlerts(), ...d.data.filter(x => x.is_live).map(x => this.loadTrend(x.id))])
      if (!this.selectedId) this.selectedId = (d.data.find(x => x.is_live) || d.data[0])?.id || null
      this.loaded = true
    },
    async loadCounts() {
      const { data, error } = await supabase.from('camera_counts').select('*')
      if (error) { console.warn('camera_counts:', error.message); return }
      const map = {}
      data.forEach(r => { map[r.destination_id] = r })
      this.counts = map
    },
    async loadAlerts() {
      const { data } = await supabase.from('alerts').select('*').order('triggered_at', { ascending: false }).limit(8)
      this.alerts = data || []
    },
    // Highest number of people inside on each of the last 7 days
    async loadTrend(id) {
      const dates = [], labels = []
      for (let i = 6; i >= 0; i--) {
        const t = new Date(Date.now() - i * 86400000)
        dates.push(dayFmt.format(t))
        labels.push(t.toLocaleDateString('en-US', { weekday: 'short', timeZone: 'Asia/Manila' }))
      }
      const { data, error } = await supabase.from('camera_daily_summary')
        .select('day,peak_inside').eq('destination_id', id).gte('day', dates[0])
      if (error) { console.warn('trend:', error.message); return }
      const by = {}
      data.forEach(r => { by[r.day] = r.peak_inside || 0 })
      this.trends = { ...this.trends, [id]: { values: dates.map(k => by[k] || 0), labels } }
    },
    async acknowledge(id) {
      const { error } = await supabase.rpc('acknowledge_alert', { p_id: id })
      if (error) { this.showToast('Could not acknowledge: ' + error.message); return }
      await this.loadAlerts()
    },
    subscribe() {
      this.unsubscribe()
      this.channel = supabase.channel('galawatch-live')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'camera_counts' }, p => {
          if (p.new?.destination_id) this.counts = { ...this.counts, [p.new.destination_id]: p.new }
        })
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'alerts' }, p => {
          const d = this.destinations.find(x => x.id === p.new.destination_id)
          this.showToast(`Overcrowding alert: ${d?.name || p.new.destination_id} has ${p.new.people_inside} people inside`)
          this.loadAlerts()
        })
        .subscribe(status => console.log('Realtime status:', status))
      // Backup refresh in case Realtime is unavailable; also keeps the camera online status current
      this.pollTimer = setInterval(() => { this.loadCounts(); this.loadAlerts() }, 10000)
      this.tickTimer = setInterval(() => { this.now = Date.now() }, 5000)
      this.trendTimer = setInterval(() => this.destinations.filter(x => x.is_live).forEach(x => this.loadTrend(x.id)), 60000)
    },
    unsubscribe() {
      if (this.channel) { supabase.removeChannel(this.channel); this.channel = null }
      clearInterval(this.pollTimer); clearInterval(this.tickTimer); clearInterval(this.trendTimer)
    }
  }
})
