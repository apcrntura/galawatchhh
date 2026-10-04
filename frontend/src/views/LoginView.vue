<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const props = defineProps({ kind: { type: String, default: 'staff' } })
const auth = useAuth()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const p = await auth.login(username.value, password.value, props.kind)
    router.replace(p.role === 'admin' ? '/admin' : '/')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <form class="lcard" @submit.prevent="submit">
      <div class="lt">GalaWatch</div>
      <div class="ls">{{ kind === 'admin' ? 'System Administrator Login' : 'Tourism Officer / LGU Officer Login' }}</div>
      <label class="field">Username
        <input class="input" v-model="username" autocomplete="username" required>
      </label>
      <label class="field">Password
        <input class="input" v-model="password" type="password" autocomplete="current-password" required>
      </label>
      <div class="err">{{ error }}</div>
      <button class="btn gold" type="submit" :disabled="busy">{{ busy ? 'Signing in...' : 'Sign in' }}</button>
      <router-link :to="kind === 'admin' ? '/login' : '/admin-login'">
        {{ kind === 'admin' ? 'Go to officer login' : 'Go to system admin login' }}
      </router-link>
    </form>
  </div>
</template>
