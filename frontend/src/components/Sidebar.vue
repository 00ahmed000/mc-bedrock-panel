<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { authStore } from '../stores/auth'
import { serversStore } from '../stores/servers'
import Icon from './Icon.vue'

const route = useRoute()
const currentServerId = computed(() => (typeof route.params.id === 'string' ? route.params.id : ''))

const serverSubTabs = [
  { name: 'server-dashboard', label: 'Dashboard', icon: 'dashboard' },
  { name: 'server-properties', label: 'Properties', icon: 'properties' },
  { name: 'server-gamerules', label: 'Gamerules', icon: 'gamerules' },
  { name: 'server-backups', label: 'Backups', icon: 'backups' },
  { name: 'server-update', label: 'Update', icon: 'update' },
  { name: 'server-allowlist', label: 'Allowlist', icon: 'allowlist' },
  { name: 'server-permissions', label: 'Permissions', icon: 'permissions' },
  { name: 'server-settings', label: 'Container', icon: 'settings' },
]

const globalTabs = [
  { name: 'tasks', label: 'Tasks', icon: 'tasks' },
  { name: 'sftp', label: 'SFTP', icon: 'sftp' },
]

function statusDotClass(status) {
  if (status === 'running') return 'bg-emerald'
  if (status === 'restarting' || status === 'paused' || status === 'created') return 'bg-glowstone'
  if (status === 'exited') return 'bg-redstone'
  return 'bg-ink-dim'
}

onMounted(() => {
  if (!serversStore.loaded) serversStore.refresh()
})
</script>

<template>
  <aside class="w-64 shrink-0 h-screen sticky top-0 glass-panel border-r border-white/5 flex flex-col">
    <div class="flex items-center gap-2.5 px-5 h-16 border-b border-white/5 shrink-0">
      <div class="w-8 h-8 rounded-lg bg-emerald/15 border border-emerald/30 flex items-center justify-center">
        <div class="w-2.5 h-2.5 rounded-sm bg-emerald"></div>
      </div>
      <span class="font-display font-semibold text-ink tracking-tight">Bedrock Panel</span>
    </div>

    <nav class="flex-1 px-3 py-3 flex flex-col gap-1 overflow-y-auto">
      <div class="flex items-center justify-between px-2 mb-1">
        <p class="text-[11px] uppercase tracking-wide text-ink-dim">Servers</p>
        <router-link
          to="/servers"
          title="Manage servers"
          class="p-1 rounded text-ink-dim hover:text-ink hover:bg-white/5 transition-colors"
        >
          <Icon name="plus" size="w-3.5 h-3.5" />
        </router-link>
      </div>

      <div v-for="s in serversStore.servers" :key="s.id">
        <router-link
          :to="`/servers/${s.id}/dashboard`"
          :class="[
            'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            currentServerId === s.id ? 'bg-emerald/10 text-emerald' : 'text-ink-muted hover:text-ink hover:bg-white/5',
          ]"
        >
          <span :class="['w-1.5 h-1.5 rounded-full shrink-0', statusDotClass(s.status)]"></span>
          <span class="truncate">{{ s.name }}</span>
        </router-link>

        <div v-if="currentServerId === s.id" class="ml-3 mt-1 mb-2 pl-3 border-l border-white/10 flex flex-col gap-0.5">
          <router-link
            v-for="tab in serverSubTabs"
            :key="tab.name"
            :to="{ name: tab.name, params: { id: s.id } }"
            :class="[
              'flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors',
              route.name === tab.name ? 'text-emerald bg-emerald/5' : 'text-ink-dim hover:text-ink hover:bg-white/5',
            ]"
          >
            <Icon :name="tab.icon" size="w-3.5 h-3.5" />
            {{ tab.label }}
          </router-link>
        </div>
      </div>

      <p v-if="serversStore.loaded && serversStore.servers.length === 0" class="px-2 text-xs text-ink-dim">
        No servers yet. <router-link to="/servers" class="text-lapis hover:underline">Create one</router-link>
      </p>

      <div class="h-px bg-white/5 my-2 mx-1"></div>
      <p class="px-2 text-[11px] uppercase tracking-wide text-ink-dim mb-1">Panel-wide</p>

      <router-link
        v-for="tab in globalTabs"
        :key="tab.name"
        :to="{ name: tab.name }"
        :class="[
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
          route.name === tab.name ? 'bg-emerald/10 text-emerald' : 'text-ink-muted hover:text-ink hover:bg-white/5',
        ]"
      >
        <Icon :name="tab.icon" size="w-4 h-4" />
        {{ tab.label }}
      </router-link>
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
