<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const props = defineProps({ id: { type: String, required: true } })
const entries = ref([])
const loading = ref(true)
const adding = ref(false)
const busyName = ref('')
const newEntry = reactive({ name: '', xuid: '', ignoresPlayerLimit: false })
const serverId = computed(() => props.id)

async function load() {
  if (!serverId.value) return
  loading.value = true
  try {
    const { data } = await api.get(`/servers/${serverId.value}/allowlist`)
    entries.value = data.entries
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load the allowlist'))
  } finally {
    loading.value = false
  }
}

async function addEntry() {
  if (!newEntry.name || !serverId.value) return
  adding.value = true
  try {
    const { data } = await api.post(`/servers/${serverId.value}/allowlist`, { ...newEntry })
    entries.value = data.entries
    toastStore.success(`Added ${newEntry.name}`)
    newEntry.name = ''
    newEntry.xuid = ''
    newEntry.ignoresPlayerLimit = false
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not add player'))
  } finally {
    adding.value = false
  }
}

async function removeEntry(name) {
  if (!window.confirm(`Remove "${name}" from the allowlist?`)) return
  busyName.value = name
  try {
    const { data } = await api.delete(`/servers/${serverId.value}/allowlist/${encodeURIComponent(name)}`)
    entries.value = data.entries
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not remove player'))
  } finally {
    busyName.value = ''
  }
}

watch(serverId, load)
onMounted(load)
</script>

<template>
  <Card v-if="!serverId">
    <p class="text-sm text-ink-muted">Select or create a server first.</p>
  </Card>

  <template v-else>
    <Card title="Add a player">
      <form @submit.prevent="addEntry" class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[160px]">
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Gamertag</label>
          <input
            v-model="newEntry.name"
            type="text"
            placeholder="PlayerName"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
          />
        </div>
        <div class="flex-1 min-w-[160px]">
          <label class="block text-xs font-medium text-ink-muted mb-1.5">XUID (optional)</label>
          <input
            v-model="newEntry.xuid"
            type="text"
            placeholder="Auto-fills on first join"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none transition-colors"
          />
        </div>
        <label class="flex items-center gap-2 pb-2.5 text-sm text-ink-muted cursor-pointer">
          <input type="checkbox" v-model="newEntry.ignoresPlayerLimit" class="rounded border-white/20 bg-white/5" />
          Ignores player limit
        </label>
        <button
          type="submit"
          :disabled="adding || !newEntry.name"
          class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all"
        >
          <Icon name="plus" size="w-4 h-4" /> Add
        </button>
      </form>
    </Card>

    <Card>
      <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>
      <div v-else-if="entries.length === 0" class="text-sm text-ink-muted">Nobody on the allowlist yet.</div>

      <table v-else class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-ink-dim uppercase tracking-wide border-b border-white/5">
            <th class="pb-3 font-medium">Name</th>
            <th class="pb-3 font-medium">XUID</th>
            <th class="pb-3 font-medium">Ignores limit</th>
            <th class="pb-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in entries" :key="e.name" class="border-b border-white/5 last:border-0">
            <td class="py-3 text-ink">{{ e.name }}</td>
            <td class="py-3 font-mono text-xs text-ink-muted">{{ e.xuid || '\u2014' }}</td>
            <td class="py-3 text-ink-muted">{{ e.ignoresPlayerLimit ? 'Yes' : 'No' }}</td>
            <td class="py-3 text-right">
              <button
                :disabled="busyName === e.name"
                @click="removeEntry(e.name)"
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
</template>
