<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { serversStore } from '../../stores/servers'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const router = useRouter()

const creating = ref(false)
const busyId = ref('')
const versions = ref([])
const loadingVersions = ref(true)

const form = reactive({
  name: '',
  version: '',
  gamemode: 'survival',
  difficulty: 'easy',
  max_players: 10,
  level_seed: '',
  online_mode: true,
  mem_limit: '',
  cpu_limit: '',
})

const statusMeta = (s) => {
  if (s === 'running') return { label: 'Online', cls: 'text-emerald bg-emerald/10 border-emerald/30' }
  if (s === 'restarting') return { label: 'Restarting', cls: 'text-glowstone bg-glowstone/10 border-glowstone/30' }
  if (s === 'exited') return { label: 'Offline', cls: 'text-redstone bg-redstone/10 border-redstone/30' }
  return { label: s || 'Unknown', cls: 'text-ink-muted bg-white/5 border-white/10' }
}

async function loadVersions() {
  loadingVersions.value = true
  try {
    const { data } = await api.get('/minecraft-versions')
    versions.value = data.versions
    if (data.versions.length > 0) form.version = data.versions[0].version
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load the version list'))
  } finally {
    loadingVersions.value = false
  }
}

async function createServer() {
  if (!form.name) return
  creating.value = true
  try {
    const { data } = await api.post('/servers', { ...form })
    toastStore.success(`Creating "${data.server.name}" \u2014 installing ${form.version || 'the latest version'} in the background`)
    form.name = ''
    form.level_seed = ''
    await serversStore.refresh()
    router.push(`/servers/${data.server.id}/dashboard`)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not create server'))
  } finally {
    creating.value = false
  }
}

async function deleteServer(server) {
  if (!window.confirm(`Stop and remove the container for "${server.name}"?`)) return
  const alsoDeleteData = window.confirm(
    `Also permanently delete "${server.name}"'s world data? This cannot be undone.\n\nOK = delete everything\nCancel = keep the files (you can recreate a server pointing at them later)`,
  )
  busyId.value = server.id
  try {
    await api.delete(`/servers/${server.id}`, { params: { delete_data: alsoDeleteData } })
    toastStore.success(`Removed "${server.name}"`)
    await serversStore.refresh()
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not delete server'))
  } finally {
    busyId.value = ''
  }
}

onMounted(() => {
  serversStore.refresh()
  loadVersions()
})
</script>

<template>
  <Card title="Create a server">
    <form @submit.prevent="createServer" class="flex flex-col gap-5">
      <div class="grid sm:grid-cols-2 gap-4">
        <div class="sm:col-span-2">
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Name</label>
          <input
            v-model="form.name"
            type="text"
            placeholder="e.g. Survival, Creative Flat"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
          />
        </div>

        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Version</label>
          <div v-if="loadingVersions" class="text-sm text-ink-muted py-2">Loading\u2026</div>
          <select
            v-else
            v-model="form.version"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none transition-colors"
          >
            <option v-for="v in versions" :key="v.version" :value="v.version">{{ v.label }}</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Game mode</label>
          <select
            v-model="form.gamemode"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
          >
            <option value="survival">Survival</option>
            <option value="creative">Creative</option>
            <option value="adventure">Adventure</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Difficulty</label>
          <select
            v-model="form.difficulty"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
          >
            <option value="peaceful">Peaceful</option>
            <option value="easy">Easy</option>
            <option value="normal">Normal</option>
            <option value="hard">Hard</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Max players</label>
          <input
            v-model.number="form.max_players"
            type="number"
            min="1"
            max="200"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none transition-colors"
          />
        </div>

        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">World seed (optional)</label>
          <input
            v-model="form.level_seed"
            type="text"
            placeholder="Random if left blank"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
          />
        </div>

        <label class="flex items-center gap-2 text-sm text-ink-muted cursor-pointer sm:col-span-2">
          <input type="checkbox" v-model="form.online_mode" class="rounded border-white/20 bg-white/5" />
          Require Xbox Live authentication
        </label>
      </div>

      <details class="text-sm">
        <summary class="cursor-pointer text-ink-muted hover:text-ink w-fit">Resource limits (optional)</summary>
        <div class="grid sm:grid-cols-2 gap-4 mt-3">
          <div>
            <label class="block text-xs font-medium text-ink-muted mb-1.5">Memory limit</label>
            <input
              v-model="form.mem_limit"
              type="text"
              placeholder="e.g. 2g \u2014 blank uses the .env default"
              class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-muted mb-1.5">CPU limit (cores)</label>
            <input
              v-model="form.cpu_limit"
              type="text"
              placeholder="e.g. 1.5 \u2014 blank uses the .env default"
              class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
            />
          </div>
        </div>
      </details>

      <button
        type="submit"
        :disabled="creating || !form.name"
        class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all self-start"
      >
        <Icon name="plus" size="w-4 h-4" /> {{ creating ? 'Creating\u2026' : 'Create server' }}
      </button>
    </form>
  </Card>

  <Card title="Your servers">
    <div v-if="serversStore.loading" class="text-sm text-ink-muted">Loading\u2026</div>
    <div v-else-if="serversStore.servers.length === 0" class="text-sm text-ink-muted">No servers yet \u2014 create one above.</div>

    <div v-else class="flex flex-col gap-2">
      <router-link
        v-for="s in serversStore.servers"
        :key="s.id"
        :to="`/servers/${s.id}/dashboard`"
        class="flex items-center justify-between gap-4 rounded-xl border border-white/10 bg-white/[0.02] p-4 hover:border-white/20 hover:bg-white/[0.04] transition-colors"
      >
        <div class="min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <p class="font-medium text-ink truncate">{{ s.name }}</p>
            <span :class="['text-xs px-2 py-0.5 rounded-full border', statusMeta(s.status).cls]">{{ statusMeta(s.status).label }}</span>
          </div>
          <p class="text-xs text-ink-dim font-mono">
            port {{ s.port }}/{{ s.portv6 }} \u00b7 {{ s.installed_version || 'no version installed yet' }}
          </p>
        </div>
        <button
          :disabled="busyId === s.id"
          @click.prevent="deleteServer(s)"
          title="Delete"
          class="p-2 rounded-md text-ink-muted hover:text-redstone hover:bg-redstone/10 disabled:opacity-40 transition-colors shrink-0"
        >
          <Icon name="trash" size="w-4 h-4" />
        </button>
      </router-link>
    </div>
  </Card>
</template>
