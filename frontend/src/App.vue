<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import api from './api'
import LoginView from './components/LoginView.vue'
import Sidebar from './components/Sidebar.vue'
import ToastHost from './components/ToastHost.vue'
import { authStore } from './stores/auth'

import AllowlistView from './components/views/AllowlistView.vue'
import BackupsView from './components/views/BackupsView.vue'
import DashboardView from './components/views/DashboardView.vue'
import PermissionsView from './components/views/PermissionsView.vue'
import PropertiesView from './components/views/PropertiesView.vue'
import SftpView from './components/views/SftpView.vue'
import UpdateView from './components/views/UpdateView.vue'

const activeTab = ref('dashboard')
const views = {
  dashboard: DashboardView,
  properties: PropertiesView,
  backups: BackupsView,
  update: UpdateView,
  sftp: SftpView,
  allowlist: AllowlistView,
  permissions: PermissionsView,
}
const activeView = computed(() => views[activeTab.value] || DashboardView)

const titles = {
  dashboard: 'Dashboard',
  properties: 'Server Properties',
  backups: 'Backups',
  update: 'Update Server',
  sftp: 'SFTP Access',
  allowlist: 'Allowlist',
  permissions: 'Permissions',
}

const status = ref({ exists: false, status: 'unknown' })
let pollHandle = null

async function pollStatus() {
  try {
    const { data } = await api.get('/server/status')
    status.value = data
  } catch {
    // Silent on purpose: the top bar just shows "unknown" until the next
    // successful poll rather than spamming a toast every 5 seconds.
  }
}

function startPolling() {
  pollStatus()
  pollHandle = setInterval(pollStatus, 5000)
}
function stopPolling() {
  if (pollHandle) clearInterval(pollHandle)
  pollHandle = null
}

watch(
  () => authStore.isAuthenticated,
  (isAuthed) => {
    if (isAuthed) startPolling()
    else stopPolling()
  },
  { immediate: true },
)
onBeforeUnmount(stopPolling)

const statusMeta = computed(() => {
  const s = status.value.status
  if (s === 'running') return { label: 'Online', dot: 'bg-emerald text-emerald' }
  if (s === 'restarting') return { label: 'Restarting', dot: 'bg-glowstone text-glowstone' }
  if (s === 'created' || s === 'paused') return { label: 'Paused', dot: 'bg-glowstone text-glowstone' }
  if (s === 'not_found') return { label: 'Not built yet', dot: 'bg-ink-dim text-ink-dim' }
  if (s === 'exited') return { label: 'Offline', dot: 'bg-redstone text-redstone' }
  return { label: 'Unknown', dot: 'bg-ink-dim text-ink-dim' }
})
</script>

<template>
  <LoginView v-if="!authStore.isAuthenticated" />

  <div v-else class="flex min-h-screen font-body">
    <Sidebar :active-tab="activeTab" @change="(id) => (activeTab = id)" />

    <div class="flex-1 min-w-0">
      <header class="h-16 glass-panel border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-10">
        <h1 class="font-display font-semibold text-lg text-ink">{{ titles[activeTab] }}</h1>
        <div class="flex items-center gap-2 text-sm">
          <span :class="['w-2 h-2 rounded-full pulse-dot', statusMeta.dot]"></span>
          <span class="text-ink-muted">{{ statusMeta.label }}</span>
        </div>
      </header>

      <main class="p-6 max-w-5xl">
        <Transition name="fade" mode="out-in">
          <component :is="activeView" :key="activeTab" />
        </Transition>
      </main>
    </div>

    <ToastHost />
  </div>
</template>
