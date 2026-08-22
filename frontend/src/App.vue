<script setup>
import LoginView from './components/LoginView.vue'
import PanelLayout from './components/PanelLayout.vue'
import { authStore } from './stores/auth'
</script>

<template>
  <LoginView v-if="!authStore.isAuthenticated" />
  <PanelLayout v-else />
</template>
