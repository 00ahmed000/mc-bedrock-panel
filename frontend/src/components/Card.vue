<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <section class="glass-panel rounded-2xl p-6 mb-5">
    <div v-if="title" class="mb-5">
      <h2 class="font-display font-semibold text-ink text-base">{{ title }}</h2>
      <p v-if="subtitle" class="text-sm text-ink-muted mt-0.5">{{ subtitle }}</p>
    </div>
    <slot />
  </section>
</template>
