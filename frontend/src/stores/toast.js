import { reactive } from 'vue'

let nextId = 1

export const toastStore = reactive({
  items: [],

  push(message, type = 'info', duration = 4500) {
    const id = nextId++
    this.items.push({ id, message, type })
    setTimeout(() => this.dismiss(id), duration)
    return id
  },

  success(message) {
    return this.push(message, 'success')
  },

  error(message) {
    return this.push(message, 'error', 7000)
  },

  info(message) {
    return this.push(message, 'info')
  },

  dismiss(id) {
    const idx = this.items.findIndex((t) => t.id === id)
    if (idx !== -1) this.items.splice(idx, 1)
  },
})

/**
 * Pull a readable message out of an axios error. FastAPI's default error
 * shape is {"detail": "..."} for a single error or a list of validation
 * error objects for a 422 — this normalizes both to one string.
 */
export function extractErrorMessage(error, fallback = 'Something went wrong') {
  const detail = error?.response?.data?.detail
  if (!detail) return error?.message || fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  }
  return fallback
}
