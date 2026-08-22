<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '../../api'
import { propertyGroups } from '../../data/propertyFields'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'
import Icon from '../Icon.vue'

const props = defineProps({ id: { type: String, required: true } })
const form = reactive({})
const loading = ref(true)
const saving = ref(false)
const serverId = computed(() => props.id)

async function load() {
  if (!serverId.value) return
  loading.value = true
  try {
    const { data } = await api.get(`/servers/${serverId.value}/properties`)
    Object.assign(form, data)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load server.properties'))
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!serverId.value) return
  saving.value = true
  try {
    const { data } = await api.post(`/servers/${serverId.value}/properties`, form)
    Object.assign(form, data)
    toastStore.success('Properties saved. Restart the server to apply changes.')
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not save properties'))
  } finally {
    saving.value = false
  }
}

watch(serverId, load)
onMounted(load)
</script>

<template>
  <Card v-if="!serverId">
    <p class="text-sm text-ink-muted">Select or create a server first.</p>
  </Card>

  <div v-else-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>

  <form v-else @submit.prevent="save">
    <Card v-for="group in propertyGroups" :key="group.title" :title="group.title">
      <div class="grid sm:grid-cols-2 gap-x-6 gap-y-5">
        <div v-for="field in group.fields" :key="field.key">
          <label class="flex items-center justify-between gap-3 mb-1.5">
            <span class="text-sm text-ink-muted">{{ field.label }}</span>
            <label v-if="field.type === 'boolean'" class="relative inline-flex items-center cursor-pointer shrink-0">
              <input type="checkbox" v-model="form[field.key]" class="sr-only peer" />
              <div class="w-9 h-5 bg-white/10 rounded-full peer-checked:bg-emerald transition-colors duration-200"></div>
              <div
                class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-200 peer-checked:translate-x-4"
              ></div>
            </label>
          </label>

          <select
            v-if="field.type === 'select'"
            v-model="form[field.key]"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
          >
            <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>

          <input
            v-else-if="field.type === 'number'"
            type="number"
            v-model.number="form[field.key]"
            :min="field.min"
            :max="field.max"
            :step="field.step || 1"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-ink font-mono focus:border-lapis/60 outline-none transition-colors"
          />

          <input
            v-else-if="field.type === 'text'"
            type="text"
            v-model="form[field.key]"
            class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-ink focus:border-lapis/60 outline-none transition-colors"
          />

          <p v-if="field.help" class="text-xs text-ink-dim mt-1.5">{{ field.help }}</p>
        </div>
      </div>
    </Card>

    <div class="flex justify-end sticky bottom-4">
      <button
        type="submit"
        :disabled="saving"
        class="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald text-void text-sm font-medium hover:brightness-110 disabled:opacity-40 shadow-glass transition-all"
      >
        <Icon name="save" size="w-4 h-4" />
        {{ saving ? 'Saving\u2026' : 'Save changes' }}
      </button>
    </div>
  </form>
</template>
