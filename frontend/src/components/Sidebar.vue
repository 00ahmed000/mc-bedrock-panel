<script setup>
import { authStore } from '../stores/auth'
import Icon from './Icon.vue'

defineProps({
  activeTab: { type: String, required: true },
})
const emit = defineEmits(['change'])

const tabs = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'properties', label: 'Properties', icon: 'properties' },
  { id: 'backups', label: 'Backups', icon: 'backups' },
  { id: 'update', label: 'Update', icon: 'update' },
  { id: 'sftp', label: 'SFTP', icon: 'sftp' },
  { id: 'allowlist', label: 'Allowlist', icon: 'allowlist' },
  { id: 'permissions', label: 'Permissions', icon: 'permissions' },
]
</script>

<template>
  <aside class="w-60 shrink-0 h-screen sticky top-0 glass-panel border-r border-white/5 flex flex-col">
    <div class="flex items-center gap-2.5 px-5 h-16 border-b border-white/5 shrink-0">
      <div class="w-8 h-8 rounded-lg bg-emerald/15 border border-emerald/30 flex items-center justify-center">
        <div class="w-2.5 h-2.5 rounded-sm bg-emerald"></div>
      </div>
      <span class="font-display font-semibold text-ink tracking-tight">Bedrock Panel</span>
    </div>

    <nav class="flex-1 px-3 py-4 flex flex-col gap-1 overflow-y-auto">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="emit('change', tab.id)"
        :class="[
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left',
          activeTab === tab.id
            ? 'bg-emerald/10 text-emerald border border-emerald/20'
            : 'text-ink-muted hover:text-ink hover:bg-white/5 border border-transparent',
        ]"
      >
        <Icon :name="tab.icon" size="w-4 h-4" />
        {{ tab.label }}
      </button>
    </nav>

    <div class="px-3 py-4 border-t border-white/5 shrink-0">
      <div class="px-3 py-2 mb-1">
        <p class="text-xs text-ink-dim">Signed in as</p>
        <p class="text-sm text-ink font-medium truncate">{{ authStore.username || 'admin' }}</p>
      </div>
      <button
        @click="authStore.logout()"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-ink-muted hover:text-redstone hover:bg-redstone/10 transition-colors"
      >
        <Icon name="logout" size="w-4 h-4" />
        Sign out
      </button>
    </div>
  </aside>
</template>
