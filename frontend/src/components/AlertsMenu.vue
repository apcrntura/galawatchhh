<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useData } from '../stores/data'

const data = useData()
const open = ref(false)
const close = () => { open.value = false }
onMounted(() => document.addEventListener('click', close))
onBeforeUnmount(() => document.removeEventListener('click', close))

function pick(id) { data.selectedId = id; open.value = false }
const name = (id) => data.destinations.find(d => d.id === id)?.name || id
const when = (t) => new Date(t).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
</script>

<template>
  <div class="alerts-wrap">
    <button class="icon-btn" title="Overcrowding alerts" @click.stop="open = !open">
      Alerts<span v-if="data.highs.length" class="badge-count" style="display:flex">{{ data.highs.length }}</span>
    </button>
    <div class="alerts-panel" :class="{ open }" @click.stop>
      <div class="alerts-head">Overcrowding Alerts</div>
      <div class="alerts-list">
        <div v-if="!data.highs.length" class="alerts-empty">No active overcrowding alerts.</div>
        <div v-for="d in data.highs" :key="d.id" class="alert-row" @click="pick(d.id)">
          <div class="alert-row-top">
            <div class="alert-row-name">{{ d.name }}</div>
            <div class="alert-row-cap">{{ d.cap }}%</div>
          </div>
          <div class="alert-row-msg">{{ d.note }}</div>
        </div>
        <div v-if="data.alerts.length" class="alert-log">
          <div class="alert-log-head">Alert log</div>
          <div v-for="a in data.alerts.slice(0, 5)" :key="a.id" class="log-row">
            <div>
              {{ name(a.destination_id) }}: {{ a.people_inside }} people
              <small>{{ when(a.triggered_at) }} · {{ a.status }}</small>
            </div>
            <button v-if="a.status === 'Unacknowledged'" class="mini-btn" @click="data.acknowledge(a.id)">Acknowledge</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
