<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const props = defineProps({ id: { type: String, required: true } })

const loading = ref(true)
const saving = ref(false)
const form = reactive({ restart_policy: 'unless-stopped', mem_limit: '', cpu_limit: '' })
const ports = reactive({ port: null, portv6: null })

async function load() {
  loading.value = true
  try {
    const { data } = await api.get(`/servers/${props.id}/settings`)
    form.restart_policy = data.restart_policy
    form.mem_limit = data.mem_limit
    form.cpu_limit = data.cpu_limit
    ports.port = data.port
    ports.portv6 = data.portv6
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load container settings'))
  } finally {
    loading.value = false
  }
}

async function save() {
  if (
    !window.confirm(
      'Applying this briefly recreates the server container (a few seconds of downtime) to apply the change. Continue?',
    )
  )
    return
  saving.value = true
  try {
    await api.post(`/servers/${props.id}/settings`, { ...form })
    toastStore.success('Container settings updated')
    await load()
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not update container settings'))
  } finally {
    saving.value = false
  }
}

watch(() => props.id, load)
onMounted(load)
</script>

<template>
  <Card title="Ports" subtitle="Allocated automatically when this server was created">
    <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>
    <dl v-else class="grid sm:grid-cols-2 gap-4 text-sm max-w-md">
      <div class="rounded-lg bg-white/5 border border-white/10 p-4">
        <dt class="text-xs text-ink-dim uppercase tracking-wide mb-1">IPv4 (UDP)</dt>
        <dd class="font-mono text-ink">{{ ports.port }}</dd>
      </div>
      <div class="rounded-lg bg-white/5 border border-white/10 p-4">
        <dt class="text-xs text-ink-dim uppercase tracking-wide mb-1">IPv6 (UDP)</dt>
        <dd class="font-mono text-ink">{{ ports.portv6 }}</dd>
      </div>
    </dl>
  </Card>

  <Card title="Container" subtitle="Applies directly to this server's Docker container">
    <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>

    <form v-else @submit.prevent="save" class="max-w-md flex flex-col gap-4">
      <div>
        <label class="block text-xs font-medium text-ink-muted mb-1.5">Restart policy</label>
        <select
          v-model="form.restart_policy"
          class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
        >
          <option value="unless-stopped">Restart unless manually stopped (recommended)</option>
          <option value="always">Always restart, even after a manual stop</option>
          <option value="on-failure">Restart only on crash</option>
          <option value="no">Never restart automatically</option>
        </select>
      </div>

      <div>
        <label class="block text-xs font-medium text-ink-muted mb-1.5">Memory limit</label>
        <input
          v-model="form.mem_limit"
          type="text"
          placeholder="e.g. 2g, 512m \u2014 blank = no limit"
          class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-ink-muted mb-1.5">CPU limit (cores)</label>
        <input
          v-model="form.cpu_limit"
          type="text"
          placeholder="e.g. 1.5 \u2014 blank = no limit"
          class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
        />
      </div>

      <button
        type="submit"
        :disabled="saving"
        class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all self-start"
      >
        <Icon name="save" size="w-4 h-4" />
        {{ saving ? 'Applying\u2026' : 'Apply' }}
      </button>
    </form>
  </Card>
</template>
