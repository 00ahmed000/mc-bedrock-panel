<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../../api'
import { serversStore } from '../../stores/servers'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const tasks = ref([])
const loading = ref(true)
const creating = ref(false)
const busyId = ref('')

const form = reactive({
  server_id: '',
  action: 'backup',
  schedule_type: 'daily',
  interval_minutes: 360,
  daily_hour: 4,
  daily_minute: 0,
})

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/tasks')
    tasks.value = data.tasks
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load tasks'))
  } finally {
    loading.value = false
  }
}

function serverName(id) {
  return serversStore.servers.find((s) => s.id === id)?.name || id
}

function describe(task) {
  const what = task.action === 'backup' ? 'Back up' : 'Restart'
  if (task.schedule_type === 'interval') {
    return `${what} every ${task.interval_minutes} min`
  }
  const hh = String(task.daily_hour).padStart(2, '0')
  const mm = String(task.daily_minute).padStart(2, '0')
  return `${what} daily at ${hh}:${mm}`
}

async function createTask() {
  if (!form.server_id) return
  creating.value = true
  try {
    const payload = {
      server_id: form.server_id,
      action: form.action,
      schedule_type: form.schedule_type,
      ...(form.schedule_type === 'interval'
        ? { interval_minutes: form.interval_minutes }
        : { daily_hour: form.daily_hour, daily_minute: form.daily_minute }),
    }
    await api.post('/tasks', payload)
    toastStore.success('Task scheduled')
    await load()
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not create task'))
  } finally {
    creating.value = false
  }
}

async function deleteTask(taskId) {
  if (!window.confirm('Remove this scheduled task?')) return
  busyId.value = taskId
  try {
    await api.delete(`/tasks/${taskId}`)
    tasks.value = tasks.value.filter((t) => t.task_id !== taskId)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not remove task'))
  } finally {
    busyId.value = ''
  }
}

onMounted(() => {
  if (!serversStore.loaded) serversStore.refresh()
  load()
})
</script>

<template>
  <Card title="Schedule a task" subtitle="Runs in the panel's timezone (TZ in .env)">
    <form @submit.prevent="createTask" class="flex flex-wrap items-end gap-3">
      <div class="min-w-[160px]">
        <label class="block text-xs font-medium text-ink-muted mb-1.5">Server</label>
        <select
          v-model="form.server_id"
          class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none"
        >
          <option value="" disabled>Choose a server</option>
          <option v-for="s in serversStore.servers" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </div>

      <div>
        <label class="block text-xs font-medium text-ink-muted mb-1.5">Action</label>
        <select
          v-model="form.action"
          class="rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none"
        >
          <option value="backup">Backup</option>
          <option value="restart">Restart</option>
        </select>
      </div>

      <div>
        <label class="block text-xs font-medium text-ink-muted mb-1.5">Schedule</label>
        <select
          v-model="form.schedule_type"
          class="rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none"
        >
          <option value="daily">Daily at\u2026</option>
          <option value="interval">Every N minutes</option>
        </select>
      </div>

      <template v-if="form.schedule_type === 'daily'">
        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Hour (0\u201323)</label>
          <input
            type="number"
            v-model.number="form.daily_hour"
            min="0"
            max="23"
            class="w-20 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Minute</label>
          <input
            type="number"
            v-model.number="form.daily_minute"
            min="0"
            max="59"
            class="w-20 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none"
          />
        </div>
      </template>
      <template v-else>
        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Every (minutes)</label>
          <input
            type="number"
            v-model.number="form.interval_minutes"
            min="5"
            class="w-24 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none"
          />
        </div>
      </template>

      <button
        type="submit"
        :disabled="creating || !form.server_id"
        class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all"
      >
        <Icon name="plus" size="w-4 h-4" /> Schedule
      </button>
    </form>
  </Card>

  <Card>
    <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>
    <div v-else-if="tasks.length === 0" class="text-sm text-ink-muted">No scheduled tasks yet.</div>

    <table v-else class="w-full text-sm">
      <thead>
        <tr class="text-left text-xs text-ink-dim uppercase tracking-wide border-b border-white/5">
          <th class="pb-3 font-medium">Server</th>
          <th class="pb-3 font-medium">Schedule</th>
          <th class="pb-3 font-medium text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tasks" :key="t.task_id" class="border-b border-white/5 last:border-0">
          <td class="py-3 text-ink">{{ serverName(t.server_id) }}</td>
          <td class="py-3 text-ink-muted">{{ describe(t) }}</td>
          <td class="py-3 text-right">
            <button
              :disabled="busyId === t.task_id"
              @click="deleteTask(t.task_id)"
              title="Remove"
              class="p-2 rounded-md text-ink-muted hover:text-redstone hover:bg-redstone/10 disabled:opacity-40 transition-colors"
            >
              <Icon name="trash" size="w-4 h-4" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </Card>
</template>
