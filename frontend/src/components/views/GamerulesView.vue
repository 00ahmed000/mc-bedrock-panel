<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api from '../../api'
import { extractErrorMessage, toastStore } from '../../stores/toast'
import Card from '../Card.vue'

const props = defineProps({ id: { type: String, required: true } })
const rules = ref([])
const loading = ref(true)
const busyRule = ref('')
const draftInts = ref({})

const serverId = computed(() => props.id)

async function load() {
  if (!serverId.value) return
  loading.value = true
  try {
    const { data } = await api.get(`/servers/${serverId.value}/gamerules`)
    rules.value = data.rules
    draftInts.value = Object.fromEntries(
      data.rules.filter((r) => r.type === 'int').map((r) => [r.name, r.current ?? r.default]),
    )
  } catch (err) {
    toastStore.error(extractErrorMessage(err, 'Could not load gamerules'))
  } finally {
    loading.value = false
  }
}

async function applyRule(name, value) {
  busyRule.value = name
  try {
    await api.post(`/servers/${serverId.value}/gamerules`, { name, value })
    const rule = rules.value.find((r) => r.name === name)
    if (rule) rule.current = value
    toastStore.success(`gamerule ${name} ${value}`)
  } catch (err) {
    toastStore.error(extractErrorMessage(err, `Could not set ${name}`))
  } finally {
    busyRule.value = ''
  }
}

watch(serverId, load)
onMounted(load)
</script>

<template>
  <Card v-if="!serverId">
    <p class="text-sm text-ink-muted">Select or create a server first.</p>
  </Card>

  <template v-else>
    <Card
      title="Gamerules"
      subtitle="Sent live to the server console. Bedrock has no gamerules file to read back, so &quot;Current&quot; reflects the last value this panel sent, not necessarily a value changed in-game by someone else."
    >
      <div v-if="loading" class="text-sm text-ink-muted">Loading\u2026</div>

      <div v-else class="grid sm:grid-cols-2 gap-3">
        <div
          v-for="rule in rules"
          :key="rule.name"
          class="flex items-center justify-between gap-3 rounded-lg bg-white/5 border border-white/10 px-4 py-3"
        >
          <div class="min-w-0">
            <p class="text-sm text-ink truncate">{{ rule.label }}</p>
            <p class="text-xs text-ink-dim font-mono">
              {{ rule.name }} \u00b7 {{ rule.current === null ? 'not set (default ' + rule.default + ')' : rule.current }}
            </p>
          </div>

          <label v-if="rule.type === 'boolean'" class="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              :checked="rule.current ?? rule.default"
              :disabled="busyRule === rule.name"
              @change="applyRule(rule.name, $event.target.checked)"
              class="sr-only peer"
            />
            <div class="w-9 h-5 bg-white/10 rounded-full peer-checked:bg-emerald transition-colors duration-200"></div>
            <div
              class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-200 peer-checked:translate-x-4"
            ></div>
          </label>

          <div v-else class="flex items-center gap-1.5 shrink-0">
            <input
              type="number"
              v-model.number="draftInts[rule.name]"
              class="w-20 rounded-md bg-white/5 border border-white/10 px-2 py-1.5 text-xs text-ink font-mono focus:border-lapis/60 outline-none"
            />
            <button
              :disabled="busyRule === rule.name"
              @click="applyRule(rule.name, draftInts[rule.name])"
              class="text-xs px-2.5 py-1.5 rounded-md bg-white/5 border border-white/10 text-ink-muted hover:text-ink hover:bg-white/10 disabled:opacity-40 transition-colors"
            >
              Set
            </button>
          </div>
        </div>
      </div>
    </Card>
  </template>
</template>
