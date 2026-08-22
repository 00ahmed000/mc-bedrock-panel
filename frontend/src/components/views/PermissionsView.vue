<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const props = defineProps({ id: { type: String, required: true } })
const entries = ref([])
const loading = ref(true)
const saving = ref(false)
const busyXuid = ref('')
const newEntry = reactive({ xuid: '', permission: 'member' })
const serverId = computed(() => props.id)

async function load() {
  if (!serverId.value) return
  loading.value = true
  try {
    const { data } = await api.get(`/servers/${serverId.value}/permissions`)
    entries.value = data.entries
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load permissions'))
  } finally {
    loading.value = false
  }
}

async function setEntry() {
  if (!newEntry.xuid || !serverId.value) return
  saving.value = true
  try {
    const { data } = await api.post(`/servers/${serverId.value}/permissions`, { ...newEntry })
    entries.value = data.entries
    toastStore.success(`Set ${newEntry.xuid} to ${newEntry.permission}`)
    newEntry.xuid = ''
    newEntry.permission = 'member'
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not set permission'))
  } finally {
    saving.value = false
  }
}

async function removeEntry(xuid) {
  if (!window.confirm(`Remove the permission entry for "${xuid}"?`)) return
  busyXuid.value = xuid
  try {
    const { data } = await api.delete(`/servers/${serverId.value}/permissions/${encodeURIComponent(xuid)}`)
    entries.value = data.entries
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not remove entry'))
  } finally {
    busyXuid.value = ''
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
    <Card title="Set a permission" subtitle="Players need to have joined at least once so you have their XUID">
      <form @submit.prevent="setEntry" class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium text-ink-muted mb-1.5">XUID</label>
          <input
            v-model="newEntry.xuid"
            type="text"
            placeholder="25354xxxxxxxxxxx"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none transition-colors"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-ink-muted mb-1.5">Permission</label>
          <select
            v-model="newEntry.permission"
            class="rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
          >
            <option value="visitor">Visitor</option>
            <option value="member">Member</option>
            <option value="operator">Operator</option>
          </select>
        </div>
        <button
          type="submit"
          :disabled="saving || !newEntry.xuid"
          class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all"
        >
          <Icon name="plus" size="w-4 h-4" /> Set
        </button>
      </form>
    </Card>

    <Card>
      <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>
      <div v-else-if="entries.length === 0" class="text-sm text-ink-muted">No custom permissions set.</div>

      <table v-else class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-ink-dim uppercase tracking-wide border-b border-white/5">
            <th class="pb-3 font-medium">XUID</th>
            <th class="pb-3 font-medium">Permission</th>
            <th class="pb-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in entries" :key="e.xuid" class="border-b border-white/5 last:border-0">
            <td class="py-3 font-mono text-xs text-ink">{{ e.xuid }}</td>
            <td class="py-3">
              <span
                :class="[
                  'px-2 py-0.5 rounded-full text-xs font-medium border',
                  e.permission === 'operator'
                    ? 'bg-glowstone/10 text-glowstone border-glowstone/30'
                    : e.permission === 'member'
                      ? 'bg-lapis/10 text-lapis border-lapis/30'
                      : 'bg-white/5 text-ink-muted border-white/10',
                ]"
                >{{ e.permission }}</span
              >
            </td>
            <td class="py-3 text-right">
              <button
                :disabled="busyXuid === e.xuid"
                @click="removeEntry(e.xuid)"
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
