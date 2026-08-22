import { reactive } from 'vue'
import api from '../api'

export const serversStore = reactive({
  servers: [],
  loading: false,
  loaded: false,

  async refresh() {
    this.loading = true
    try {
      const { data } = await api.get('/servers')
      this.servers = data.servers
    } finally {
      this.loading = false
      this.loaded = true
    }
  },

  byId(id) {
    return this.servers.find((s) => s.id === id) || null
  },
})
