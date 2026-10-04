<script setup>
import { onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useData } from '../stores/data'

const data = useData()
let map = null
let markers = {}
let fitted = false

function drawPins() {
  if (!map) return
  Object.values(markers).forEach(m => m.remove())
  markers = {}
  data.items.forEach(d => {
    const on = d.id === data.selectedId
    const html =
      `<div style="position:relative;width:16px;height:16px">` +
      (d.high ? `<div class="pin-ring" style="background:${d.color}"></div>` : '') +
      `<div class="pin-dot" style="background:${d.color};${on ? 'transform:rotate(-45deg) scale(1.3)' : ''}"></div></div>`
    const m = L.marker([Number(d.lat), Number(d.lng)], {
      icon: L.divIcon({ className: 'pin', iconSize: [16, 16], iconAnchor: [8, 16], html })
    }).addTo(map)
    m.bindTooltip(`${d.name} | ${d.cap}%`, { direction: 'top', offset: [0, -16] })
    m.on('click', () => { data.selectedId = d.id })
    markers[d.id] = m
  })
  if (!fitted && data.items.length) {
    map.fitBounds(data.items.map(d => [Number(d.lat), Number(d.lng)]), { padding: [50, 50] })
    fitted = true
  }
}

onMounted(() => {
  map = L.map('map').setView([16.9, 120.7], 8)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)
  drawPins()
})
onBeforeUnmount(() => { if (map) { map.remove(); map = null } })

const signature = () => data.items.map(d => [d.id, d.lat, d.lng, d.cap, d.color, d.high].join(',')).join('|')
watch(signature, drawPins)
watch(() => data.selectedId, drawPins)
watch(() => data.selectedId, () => {
  const d = data.selected
  if (d && map) map.flyTo([Number(d.lat), Number(d.lng)], d.live ? 17 : 12)
})
</script>

<template>
  <div id="map"></div>
</template>
