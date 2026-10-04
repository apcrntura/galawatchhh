<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { ROLES } from '../lib/supabase'
import UsersTab from '../components/UsersTab.vue'
import DestinationsTab from '../components/DestinationsTab.vue'
import ThresholdTab from '../components/ThresholdTab.vue'

const auth = useAuth()
const router = useRouter()
const tab = ref('users')
const msg = ref({ text: '', ok: true })
const tabs = [
  ['users', 'User Accounts'],
  ['dests', 'Destinations and Cameras'],
  ['thr', 'Overcrowding Threshold']
]
function say(text, ok = true) { msg.value = { text, ok } }
function pick(t) { tab.value = t; say('') }

async function logout() {
  await auth.logout()
  router.replace('/admin-login')
}
</script>

<template>
  <div class="adm adm-body">
    <div class="topbar">
      <div class="brand">
        <div class="brand-title">GalaWatch Admin</div>
        <div class="brand-sub">{{ auth.profile?.full_name }} ({{ ROLES[auth.profile?.role] }})</div>
      </div>
      <router-link class="export-btn" to="/" style="text-decoration:none">View Dashboard</router-link>
      <button class="logout-btn" @click="logout">Log out</button>
    </div>

    <div class="tabs">
      <button v-for="t in tabs" :key="t[0]" class="btn" :class="{ on: tab === t[0] }" @click="pick(t[0])">{{ t[1] }}</button>
    </div>
    <div class="msg" :class="msg.ok ? 'ok' : 'bad'">{{ msg.text }}</div>

    <main>
      <UsersTab v-if="tab === 'users'" @say="say" />
      <DestinationsTab v-else-if="tab === 'dests'" @say="say" />
      <ThresholdTab v-else @say="say" />
    </main>
  </div>
</template>
