import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/servers' },
  { path: '/servers', name: 'servers', component: () => import('./components/views/ServersView.vue') },
  { path: '/servers/:id', redirect: (to) => `/servers/${to.params.id}/dashboard` },
  {
    path: '/servers/:id/dashboard',
    name: 'server-dashboard',
    component: () => import('./components/views/DashboardView.vue'),
    props: true,
  },
  {
    path: '/servers/:id/properties',
    name: 'server-properties',
    component: () => import('./components/views/PropertiesView.vue'),
    props: true,
  },
  {
    path: '/servers/:id/gamerules',
    name: 'server-gamerules',
    component: () => import('./components/views/GamerulesView.vue'),
    props: true,
  },
  {
    path: '/servers/:id/backups',
    name: 'server-backups',
    component: () => import('./components/views/BackupsView.vue'),
    props: true,
  },
  {
    path: '/servers/:id/update',
    name: 'server-update',
    component: () => import('./components/views/UpdateView.vue'),
    props: true,
  },
  {
    path: '/servers/:id/allowlist',
    name: 'server-allowlist',
    component: () => import('./components/views/AllowlistView.vue'),
    props: true,
  },
  {
    path: '/servers/:id/permissions',
    name: 'server-permissions',
    component: () => import('./components/views/PermissionsView.vue'),
    props: true,
  },
  {
    path: '/servers/:id/settings',
    name: 'server-settings',
    component: () => import('./components/views/ServerSettingsView.vue'),
    props: true,
  },
  { path: '/tasks', name: 'tasks', component: () => import('./components/views/TasksView.vue') },
  { path: '/sftp', name: 'sftp', component: () => import('./components/views/SftpView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/servers' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
