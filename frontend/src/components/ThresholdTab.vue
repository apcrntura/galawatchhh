<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '../lib/supabase'

const emit = defineEmits(['say'])
const medium = ref(40)
const high = ref(70)

onMounted(async () => {
  const { data } = await supabase.from('app_settings').select('*').eq('id', 1).maybeSingle()
  if (data) { medium.value = data.medium; high.value = data.high }
})

async function save() {
  const m = Number(medium.value), h = Number(high.value)
  if (!Number.isInteger(m) || !Number.isInteger(h) || !(m > 0 && m < h && h <= 100))
    return emit('say', 'Medium must be above 0 and below High, and High must be 100 or less.', false)
  const { error } = await supabase.from('app_settings').update({ medium: m, high: h }).eq('id', 1)
  if (error) return emit('say', error.message, false)
  emit('say', 'Thresholds saved. Open dashboards pick them up on next load.')
}
</script>

<template>
  <h2>Overcrowding Threshold</h2>
  <div class="card">
    <form class="row" @submit.prevent="save">
      <label class="field">Medium starts above (%)<input class="input" type="number" v-model="medium"></label>
      <label class="field">High (overcrowding alert) above (%)<input class="input" type="number" v-model="high"></label>
      <button class="btn gold" type="submit">Save thresholds</button>
    </form>
  </div>
  <p style="font-size:12px;color:#64748b">
    Live camera destinations also have their own people limit, set under Destinations and Cameras ("Alert at").
  </p>
</template>
