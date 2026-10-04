<script setup>
import { ref, computed } from 'vue'
import { useData } from '../stores/data'
import { api } from '../lib/supabase'

const emit = defineEmits(['close'])
const data = useData()

const fmtDay = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila' })
const today = fmtDay.format(new Date())
const weekAgo = fmtDay.format(new Date(Date.now() - 6 * 86400000))

const liveDests = computed(() => data.items.filter(d => d.live))
const destination = ref(liveDests.value[0]?.id || '')
const start = ref(weekAgo)
const end = ref(today)
const format = ref('xlsx')
const busy = ref(false)
const error = ref('')

function download(blob, name) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = name
  document.body.appendChild(a); a.click(); document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function snapshotCsv() {
  const rows = ['Destination,Region,Capacity Load (%),Visitors,Status']
  data.items.forEach(d => {
    const status = d.level === 'high' ? 'High' : d.level === 'med' ? 'Medium' : 'Low'
    const v = d.live ? d.visitors : Math.round(d.visitors * data.periodMult)
    rows.push(`"${d.name}","${d.region}",${d.cap},${v},${status}`)
  })
  download(new Blob([rows.join('\n')], { type: 'text/csv' }), `GalaWatch_Snapshot_${today}.csv`)
}

async function submit() {
  error.value = ''
  if (format.value === 'csv') { snapshotCsv(); data.showToast('Report exported successfully'); emit('close'); return }
  if (!destination.value) { error.value = 'Choose a destination.'; return }
  if (start.value > end.value) { error.value = 'The end date must not be earlier than the start date.'; return }
  busy.value = true
  try {
    const q = new URLSearchParams({ destination: destination.value, start: start.value, end: end.value, format: format.value })
    const res = await api('/reports?' + q.toString())
    download(await res.blob(), `GalaWatch_${destination.value}_${start.value}_to_${end.value}.${format.value}`)
    data.showToast('Report exported successfully')
    emit('close')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="modal-back" @click.self="emit('close')">
    <form class="modal" @submit.prevent="submit">
      <h3>Export Report</h3>
      <label class="field">Format
        <select class="input" v-model="format">
          <option value="xlsx">Excel report (live camera history)</option>
          <option value="pdf">PDF report (live camera history)</option>
          <option value="csv">CSV snapshot (all destinations, as shown)</option>
        </select>
      </label>
      <template v-if="format !== 'csv'">
        <label class="field">Destination
          <select class="input" v-model="destination">
            <option v-for="d in liveDests" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </label>
        <div class="row2">
          <label class="field">From <input class="input" type="date" v-model="start" required></label>
          <label class="field">To <input class="input" type="date" v-model="end" required></label>
        </div>
      </template>
      <div class="err" style="color:#dc2626;font-size:12px;min-height:16px">{{ error }}</div>
      <div class="modal-actions">
        <button type="button" class="btn" @click="emit('close')">Cancel</button>
        <button type="submit" class="btn gold" :disabled="busy">{{ busy ? 'Preparing...' : 'Export' }}</button>
      </div>
    </form>
  </div>
</template>
