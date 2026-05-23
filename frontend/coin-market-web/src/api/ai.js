import axios from 'axios'

const aiClient = axios.create({
  baseURL: '/api/ai',
  timeout: 120000
})

export function getAiHealth() {
  return aiClient.get('/health')
}

export function sendAiChat(payload) {
  return aiClient.post('/chat', payload)
}
