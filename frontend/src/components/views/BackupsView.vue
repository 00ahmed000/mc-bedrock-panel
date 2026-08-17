<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const backups = ref([])
const loading = ref(true)
const creating = ref(false)
const busyFilename = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/backups')
    backups.value = data.backups
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load backups'))
  } finally {
    loading.value = false
  }
}

async function createBackup() {
  creating.value = true
  try {
    await api.post('/backups/create')
    toastStore.success('Backup started \u2014 refreshing the list shortly')
    setTimeout(load, 3000)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not start backup'))
  } finally {
    creating.value = false
  }
}

async function downloadBackup(filename) {
  busyFilename.value = filename
  try {
    const response = await api.get(`/backups/${encodeURIComponent(filename)}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not download backup'))
  } finally {
    busyFilename.value = ''
  }
}

async function restoreBackup(filename) {
  if (!window.confirm(`Restore "${filename}"? This overwrites the current world and config files.`)) return
  busyFilename.value = filename
  try {
    const { data } = await api.post(`/backups/restore/${encodeURIComponent(filename)}`)
    toastStore.success(data.message)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Restore failed'))
  } finally {
    busyFilename.value = ''
  }
}

async function deleteBackup(filename) {
  if (!window.confirm(`Delete "${filename}"? This cannot be undone.`)) return
  busyFilename.value = filename
  try {
    await api.delete(`/backups/${encodeURIComponent(filename)}`)
    backups.value = backups.value.filter((b) => b.filename !== filename)
    toastStore.success('Backup deleted')
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not delete backup'))
  } finally {
    busyFilename.value = ''
  }
}

onMounted(load)
</script>

<template>
  <Card title="Backups" subtitle="Snapshots include your world, server.properties, allowlist, and permissions">
    <button
      @click="createBackup"
      :disabled="creating"
      class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all"
    >
      <Icon name="backups" size="w-4 h-4" />
      {{ creating ? 'Starting\u2026' : 'Create backup' }}
    </button>
  </Card>

  <Card>
    <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>
    <div v-else-if="backups.length === 0" class="text-sm text-ink-muted">No backups yet.</div>

    <table v-else class="w-full text-sm">
      <thead>
        <tr class="text-left text-xs text-ink-dim uppercase tracking-wide border-b border-white/5">
          <th class="pb-3 font-medium">File</th>
          <th class="pb-3 font-medium">Size</th>
          <th class="pb-3 font-medium">Created</th>
          <th class="pb-3 font-medium text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="b in backups" :key="b.filename" class="border-b border-white/5 last:border-0">
          <td class="py-3 font-mono text-xs text-ink">{{ b.filename }}</td>
          <td class="py-3 text-ink-muted">{{ b.size_mb }} MB</td>
          <td class="py-3 text-ink-muted">{{ b.created_at }}</td>
          <td class="py-3">
            <div class="flex justify-end gap-1.5">
              <button
                :disabled="busyFilename === b.filename"
                @click="downloadBackup(b.filename)"
                title="Download"
                class="p-2 rounded-md text-ink-muted hover:text-lapis hover:bg-lapis/10 disabled:opacity-40 transition-colors"
              >
                <Icon name="download" size="w-4 h-4" />
              </button>
              <button
                :disabled="busyFilename === b.filename"
                @click="restoreBackup(b.filename)"
                title="Restore"
                class="p-2 rounded-md text-ink-muted hover:text-glowstone hover:bg-glowstone/10 disabled:opacity-40 transition-colors"
              >
                <Icon name="restart" size="w-4 h-4" />
              </button>
              <button
                :disabled="busyFilename === b.filename"
                @click="deleteBackup(b.filename)"
                title="Delete"
                class="p-2 rounded-md text-ink-muted hover:text-redstone hover:bg-redstone/10 disabled:opacity-40 transition-colors"
              >
                <Icon name="trash" size="w-4 h-4" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </Card>
</template>
