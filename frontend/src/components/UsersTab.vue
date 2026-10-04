<script setup>
import { ref, onMounted } from 'vue'
import { supabase, api, ROLES } from '../lib/supabase'
import { useAuth } from '../stores/auth'

const emit = defineEmits(['say'])
const auth = useAuth()
const users = ref([])
const form = ref({ full_name: '', username: '', role: 'tourism', password: '' })
const busy = ref(false)

async function load() {
  const { data, error } = await supabase.from('profiles').select('*').order('created_at')
  if (error) return emit('say', 'Could not load users: ' + error.message, false)
  users.value = data
}
onMounted(load)

const isMe = (u) => u.id === auth.profile.id

async function add() {
  const f = form.value
  const username = f.username.trim().toLowerCase()
  if (!f.full_name.trim() || !username) return emit('say', 'Full name and username are required.', false)
  if (!/^[a-z0-9._-]{3,30}$/.test(username)) return emit('say', 'Username: 3 to 30 letters, numbers, dot, dash or underscore.', false)
  if (f.password.length < 8) return emit('say', 'Password must be at least 8 characters.', false)
  busy.value = true
  try {
    await api('/admin/users', { method: 'POST', body: JSON.stringify({ full_name: f.full_name.trim(), username, role: f.role, password: f.password }) })
    form.value = { full_name: '', username: '', role: 'tourism', password: '' }
    emit('say', 'User added.')
    await load()
  } catch (e) { emit('say', e.message, false) } finally { busy.value = false }
}

async function toggle(u) {
  if (isMe(u)) return emit('say', 'You cannot disable your own account.', false)
  const { error } = await supabase.from('profiles').update({ active: !u.active }).eq('id', u.id)
  if (error) return emit('say', error.message, false)
  emit('say', 'Saved.'); load()
}

async function reset(u) {
  const p = window.prompt(`New password for ${u.username} (minimum 8 characters)`)
  if (!p) return
  if (p.length < 8) return emit('say', 'Password not changed: minimum 8 characters.', false)
  try { await api(`/admin/users/${u.id}/password`, { method: 'POST', body: JSON.stringify({ password: p }) }); emit('say', 'Password changed.') }
  catch (e) { emit('say', e.message, false) }
}

async function remove(u) {
  if (isMe(u)) return emit('say', 'You cannot delete your own account.', false)
  if (!window.confirm(`Delete ${u.username}? This cannot be undone.`)) return
  try { await api(`/admin/users/${u.id}`, { method: 'DELETE' }); emit('say', 'User deleted.'); load() }
  catch (e) { emit('say', e.message, false) }
}
</script>

<template>
  <h2>User Accounts</h2>
  <table>
    <thead><tr><th>Name</th><th>Username</th><th>Role</th><th>Status</th><th></th></tr></thead>
    <tbody>
      <tr v-for="u in users" :key="u.id">
        <td>{{ u.full_name }}</td><td>{{ u.username }}</td><td>{{ ROLES[u.role] }}</td>
        <td>{{ u.active ? 'Active' : 'Disabled' }}</td>
        <td>
          <button class="mini-btn" @click="toggle(u)">{{ u.active ? 'Disable' : 'Enable' }}</button>
          <button class="mini-btn" @click="reset(u)">Reset password</button>
          <button class="mini-btn" @click="remove(u)">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Add user</h3>
  <form class="row" @submit.prevent="add">
    <label class="field">Full name<input class="input" v-model="form.full_name"></label>
    <label class="field">Username<input class="input" v-model="form.username" autocomplete="off"></label>
    <label class="field">Role
      <select class="input" v-model="form.role">
        <option value="tourism">Tourism Officer</option>
        <option value="lgu">LGU Officer</option>
        <option value="admin">System Admin</option>
      </select>
    </label>
    <label class="field">Password<input class="input" type="password" v-model="form.password" autocomplete="new-password" placeholder="Minimum 8 characters"></label>
    <button class="btn gold" type="submit" :disabled="busy">{{ busy ? 'Adding...' : 'Add user' }}</button>
  </form>
</template>
