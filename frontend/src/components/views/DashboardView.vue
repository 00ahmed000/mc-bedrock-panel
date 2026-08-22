<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const props = defineProps({ id: { type: String, required: true } })
const serverId = computed(() => props.id)

const status = ref({ exists: false, status: 'unknown' })
const logs = ref('')
const loadingAction = ref('')
const loadingLogs = ref(false)
const command = ref('')
const sendingCommand = ref(false)
let pollHandle = null

async function fetchStatus() {
  if (!serverId.value) return
  try {
    const { data } = await api.get(`/servers/${serverId.value}/status`)
    status.value = data
  } catch {
    // top-level polling errors aren't worth a toast every 5s
  }
}

async function fetchLogs() {
  if (!serverId.value) return
  loadingLogs.value = true
  try {
    const { data } = await api.get(`/servers/${serverId.value}/logs`, { params: { tail: 300 } })
    logs.value = data.logs || '(no log output yet)'
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not fetch logs'))
  } finally {
    loadingLogs.value = false
  }
}

async function sendCommand() {
  if (!command.value || !serverId.value) return
  sendingCommand.value = true
  try {
    await api.post(`/servers/${serverId.value}/console`, { command: command.value })
    command.value = ''
    setTimeout(fetchLogs, 600)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not send command'))
  } finally {
    sendingCommand.value = false
  }
}

async function runAction(action, confirmMessage) {
  if (!serverId.value) return
  if (confirmMessage && !window.confirm(confirmMessage)) return
  loadingAction.value = action
  try {
    await api.post(`/servers/${serverId.value}/${action}`)
    toastStore.success(`Server ${action} requested`)
    setTimeout(fetchStatus, 1500)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, `Could not ${action} the server`))
  } finally {
    loadingAction.value = ''
  }
}

const statusMeta = computed(() => {
  const s = status.value.status
  if (s === 'running') return { label: 'Online', color: 'text-emerald', dot: 'bg-emerald' }
  if (s === 'restarting') return { label: 'Restarting', color: 'text-glowstone', dot: 'bg-glowstone' }
  if (s === 'created' || s === 'paused') return { label: 'Paused', color: 'text-glowstone', dot: 'bg-glowstone' }
  if (s === 'not_found') return { label: 'Not started yet', color: 'text-ink-dim', dot: 'bg-ink-dim' }
  if (s === 'exited') return { label: 'Offline', color: 'text-redstone', dot: 'bg-redstone' }
  return { label: 'Unknown', color: 'text-ink-dim', dot: 'bg-ink-dim' }
})

const isRunning = computed(() => status.value.status === 'running')

function refreshAll() {
  fetchStatus()
  fetchLogs()
}

watch(serverId, refreshAll)

onMounted(() => {
  refreshAll()
  pollHandle = setInterval(fetchStatus, 5000)
})
onBeforeUnmount(() => {
  if (pollHandle) clearInterval(pollHandle)
})
</script>

<template>
  <Card v-if="!serverId">
    <p class="text-sm text-ink-muted">Select or create a server first.</p>
  </Card>

  <template v-else>
    <Card>
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
            <span :class="['w-3.5 h-3.5 rounded-full pulse-dot', statusMeta.dot, statusMeta.color]"></span>
          </div>
          <div>
            <p class="text-xs text-ink-muted uppercase tracking-wide mb-0.5">Server status</p>
            <p :class="['font-display text-xl font-semibold', statusMeta.color]">{{ statusMeta.label }}</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="!isRunning"
            :disabled="loadingAction === 'start'"
            @click="runAction('start')"
            class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all"
          >
            <Icon name="play" size="w-4 h-4" /> Start
          </button>
          <button
            v-if="isRunning"
            :disabled="loadingAction === 'stop'"
            @click="runAction('stop', 'Stop the server? Connected players will be disconnected.')"
            class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-redstone/15 text-redstone border border-redstone/30 text-sm font-medium hover:bg-redstone/25 disabled:opacity-40 transition-all"
          >
            <Icon name="stop" size="w-4 h-4" /> Stop
          </button>
          <button
            v-if="isRunning"
            :disabled="loadingAction === 'restart'"
            @click="runAction('restart', 'Restart the server? Connected players will be disconnected briefly.')"
            class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-ink text-sm font-medium hover:bg-white/10 disabled:opacity-40 transition-all"
          >
            <Icon name="restart" size="w-4 h-4" /> Restart
          </button>
        </div>
      </div>
    </Card>

    <Card title="Console" subtitle="Sends commands straight to the server \u2014 no leading slash needed">
      <div class="flex justify-end mb-3">
        <button
          @click="fetchLogs"
          :disabled="loadingLogs"
          class="flex items-center gap-1.5 text-xs text-ink-muted hover:text-ink px-2.5 py-1.5 rounded-md hover:bg-white/5 transition-colors"
        >
          <Icon name="restart" size="w-3.5 h-3.5" />
          {{ loadingLogs ? 'Refreshing\u2026' : 'Refresh' }}
        </button>
      </div>
      <pre class="font-mono text-xs text-ink-muted bg-black/30 rounded-xl p-4 max-h-96 overflow-auto whitespace-pre-wrap leading-relaxed mb-3">{{ logs }}</pre>

      <form @submit.prevent="sendCommand" class="flex items-center gap-2">
        <Icon name="terminal" size="w-4 h-4" class="text-ink-dim shrink-0" />
        <input
          v-model="command"
          type="text"
          :disabled="!isRunning || sendingCommand"
          placeholder="say hello, gamerule keepinventory true, kick PlayerName\u2026"
          class="flex-1 rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm font-mono text-ink placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors disabled:opacity-40"
        />
        <button
          type="submit"
          :disabled="!isRunning || !command || sendingCommand"
          class="px-4 py-2 rounded-lg bg-lapis/15 text-lapis border border-lapis/30 text-sm font-medium hover:bg-lapis/25 disabled:opacity-40 transition-all shrink-0"
        >
          Send
        </button>
      </form>
      <p v-if="!isRunning" class="text-xs text-ink-dim mt-2">Start the server to enable the console.</p>
    </Card>
  </template>
</template>
