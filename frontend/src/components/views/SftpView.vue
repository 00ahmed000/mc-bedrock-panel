<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const info = ref({ running: false, port: 2222, username: '' })
const loading = ref(true)
const password = ref('')
const confirmPassword = ref('')
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/sftp/info')
    info.value = data
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load SFTP info'))
  } finally {
    loading.value = false
  }
}

const passwordsMatch = computed(() => password.value && password.value === confirmPassword.value)
const passwordTooShort = computed(() => password.value.length > 0 && password.value.length < 8)

async function savePassword() {
  if (!passwordsMatch.value) return
  saving.value = true
  try {
    const { data } = await api.post('/sftp/configure', { password: password.value })
    toastStore.success(data.message)
    password.value = ''
    confirmPassword.value = ''
    setTimeout(load, 1500)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not update SFTP password'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <Card title="Connection info" subtitle="Use any SFTP client \u2014 FileZilla, Cyberduck, WinSCP">
    <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>
    <dl v-else class="grid sm:grid-cols-3 gap-4 text-sm">
      <div class="rounded-lg bg-white/5 border border-white/10 p-4">
        <dt class="text-xs text-ink-dim uppercase tracking-wide mb-1">Host</dt>
        <dd class="font-mono text-ink">your-server-ip</dd>
      </div>
      <div class="rounded-lg bg-white/5 border border-white/10 p-4">
        <dt class="text-xs text-ink-dim uppercase tracking-wide mb-1">Port</dt>
        <dd class="font-mono text-ink">{{ info.port }}</dd>
      </div>
      <div class="rounded-lg bg-white/5 border border-white/10 p-4">
        <dt class="text-xs text-ink-dim uppercase tracking-wide mb-1">Username</dt>
        <dd class="font-mono text-ink">{{ info.username }}</dd>
      </div>
    </dl>
    <p class="text-xs text-ink-dim mt-4">
      After connecting, look inside the <span class="font-mono">server/</span> folder for your world files.
    </p>
  </Card>

  <Card title="Change password" subtitle="The username above is fixed at setup and can't be changed here">
    <form @submit.prevent="savePassword" class="max-w-sm">
      <label class="block text-xs font-medium text-ink-muted mb-1.5">New password</label>
      <input
        v-model="password"
        type="password"
        autocomplete="new-password"
        class="w-full mb-3 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
      />
      <label class="block text-xs font-medium text-ink-muted mb-1.5">Confirm password</label>
      <input
        v-model="confirmPassword"
        type="password"
        autocomplete="new-password"
        class="w-full mb-1.5 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
      />
      <p v-if="passwordTooShort" class="text-xs text-redstone mb-2">At least 8 characters.</p>
      <p v-else-if="confirmPassword && !passwordsMatch" class="text-xs text-redstone mb-2">Passwords don't match.</p>

      <button
        type="submit"
        :disabled="saving || !passwordsMatch || passwordTooShort"
        class="mt-3 flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 transition-all"
      >
        <Icon name="save" size="w-4 h-4" />
        {{ saving ? 'Updating\u2026' : 'Update password' }}
      </button>
      <p class="text-xs text-ink-dim mt-3">
        This briefly restarts the SFTP container (a few seconds) to apply the change \u2014 it doesn't touch the Minecraft server.
      </p>
    </form>
  </Card>
</template>
