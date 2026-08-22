<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: String, default: 'w-5 h-5' },
})
</script>

<template>
  <svg
    :class="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <template v-if="name === 'dashboard'">
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </template>

    <template v-else-if="name === 'properties'">
      <circle cx="12" cy="12" r="3" />
      <circle cx="12" cy="12" r="8" stroke-dasharray="2 3" />
    </template>

    <template v-else-if="name === 'backups'">
      <rect x="3" y="7" width="18" height="13" rx="1.5" />
      <path d="M3 7 L5 3 L19 3 L21 7" />
      <line x1="9" y1="12" x2="15" y2="12" />
    </template>

    <template v-else-if="name === 'update' || name === 'restart'">
      <path d="M20 11 A8 8 0 1 0 4 13" />
      <path d="M20 11 L20 5" />
      <path d="M20 11 L14 11" />
    </template>

    <template v-else-if="name === 'sftp'">
      <rect x="4" y="8" width="16" height="12" rx="1.5" />
      <path d="M8 8 V6 A4 4 0 0 1 16 6 V8" />
    </template>

    <template v-else-if="name === 'allowlist'">
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3 20 V19 A6 6 0 0 1 9 13 A6 6 0 0 1 15 19 V20" />
      <line x1="17" y1="8" x2="21" y2="8" />
      <line x1="19" y1="6" x2="19" y2="10" />
    </template>

    <template v-else-if="name === 'permissions'">
      <path d="M12 3 L19 6 V11 C19 15.5 16 19 12 21 C8 19 5 15.5 5 11 V6 Z" />
    </template>

    <template v-else-if="name === 'logout'">
      <path d="M9 21 H6 A2 2 0 0 1 4 19 V5 A2 2 0 0 1 6 3 H9" />
      <path d="M16 17 L20 12 L16 7" />
      <line x1="20" y1="12" x2="9" y2="12" />
    </template>

    <template v-else-if="name === 'play'">
      <polygon points="6 4 20 12 6 20 6 4" />
    </template>

    <template v-else-if="name === 'stop'">
      <rect x="6" y="6" width="12" height="12" rx="1.5" />
    </template>

    <template v-else-if="name === 'plus'">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </template>

    <template v-else-if="name === 'trash'">
      <path d="M3 6 H21" />
      <path d="M8 6 V4 A2 2 0 0 1 10 2 H14 A2 2 0 0 1 16 4 V6" />
      <path d="M19 6 L18 20 A2 2 0 0 1 16 22 H8 A2 2 0 0 1 6 20 L5 6" />
    </template>

    <template v-else-if="name === 'download'">
      <path d="M12 3 V15" />
      <path d="M7 10 L12 15 L17 10" />
      <path d="M4 21 H20" />
    </template>

    <template v-else-if="name === 'save'">
      <path d="M5 3 H16 L19 6 V19 A2 2 0 0 1 17 21 H5 A2 2 0 0 1 3 19 V5 A2 2 0 0 1 5 3 Z" />
      <rect x="7" y="3" width="8" height="5" />
      <rect x="7" y="13" width="10" height="8" />
    </template>

    <template v-else-if="name === 'chevron'">
      <polyline points="9 6 15 12 9 18" />
    </template>

    <template v-else-if="name === 'terminal'">
      <rect x="3" y="4" width="18" height="16" rx="1.5" />
      <polyline points="7 9 11 12 7 15" />
      <line x1="13" y1="15" x2="17" y2="15" />
    </template>

    <template v-else-if="name === 'gamerules'">
      <rect x="4" y="4" width="16" height="16" rx="3" />
      <circle cx="8.5" cy="8.5" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="8.5" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="8.5" cy="15.5" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="15.5" r="1.1" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'servers'">
      <rect x="3" y="4" width="18" height="5" rx="1.5" />
      <rect x="3" y="14" width="18" height="5" rx="1.5" />
      <circle cx="7" cy="6.5" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="7" cy="16.5" r="0.9" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'tasks'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7 V12 L16 14" />
    </template>

    <template v-else-if="name === 'settings'">
      <line x1="4" y1="7" x2="20" y2="7" />
      <circle cx="14" cy="7" r="2" fill="currentColor" stroke="none" />
      <line x1="4" y1="12" x2="20" y2="12" />
      <circle cx="8" cy="12" r="2" fill="currentColor" stroke="none" />
      <line x1="4" y1="17" x2="20" y2="17" />
      <circle cx="16" cy="17" r="2" fill="currentColor" stroke="none" />
    </template>
  </svg>
</template>
