<script setup>
import { ref } from 'vue'
import api from '../api'
import { authStore } from '../stores/auth'
import { extractErrorMessage } from '../stores/toast'

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (!username.value || !password.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await api.post('/auth/login', {
      username: username.value,
      password: password.value,
    })
    authStore.setSession(data.access_token, data.expires_in, username.value)
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div class="flex items-center justify-center gap-2 mb-8">
        <div class="w-9 h-9 rounded-lg bg-emerald/15 border border-emerald/30 flex items-center justify-center">
          <div class="w-3 h-3 rounded-sm bg-emerald pulse-dot text-emerald"></div>
        </div>
        <span class="font-display font-semibold text-lg tracking-tight text-ink">Bedrock Panel</span>
      </div>

      <form class="glass-panel-strong rounded-2xl p-7 shadow-glass" @submit.prevent="handleSubmit">
        <h1 class="font-display text-xl font-semibold text-ink mb-1">Sign in</h1>
        <p class="text-sm text-ink-muted mb-6">Manage your Bedrock server.</p>

        <label class="block text-xs font-medium text-ink-muted mb-1.5" for="username">Username</label>
        <input
          id="username"
          v-model="username"
          type="text"
          autocomplete="username"
          class="w-full mb-4 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink placeholder:text-ink-dim focus:border-lapis/60 focus:bg-white/[0.07] outline-none transition-colors"
          placeholder="admin"
        />

        <label class="block text-xs font-medium text-ink-muted mb-1.5" for="password">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          class="w-full mb-2 rounded-lg bg-white/5 border border-white/10 px-3 py-2.5 text-sm text-ink placeholder:text-ink-dim focus:border-lapis/60 focus:bg-white/[0.07] outline-none transition-colors"
          placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
        />

        <p v-if="errorMessage" class="text-xs text-redstone mt-2 mb-1">{{ errorMessage }}</p>

        <button
          type="submit"
          :disabled="loading || !username || !password"
          class="w-full mt-5 rounded-lg bg-emerald text-void font-medium text-sm py-2.5 flex items-center justify-center gap-2 hover:brightness-110 active:brightness-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          <span v-if="!loading">Sign in</span>
          <span v-else>Signing in\u2026</span>
        </button>
      </form>

      <p class="text-center text-xs text-ink-dim mt-6">Credentials are set in your .env file</p>
    </div>
  </div>
</template>
