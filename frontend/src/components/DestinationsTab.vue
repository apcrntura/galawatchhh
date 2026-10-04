<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '../lib/supabase'

const emit = defineEmits(['say'])
const dests = ref([])
const cams = ref([])
const newCam = ref({})
const blank = () => ({ name: '', region: '', lat: '', lng: '', capacity: '', alert_at: '', is_live: false, sample_visitors: 0, sample_cap: 0 })
const fresh = ref(blank())

async function load() {
  const [d, c] = await Promise.all([
    supabase.from('destinations').select('*').order('name'),
    supabase.from('cameras').select('*').order('name')
  ])
  if (d.error) return emit('say', 'Could not load destinations: ' + d.error.message, false)
  dests.value = d.data.map(x => ({ ...x }))
  cams.value = c.data || []
}
onMounted(load)

const camsOf = (id) => cams.value.filter(c => c.destination_id === id)

function clean(f) {
  const lat = Number(f.lat), lng = Number(f.lng)
  const o = {
    name: String(f.name).trim(), region: String(f.region).trim(), lat, lng,
    capacity: f.capacity === '' || f.capacity == null ? null : Number(f.capacity),
    alert_at: f.alert_at === '' || f.alert_at == null ? null : Number(f.alert_at),
    is_live: !!f.is_live,
    sample_visitors: Number(f.sample_visitors) || 0,
    sample_cap: Number(f.sample_cap) || 0
  }
  const bad =
    !o.name || !o.region || f.lat === '' || f.lng === '' || Math.abs(lat) > 90 || Math.abs(lng) > 180 ||
    (o.capacity != null && !(o.capacity > 0)) || (o.alert_at != null && !(o.alert_at > 0)) ||
    !(o.sample_cap >= 0 && o.sample_cap <= 100) || !(o.sample_visitors >= 0) ||
    (o.is_live && o.capacity == null)
  if (bad) { emit('say', 'Check the fields: name, region, valid coordinates, capacity above 0 (required for live), load 0-100, visitors 0 or more.', false); return null }
  return o
}

async function save(d) {
  const o = clean(d); if (!o) return
  const { error } = await supabase.from('destinations').update(o).eq('id', d.id)
  if (error) return emit('say', error.message, false)
  emit('say', 'Destination saved.'); load()
}
async function remove(d) {
  if (!window.confirm(`Delete ${d.name} and its cameras and alerts?`)) return
  const { error } = await supabase.from('destinations').delete().eq('id', d.id)
  if (error) return emit('say', error.message, false)
  emit('say', 'Destination deleted.'); load()
}
async function add() {
  const o = clean(fresh.value); if (!o) return
  const slug = o.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 24) || 'dest'
  const id = `${slug}-${Math.random().toString(36).slice(2, 6)}`
  const { error } = await supabase.from('destinations').insert({ id, ...o, sample_trend: [0, 0, 0, 0, 0, 0, 0], sample_note: 'Added by administrator.' })
  if (error) return emit('say', error.message, false)
  fresh.value = blank(); emit('say', 'Destination added.'); load()
}

async function addCam(d) {
  const name = (newCam.value[d.id] || '').trim()
  if (!name) return emit('say', 'Enter a camera name.', false)
  const { error } = await supabase.from('cameras').insert({ destination_id: d.id, name })
  if (error) return emit('say', error.message, false)
  newCam.value[d.id] = ''; load()
}
async function setStatus(c, status) {
  const { error } = await supabase.from('cameras').update({ status }).eq('id', c.id)
  if (error) return emit('say', error.message, false)
  load()
}
async function removeCam(c) {
  const { error } = await supabase.from('cameras').delete().eq('id', c.id)
  if (error) return emit('say', error.message, false)
  load()
}
</script>

<template>
  <h2>Destinations and Cameras</h2>
  <div v-for="d in dests" :key="d.id" class="card">
    <div class="row">
      <label class="field">Name<input class="input" v-model="d.name"></label>
      <label class="field">Region<input class="input" v-model="d.region"></label>
      <label class="field">Latitude<input class="input" v-model="d.lat" style="width:110px"></label>
      <label class="field">Longitude<input class="input" v-model="d.lng" style="width:110px"></label>
      <label class="field">Capacity (100% load)<input class="input" type="number" v-model="d.capacity" style="width:110px"></label>
      <label class="field">Alert at (people)<input class="input" type="number" v-model="d.alert_at" style="width:110px"></label>
      <label class="field check"><input type="checkbox" v-model="d.is_live"> Live camera</label>
      <template v-if="!d.is_live">
        <label class="field">Sample visitors<input class="input" type="number" v-model="d.sample_visitors" style="width:110px"></label>
        <label class="field">Sample load %<input class="input" type="number" v-model="d.sample_cap" style="width:90px"></label>
      </template>
      <button class="btn gold" @click="save(d)">Save</button>
      <button class="btn" @click="remove(d)">Delete</button>
    </div>
    <div class="cams">
      Cameras:
      <span v-for="c in camsOf(d.id)" :key="c.id" class="chip">
        {{ c.name }}
        <select class="input" :value="c.status" @change="setStatus(c, $event.target.value)" style="padding:2px 4px;font-size:11px">
          <option>Active</option><option>Offline</option><option>Maintenance</option>
        </select>
        <button class="mini-btn" @click="removeCam(c)">Remove</button>
      </span>
      <span v-if="!camsOf(d.id).length">None</span>
      <input class="input" v-model="newCam[d.id]" placeholder="New camera name" style="padding:4px 8px">
      <button class="mini-btn" @click="addCam(d)">Add camera</button>
    </div>
  </div>

  <h3>Add destination</h3>
  <form class="row" @submit.prevent="add">
    <label class="field">Name<input class="input" v-model="fresh.name"></label>
    <label class="field">Region<input class="input" v-model="fresh.region"></label>
    <label class="field">Latitude<input class="input" v-model="fresh.lat" style="width:110px"></label>
    <label class="field">Longitude<input class="input" v-model="fresh.lng" style="width:110px"></label>
    <label class="field">Capacity<input class="input" type="number" v-model="fresh.capacity" style="width:110px"></label>
    <label class="field">Alert at<input class="input" type="number" v-model="fresh.alert_at" style="width:110px"></label>
    <label class="field check"><input type="checkbox" v-model="fresh.is_live"> Live camera</label>
    <button class="btn gold" type="submit">Add destination</button>
  </form>
</template>
