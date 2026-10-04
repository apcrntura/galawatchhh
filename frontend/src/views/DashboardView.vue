<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { useData } from '../stores/data'
import { ROLES } from '../lib/supabase'
import DestinationList from '../components/DestinationList.vue'
import MapPanel from '../components/MapPanel.vue'
import DetailsPanel from '../components/DetailsPanel.vue'
import AlertsMenu from '../components/AlertsMenu.vue'
import ReportModal from '../components/ReportModal.vue'

const auth = useAuth()
const data = useData()
const router = useRouter()

const dateIn = ref(new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila' }).format(new Date()))
const period = ref('1')
const PERIOD_LABEL = { '1': 'Today', '6.2': 'This week', '24': 'This month' }
const showReport = ref(false)

const filterText = computed(() => {
  const label = new Date(dateIn.value + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return { label, period: PERIOD_LABEL[period.value] }
})
function onPeriod() { data.periodMult = parseFloat(period.value) }

async function logout() {
  const wasAdmin = auth.isAdmin
  data.unsubscribe()
  await auth.logout()
  router.replace(wasAdmin ? '/admin-login' : '/login')
}

onMounted(async () => { await data.load(); data.subscribe() })
onBeforeUnmount(() => data.unsubscribe())
</script>

<template>
  <div class="topbar">
    <div class="brand">
      <div class="brand-title">GalaWatch</div>
      <div class="brand-sub">Tourist Traffic Monitoring &middot; Department of Tourism</div>
    </div>
    <div class="ctrl"><label>Date</label><input type="date" v-model="dateIn"></div>
    <div class="ctrl">
      <label>Period</label>
      <select v-model="period" @change="onPeriod">
        <option value="1">Today</option>
        <option value="6.2">This week</option>
        <option value="24">This month</option>
      </select>
    </div>
    <AlertsMenu />
    <span id="who">{{ auth.profile?.full_name }} ({{ ROLES[auth.profile?.role] }})</span>
    <router-link v-if="auth.isAdmin" class="export-btn" to="/admin" style="text-decoration:none">Admin Panel</router-link>
    <button class="export-btn" @click="showReport = true">Export Report</button>
    <span class="badge-live">Live</span>
    <button class="logout-btn" @click="logout">Log out</button>
  </div>
  <div v-if="data.error" class="error-banner">{{ data.error }}</div>

  <div class="layout">
    <div class="left">
      <div class="panel-title">Congestion Level</div>
      <div class="legend">
        <div class="legend-item"><div class="dot" style="background:#16a34a"></div>Low</div>
        <div class="legend-item"><div class="dot" style="background:#d97706"></div>Medium</div>
        <div class="legend-item"><div class="dot" style="background:#dc2626"></div>High</div>
      </div>
      <div class="panel-title" style="padding-top:12px">Destinations</div>
      <DestinationList />
    </div>

    <div class="map-wrap">
      <MapPanel />
      <div class="filter-tag">Showing: <b>{{ filterText.label }}</b> &middot; <b>{{ filterText.period }}</b></div>
      <div class="map-legend">
        <div class="map-legend-title">Congestion</div>
        <div class="map-legend-item"><div class="map-legend-swatch" style="background:#16a34a"></div>Low (&lt;{{ data.settings.medium }}%)</div>
        <div class="map-legend-item"><div class="map-legend-swatch" style="background:#d97706"></div>Medium ({{ data.settings.medium }}-{{ data.settings.high }}%)</div>
        <div class="map-legend-item"><div class="map-legend-swatch" style="background:#dc2626"></div>High (&gt;{{ data.settings.high }}%)</div>
      </div>
      <div class="map-hint">Select a destination to view details</div>
    </div>

    <DetailsPanel />
  </div>

  <div class="toast" :class="{ show: !!data.toast }">{{ data.toast }}</div>
  <ReportModal v-if="showReport" @close="showReport = false" />
</template>
