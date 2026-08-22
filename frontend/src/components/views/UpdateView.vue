<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api'
import { serversStore } from '../../stores/servers'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const props = defineProps({ id: { type: String, required: true } })

const mode = ref('list') // 'list' | 'url'
const versions = ref([])
const loadingVersions = ref(true)
const selectedVersion = ref('')
const customVersion = ref('')
const downloadUrl = ref('')
const expectedSha256 = ref('')
const updating = ref(false)

const currentVersion = computed(() => serversStore.byId(props.id)?.installed_version)
const canSubmit = computed(() => {
  if (mode.value === 'url') return !!downloadUrl.value
  return !!(selectedVersion.value || customVersion.value)
})

async function loadVersions() {
  loadingVersions.value = true
  try {
    const { data } = await api.get('/minecraft-versions')
    versions.value = data.versions
    if (!selectedVersion.value && versions.value.length > 0) {
      selectedVersion.value = versions.value[0].version
    }
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load the version list'))
  } finally {
    loadingVersions.value = false
  }
}

async function startUpdate() {
  if (!canSubmit.value) return
  if (
    !window.confirm(
      'This stops the server, replaces the server binary, and starts it back up. Your world and config files are preserved. Continue?',
    )
  )
    return
  updating.value = true
  try {
    const payload =
      mode.value === 'url'
        ? { download_url: downloadUrl.value, expected_sha256: expectedSha256.value || undefined }
        : { version: customVersion.value || selectedVersion.value, expected_sha256: expectedSha256.value || undefined }
    await api.post(`/servers/${props.id}/update`, payload)
    toastStore.success('Update started in the background \u2014 check the Dashboard log for progress')
    downloadUrl.value = ''
    customVersion.value = ''
    expectedSha256.value = ''
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not start update'))
  } finally {
    updating.value = false
  }
}

onMounted(loadVersions)
</script>

<template>
  <Card title="Update Server" subtitle="Installs a bedrock_server build and swaps it in">
    <p v-if="currentVersion" class="text-sm text-ink-muted mb-4">
      Currently installed: <span class="font-mono text-ink">{{ currentVersion }}</span>
    </p>

    <div class="flex gap-2 mb-5">
      <button
        @click="mode = 'list'"
        :class="[
          'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
          mode === 'list' ? 'bg-emerald/10 text-emerald border-emerald/30' : 'text-ink-muted border-white/10 hover:text-ink',
        ]"
      >
        Pick a version
      </button>
      <button
        @click="mode = 'url'"
        :class="[
          'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
          mode === 'url' ? 'bg-emerald/10 text-emerald border-emerald/30' : 'text-ink-muted border-white/10 hover:text-ink',
        ]"
      >
        By direct URL
      </button>
    </div>

    <div v-if="mode === 'list'">
      <label class="block text-xs font-medium text-ink-muted mb-1.5">Version</label>
      <div v-if="loadingVersions" class="text-sm text-ink-muted">Loading versions\u2026</div>
      <select
        v-else
        v-model="selectedVersion"
        class="w-72 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono focus:border-lapis/60 outline-none transition-colors"
      >
        <option v-for="v in versions" :key="v.version" :value="v.version">{{ v.label }}</option>
      </select>

      <label class="block text-xs font-medium text-ink-muted mb-1.5 mt-4">Or type a version not in the list</label>
      <input
        v-model="customVersion"
        type="text"
        placeholder="1.21.90.4"
        class="w-72 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
      />
    </div>

    <div v-else>
      <label class="block text-xs font-medium text-ink-muted mb-1.5">Download URL</label>
      <input
        v-model="downloadUrl"
        type="url"
        placeholder="https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-x.x.x.x.zip"
        class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
      />
    </div>

    <label class="block text-xs font-medium text-ink-muted mb-1.5 mt-4">SHA256 checksum (optional)</label>
    <input
      v-model="expectedSha256"
      type="text"
      placeholder="Verifies the download before installing it, if you have one"
      class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
    />

    <button
      @click="startUpdate"
      :disabled="updating || !canSubmit"
      class="flex items-center gap-2 mt-5 px-4 py-2.5 rounded-lg bg-glowstone text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all"
    >
      <Icon name="update" size="w-4 h-4" />
      {{ updating ? 'Starting\u2026' : 'Update & restart' }}
    </button>

    <p class="text-xs text-ink-dim mt-3">
      The version list combines Mojang's official current release/preview with the community-maintained
      Bedrock-OSS/BDS-Versions history. Only links from Mojang's own domains are ever downloaded. World saves,
      server.properties, allowlist, and permissions are never touched by an update.
    </p>
  </Card>
</template>
