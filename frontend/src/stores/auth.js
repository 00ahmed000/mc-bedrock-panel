import { reactive } from 'vue'

const TOKEN_KEY = 'bedrock_panel_token'
const EXPIRY_KEY = 'bedrock_panel_token_expiry'
const USERNAME_KEY = 'bedrock_panel_username'

function loadToken() {
  const token = localStorage.getItem(TOKEN_KEY)
  const expiry = localStorage.getItem(EXPIRY_KEY)
  if (!token || !expiry) return null
  if (Date.now() > Number(expiry)) {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(EXPIRY_KEY)
    localStorage.removeItem(USERNAME_KEY)
    return null
  }
  return token
}

export const authStore = reactive({
  token: loadToken(),
  username: localStorage.getItem(USERNAME_KEY) || '',

  setSession(token, expiresInSeconds, username) {
    this.token = token
    this.username = username
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(EXPIRY_KEY, String(Date.now() + expiresInSeconds * 1000))
    localStorage.setItem(USERNAME_KEY, username)
  },

  logout() {
    this.token = null
    this.username = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(EXPIRY_KEY)
    localStorage.removeItem(USERNAME_KEY)
  },

  get isAuthenticated() {
    return !!this.token
  },
})
