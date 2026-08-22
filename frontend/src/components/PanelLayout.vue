<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { serversStore } from '../stores/servers'
import Sidebar from './Sidebar.vue'
import ToastHost from './ToastHost.vue'

const route = useRoute()

const titles = {
  servers: 'Servers',
  'server-dashboard': 'Dashboard',
  'server-properties': 'Server Properties',
  'server-gamerules': 'Gamerules',
  'server-backups': 'Backups',
  'server-update': 'Update Server',
  'server-allowlist': 'Allowlist',
  'server-permissions': 'Permissions',
  'server-settings': 'Container Settings',
  tasks: 'Scheduled Tasks',
  sftp: 'SFTP Access',
}
const title = computed(() => titles[route.name] || 'Bedrock Panel')
const currentServerId = computed(() => (typeof route.params.id === 'string' ? route.params.id : ''))

const status = ref({ exists: false, status: 'unknown' })
let pollHandle = null

async function pollStatus() {
  if (!currentServerId.value) {
    status.value = { exists: false, status: 'unknown' }
    return
  }
  try {
    const { data } = await api.get(`/servers/${currentServerId.value}/status`)
    status.value = data
  } catch {
    // silent — the badge just shows "unknown" until the next successful poll
  }
}

onMounted(() => {
  serversStore.refresh()
  pollStatus()
  pollHandle = setInterval(pollStatus, 5000)
})
onBeforeUnmount(() => {
  if (pollHandle) clearInterval(pollHandle)
})
watch(currentServerId, pollStatus)

const statusMeta = computed(() => {
  const s = status.value.status
  if (s === 'running') return { label: 'Online', dot: 'bg-emerald text-emerald' }
  if (s === 'restarting') return { label: 'Restarting', dot: 'bg-glowstone text-glowstone' }
  if (s === 'created' || s === 'paused') return { label: 'Paused', dot: 'bg-glowstone text-glowstone' }
  if (s === 'not_found') return { label: 'Not started', dot: 'bg-ink-dim text-ink-dim' }
  if (s === 'exited') return { label: 'Offline', dot: 'bg-redstone text-redstone' }
  return { label: 'Unknown', dot: 'bg-ink-dim text-ink-dim' }
})
</script>

<template>
  <div class="flex min-h-screen font-body">
    <Sidebar />

    <div class="flex-1 min-w-0">
      <header class="h-16 glass-panel border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-10">
        <h1 class="font-display font-semibold text-lg text-ink">{{ title }}</h1>
        <div v-if="currentServerId" class="flex items-center gap-2 text-sm">
          <span :class="['w-2 h-2 rounded-full pulse-dot', statusMeta.dot]"></span>
          <span class="text-ink-muted">{{ statusMeta.label }}</span>
        </div>
      </header>

      <main class="p-6 max-w-5xl">
        <router-view />
      </main>
    </div>

    <ToastHost />
  </div>
</template>
