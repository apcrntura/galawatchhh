<script setup>
import { computed } from 'vue'
import { useData } from '../stores/data'

const data = useData()
const d = computed(() => data.selected)
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const subtitle = computed(() => {
  if (!d.value) return 'Click any location in the list'
  const t = d.value.updatedAt
  return d.value.region + (t ? ' · Live, updated ' + new Date(t).toLocaleTimeString() : ' · Updated just now')
})

const chart = computed(() => {
  if (!d.value) return { pts: '', dots: [] }
  const vals = d.value.trend
  const labels = d.value.trendLabels || DAYS
  const mx = Math.max(...vals), mn = Math.min(...vals)
  const W = 232, H = 54, pad = 4
  const xy = vals.map((v, i) => ({
    x: pad + i * ((W - pad * 2) / 6),
    y: H - pad - ((v - mn) / (mx - mn || 1)) * (H - pad * 2),
    label: String(labels[i] || '').slice(0, 1)
  }))
  return { pts: xy.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' '), dots: xy, H }
})
const toneClass = computed(() => ({ warn: 'alert-warn', info: 'alert-info', ok: 'alert-ok' }[d.value?.tone] || 'alert-ok'))
</script>

<template>
  <div class="right">
    <div class="rp-header">
      <div class="rp-name">{{ d ? d.name : 'Select a destination' }}</div>
      <div class="rp-sub">{{ subtitle }}</div>
    </div>
    <div class="rp-body">
      <div v-if="!d" class="rp-empty">
        <div class="rp-empty-text">Select a destination to view its congestion status, visitor trend, and alerts.</div>
      </div>
      <template v-else>
        <div class="big-stat">
          <div class="big-stat-v" :style="{ color: d.color }">{{ d.cap }}%</div>
          <div class="big-stat-l">Current capacity load</div>
          <div class="big-stat-sub">
            {{ Math.round(d.live ? d.visitors : d.visitors * data.periodMult).toLocaleString() }} {{ d.live ? 'people inside' : 'visitors' }}
          </div>
          <div class="big-stat-l">Cameras: {{ d.camOnline }} of {{ d.camTotal }} online</div>
        </div>

        <div class="sub-head">Visitor trend</div>
        <svg class="trend-svg" viewBox="0 0 240 68" height="68" xmlns="http://www.w3.org/2000/svg">
          <polyline :points="chart.pts" fill="none" :stroke="d.color" stroke-width="2" stroke-linejoin="round" opacity=".25" />
          <polyline :points="chart.pts" fill="none" :stroke="d.color" stroke-width="1.8" stroke-linejoin="round" stroke-dasharray="4,2" />
          <g v-for="(p, i) in chart.dots" :key="i">
            <circle :cx="p.x.toFixed(1)" :cy="p.y.toFixed(1)" r="3" :fill="d.color" stroke="#fff" stroke-width="1.5" />
            <text :x="p.x.toFixed(1)" :y="chart.H + 2" text-anchor="middle" font-size="8" fill="#94a3b8">{{ p.label }}</text>
          </g>
        </svg>
        <div v-if="d.live" class="rp-note">Daily peak people inside, last 7 days</div>

        <div class="alert-box" :class="toneClass">
          <strong>{{ d.tone === 'warn' ? 'Warning:' : 'Status:' }}</strong> {{ d.note }}
        </div>

        <template v-if="d.live">
          <div class="sub-head" style="margin-top:20px">Live camera count</div>
          <div class="live-grid">
            <div class="live-cell"><div class="live-num">{{ d.visitors.toLocaleString() }}</div><div class="live-lbl">Inside now</div></div>
            <div class="live-cell"><div class="live-num" style="color:#16a34a">{{ (d.peopleIn ?? 0).toLocaleString() }}</div><div class="live-lbl">In</div></div>
            <div class="live-cell"><div class="live-num" style="color:#d97706">{{ (d.peopleOut ?? 0).toLocaleString() }}</div><div class="live-lbl">Out</div></div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
