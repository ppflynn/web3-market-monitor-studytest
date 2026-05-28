<template>
  <div class="ai-page">
    <section class="ai-title">
      <div>
        <h1>AI 助手</h1>
        <p>调用当前项目的 FastAPI AI 服务，结合行情接口、市场工具和项目 RAG 上下文回答问题。</p>
      </div>
      <button type="button" class="refresh-button" :disabled="healthLoading" @click="fetchHealth">
        {{ healthLoading ? '检查中' : '刷新状态' }}
      </button>
    </section>

    <section class="status-grid">
      <div><span>AI 服务</span><strong :class="healthOk ? 'ok' : 'warn'">{{ healthOk ? '运行中' : '未连接' }}</strong></div>
      <div><span>模型配置</span><strong :class="llmConfigured ? 'ok' : 'warn'">{{ llmConfigured ? '已配置' : '待配置' }}</strong></div>
      <div><span>当前环境</span><strong>{{ health?.environment || '--' }}</strong></div>
    </section>

    <el-alert
      v-if="errorMsg"
      :title="errorMsg"
      type="error"
      show-icon
      closable
      class="error-alert"
      @close="errorMsg = ''"
    />

    <section class="chat-layout">
      <main class="chat-card">
        <div class="chat-head">
          <div>
            <h2>Market Chat</h2>
            <p>使用 `/api/ai/chat`，保留最近 8 条上下文</p>
          </div>
          <span>{{ chatLoading ? 'Thinking' : 'Ready' }}</span>
        </div>

        <div class="messages" ref="messagesRef">
          <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
            <span class="message-role">{{ message.role === 'user' ? '你' : 'AI' }}</span>
            <p>{{ message.content }}</p>
            <div v-if="message.sources?.length" class="message-meta">
              <code v-for="source in message.sources" :key="`${source.path}-${source.score}`">{{ source.path }}</code>
            </div>
            <div v-if="message.tools?.length" class="message-meta">
              <code v-for="tool in message.tools" :key="`${tool.name}-${JSON.stringify(tool.arguments)}`">{{ tool.name }}</code>
            </div>
          </div>
        </div>

        <div class="composer">
          <el-input
            v-model="input"
            type="textarea"
            :rows="4"
            resize="none"
            maxlength="4000"
            show-word-limit
            placeholder="输入你想问 AI 的问题，例如：BTC 最近走势怎么看？"
            @keydown.ctrl.enter.prevent="submit"
          />
          <div class="composer-actions">
            <button type="button" @click="fillExample('请介绍这个项目的 AI 服务，以及它能读取哪些行情数据。')">项目介绍</button>
            <button type="button" @click="fillExample('BTC 最近 7 天走势怎么看？请基于项目数据库数据回答，并只做信息分析。')">行情提问</button>
            <button type="button" class="primary" :disabled="!canSubmit" @click="submit">{{ chatLoading ? '发送中' : '发送' }}</button>
          </div>
        </div>
      </main>

      <aside class="side-stack">
        <section class="side-card">
          <h3>已接入能力</h3>
          <ul>
            <li>FastAPI 独立 AI 服务</li>
            <li>Spring Boot / MySQL 行情读取</li>
            <li>OpenAI 兼容模型接口</li>
            <li>项目 RAG 文档检索</li>
            <li>市场工具自动调用</li>
          </ul>
          <a href="/api/ai/health" target="_blank" rel="noreferrer">查看健康检查</a>
        </section>

        <section class="side-card" v-if="latestSources.length">
          <h3>Latest Sources</h3>
          <div class="source-list">
            <code v-for="source in latestSources" :key="`${source.path}-${source.score}`">{{ source.path }}</code>
          </div>
        </section>

        <section class="side-card" v-if="latestTools.length">
          <h3>Latest Tools</h3>
          <div class="source-list">
            <code v-for="tool in latestTools" :key="`${tool.name}-${JSON.stringify(tool.arguments)}`">{{ tool.name }}</code>
          </div>
        </section>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getAiHealth, sendAiChat } from '../api/ai.js'

const route = useRoute()
const health = ref(null)
const healthLoading = ref(false)
const chatLoading = ref(false)
const errorMsg = ref('')
const input = ref('')
const messagesRef = ref(null)
const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: '你好，我是 CoinMarketCap Web3 的 AI 助手。你可以问我项目功能、FastAPI 服务，也可以让我基于项目数据库里的行情数据做信息分析。'
  }
])

const healthOk = computed(() => health.value?.status === 'ok')
const llmConfigured = computed(() => Boolean(health.value?.llm_configured))
const canSubmit = computed(() => input.value.trim().length > 0 && !chatLoading.value)
const latestAssistantMessage = computed(() => [...messages.value].reverse().find(message => message.role === 'assistant'))
const latestSources = computed(() => latestAssistantMessage.value?.sources ?? [])
const latestTools = computed(() => latestAssistantMessage.value?.tools ?? [])

async function fetchHealth() {
  try {
    healthLoading.value = true
    errorMsg.value = ''
    const res = await getAiHealth()
    health.value = res.data
  } catch (err) {
    health.value = null
    errorMsg.value = err.response?.data?.message || 'AI 服务暂时无法连接，请确认 Docker 中的 ai 服务已经启动。'
  } finally {
    healthLoading.value = false
  }
}
function fillExample(text) { input.value = text }
async function submit() {
  const content = input.value.trim()
  if (!content || chatLoading.value) return
  const history = messages.value
    .filter(message => message.role === 'user' || message.role === 'assistant')
    .slice(-8)
    .map(message => ({ role: message.role, content: message.content }))
  messages.value.push({ id: Date.now(), role: 'user', content })
  input.value = ''
  await scrollToBottom()
  try {
    chatLoading.value = true
    errorMsg.value = ''
    const res = await sendAiChat({ message: content, history, temperature: 0.3, max_tokens: 800 })
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: res.data?.answer || 'AI 没有返回内容。',
      sources: res.data?.sources || [],
      tools: res.data?.tools || []
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    errorMsg.value = detail || 'AI 调用失败，请检查模型配置或稍后重试。'
    messages.value.push({ id: Date.now() + 2, role: 'assistant', content: errorMsg.value })
  } finally {
    chatLoading.value = false
    await scrollToBottom()
  }
}
async function scrollToBottom() {
  await nextTick()
  const el = messagesRef.value
  if (el) el.scrollTop = el.scrollHeight
}
onMounted(() => {
  fetchHealth()
  if (typeof route.query.q === 'string') input.value = route.query.q
})
</script>

<style scoped>
.ai-page {
  width: min(1280px, 100%);
  min-height: calc(100vh - 64px);
  margin: 0 auto;
  padding: 28px 24px 56px;
}

.ai-title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.ai-title h1 {
  margin: 0;
  color: #111;
  font-size: 32px;
  font-weight: 800;
}

.ai-title p {
  margin: 8px 0 0;
  color: #707a8a;
  font-size: 14px;
}

button {
  font-family: inherit;
}

.refresh-button,
.composer-actions button {
  height: 34px;
  border: 1px solid #ebedf0;
  border-radius: 17px;
  padding: 0 14px;
  color: #111;
  background: #fff;
  cursor: pointer;
  font-weight: 700;
}

.refresh-button {
  color: #fff;
  border-color: #111;
  background: #111;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.status-grid div,
.chat-card,
.side-card {
  border: 1px solid #ebedf0;
  border-radius: 16px;
  background: #fff;
}

.status-grid div {
  padding: 16px;
}

.status-grid span {
  display: block;
  color: #707a8a;
  font-size: 12px;
  font-weight: 700;
}

.status-grid strong {
  display: block;
  margin-top: 6px;
  color: #111;
  font-size: 18px;
  font-weight: 800;
}

.status-grid .ok {
  color: #16a34a;
}

.status-grid .warn {
  color: #f59e0b;
}

.chat-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  align-items: start;
}

.chat-card {
  overflow: hidden;
}

.chat-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid #ebedf0;
}

.chat-head h2,
.side-card h3 {
  margin: 0;
  color: #111;
  font-size: 18px;
  font-weight: 800;
}

.chat-head p {
  margin: 4px 0 0;
  color: #707a8a;
  font-size: 13px;
}

.chat-head > span {
  color: #16a34a;
  font-size: 13px;
  font-weight: 800;
}

.messages {
  min-height: 400px;
  max-height: 520px;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
}

.message {
  max-width: 78%;
  margin-bottom: 14px;
}

.message.user {
  margin-left: auto;
}

.message-role {
  display: block;
  margin-bottom: 5px;
  color: #707a8a;
  font-size: 12px;
  font-weight: 700;
}

.message.user .message-role {
  text-align: right;
}

.message p {
  margin: 0;
  padding: 12px 14px;
  border: 1px solid #ebedf0;
  border-radius: 14px;
  color: #111;
  background: #fff;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.message.user p {
  color: #fff;
  border-color: #111;
  background: #111;
}

.message-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.message-meta code,
.source-list code {
  padding: 5px 8px;
  border: 1px solid #ebedf0;
  border-radius: 8px;
  color: #3f4656;
  background: #fff;
  font-size: 11px;
}

.composer {
  padding: 16px 20px;
  border-top: 1px solid #ebedf0;
}

.composer :deep(.el-textarea__inner) {
  border-color: #ebedf0;
  border-radius: 12px;
  color: #111;
  background: #fff;
  box-shadow: none;
}

.composer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.composer-actions .primary {
  color: #fff;
  border-color: #111;
  background: #111;
}

.composer-actions button:disabled {
  opacity: 0.5;
  cursor: default;
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.side-card {
  padding: 18px;
}

.side-card ul {
  display: grid;
  gap: 10px;
  margin: 14px 0;
  padding: 0;
  list-style: none;
}

.side-card li {
  color: #3f4656;
  font-size: 13px;
  font-weight: 700;
}

.side-card a {
  color: #111;
  font-size: 13px;
  font-weight: 800;
  text-decoration: none;
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

@media (max-width: 900px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .ai-page {
    padding: 20px 12px 40px;
  }
  .ai-title,
  .chat-head {
    align-items: stretch;
    flex-direction: column;
  }
  .status-grid {
    grid-template-columns: 1fr;
  }
  .message {
    max-width: 92%;
  }
}
</style>
