<script setup>
import { ref } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const downloadUrl = ref('')
const updating = ref(false)

async function startUpdate() {
  if (!downloadUrl.value) return
  if (
    !window.confirm(
      'This stops the server, replaces the server binary, and starts it back up. Your world and config files are preserved. Continue?',
    )
  )
    return
  updating.value = true
  try {
    await api.post('/server/update', { download_url: downloadUrl.value })
    toastStore.success('Update started in the background \u2014 check the Dashboard log for progress')
    downloadUrl.value = ''
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not start update'))
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <Card title="Update Server" subtitle="Downloads a new bedrock_server build and swaps it in">
    <ol class="text-sm text-ink-muted list-decimal list-inside space-y-1 mb-5">
      <li>
        Go to
        <a href="https://www.minecraft.net/en-us/download/server/bedrock" target="_blank" rel="noopener" class="text-lapis hover:underline"
          >minecraft.net/download/server/bedrock</a
        >
        and copy the Linux server download link.
      </li>
      <li>Paste it below and start the update.</li>
    </ol>

    <label class="block text-xs font-medium text-ink-muted mb-1.5">Download URL</label>
    <div class="flex gap-3">
      <input
        v-model="downloadUrl"
        type="url"
        placeholder="https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-x.x.x.x.zip"
        class="flex-1 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink font-mono placeholder:text-ink-dim focus:border-lapis/60 outline-none transition-colors"
      />
      <button
        @click="startUpdate"
        :disabled="updating || !downloadUrl"
        class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-glowstone text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all shrink-0"
      >
        <Icon name="update" size="w-4 h-4" />
        {{ updating ? 'Starting\u2026' : 'Update & restart' }}
      </button>
    </div>
    <p class="text-xs text-ink-dim mt-3">
      Only links from Mojang's own download domains are accepted. World saves, server.properties, allowlist, and permissions are
      never touched by an update.
    </p>
  </Card>
</template>
