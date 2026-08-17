<script setup>
import { toastStore } from '../stores/toast'

const styles = {
  success: 'border-emerald/30 text-emerald',
  error: 'border-redstone/30 text-redstone',
  info: 'border-lapis/30 text-lapis',
}
</script>

<template>
  <div class="fixed bottom-5 right-5 z-50 flex flex-col gap-2 w-80 max-w-[calc(100vw-2.5rem)]">
    <TransitionGroup name="fade">
      <div
        v-for="toast in toastStore.items"
        :key="toast.id"
        :class="['glass-panel-strong rounded-xl px-4 py-3 shadow-glass border-l-2 flex items-start justify-between gap-3', styles[toast.type] || styles.info]"
      >
        <p class="text-sm text-ink leading-snug">{{ toast.message }}</p>
        <button
          class="text-ink-dim hover:text-ink shrink-0 text-lg leading-none"
          @click="toastStore.dismiss(toast.id)"
          aria-label="Dismiss"
        >
          &times;
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
