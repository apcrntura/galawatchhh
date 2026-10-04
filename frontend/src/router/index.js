import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import AdminView from '../views/AdminView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, props: { kind: 'staff' }, meta: { guest: true } },
    { path: '/admin-login', component: LoginView, props: { kind: 'admin' }, meta: { guest: true } },
    { path: '/', component: DashboardView, meta: { roles: ['tourism', 'lgu', 'admin'] } },
    { path: '/admin', component: AdminView, meta: { roles: ['admin'] } },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  await auth.init()
  const p = auth.profile
  if (to.meta.guest) {
    if (p) return p.role === 'admin' ? '/admin' : '/'
    return true
  }
  if (!p) return to.path.startsWith('/admin') ? '/admin-login' : '/login'
  if (to.meta.roles && !to.meta.roles.includes(p.role)) return '/'
  return true
})

export default router
