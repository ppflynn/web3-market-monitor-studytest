<template>
  <div class="ai-page">
    <section class="ai-header">
      <div>
        <h1>AI 智能助手</h1>
        <p>连接 FastAPI AI 服务，先读取项目行情数据，再调用大模型生成回答。</p>
      </div>
      <el-button :icon="Refresh" :loading="healthLoading" @click="fetchHealth">刷新状态</el-button>
    </section>

    <section class="status-grid">
      <div class="status-tile">
        <span class="tile-label">AI 服务</span>
        <strong :class="healthOk ? 'ok' : 'warn'">{{ healthOk ? '运行中' : '未连接' }}</strong>
      </div>
      <div class="status-tile">
        <span class="tile-label">模型配置</span>
        <strong :class="llmConfigured ? 'ok' : 'warn'">{{ llmConfigured ? '已配置' : '待配置' }}</strong>
      </div>
      <div class="status-tile">
        <span class="tile-label">当前环境</span>
        <strong>{{ health?.environment || '--' }}</strong>
      </div>
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
      <div class="chat-panel">
        <div class="messages" ref="messagesRef">
          <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
            <span class="message-role">{{ message.role === 'user' ? '你' : 'AI' }}</span>
            <p>{{ message.content }}</p>
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
            <el-button @click="fillExample('请介绍这个项目的 AI 服务')">项目介绍</el-button>
            <el-button @click="fillExample('BTC 最近 7 天走势怎么看？请基于项目数据库数据回答。')">行情提问</el-button>
            <el-button type="primary" :loading="chatLoading" :disabled="!canSubmit" @click="submit">
              发送
            </el-button>
          </div>
        </div>
      </div>

      <aside class="side-panel">
        <h2>已接入能力</h2>
        <ul>
          <li>FastAPI 独立 AI 服务</li>
          <li>Spring Boot / MySQL 行情数据读取</li>
          <li>DeepSeek / OpenAI 兼容接口</li>
          <li>API Key 后端隐藏</li>
          <li>中文接口文档与健康检查</li>
        </ul>
        <a href="/api/ai/health" target="_blank" rel="noreferrer">查看健康检查</a>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
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

function fillExample(text) {
  input.value = text
}

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
    const res = await sendAiChat({
      message: content,
      history,
      temperature: 0.3,
      max_tokens: 800
    })

    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: res.data?.answer || 'AI 没有返回内容。'
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    errorMsg.value = detail || 'AI 调用失败，请检查模型配置或稍后重试。'
    messages.value.push({
      id: Date.now() + 2,
      role: 'assistant',
      content: errorMsg.value
    })
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
  if (typeof route.query.q === 'string') {
    input.value = route.query.q
  }
})
</script>

<style scoped>
.ai-page {
  min-height: calc(100vh - 60px);
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

.ai-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.ai-header h1 {
  margin: 0 0 6px;
  color: #f1f5f9;
  font-size: 24px;
  line-height: 1.3;
}

.ai-header p {
  margin: 0;
  color: #94a3b8;
  font-size: 14px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.status-tile {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 14px 16px;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  background: rgba(255,255,255,0.03);
}

.tile-label {
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.status-tile strong {
  overflow: hidden;
  color: #e2e8f0;
  font-size: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-tile strong.ok {
  color: #34d399;
}

.status-tile strong.warn {
  color: #fbbf24;
}

.error-alert {
  margin-bottom: 16px;
}

.chat-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}

.chat-panel,
.side-panel {
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  background: rgba(255,255,255,0.03);
}

.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 620px;
}

.messages {
  flex: 1;
  min-height: 360px;
  max-height: 520px;
  overflow-y: auto;
  padding: 18px;
}

.message {
  max-width: 78%;
  margin-bottom: 12px;
}

.message.user {
  margin-left: auto;
}

.message-role {
  display: block;
  margin-bottom: 4px;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.message.user .message-role {
  text-align: right;
}

.message p {
  margin: 0;
  padding: 12px 14px;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  color: #e2e8f0;
  background: rgba(15,23,42,0.8);
  line-height: 1.7;
  white-space: pre-wrap;
}

.message.user p {
  color: #eef6ff;
  background: rgba(37,99,235,0.28);
}

.composer {
  padding: 14px;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.composer :deep(.el-textarea__inner) {
  color: #e2e8f0;
  background: rgba(255,255,255,0.04);
  border-color: rgba(255,255,255,0.08);
  box-shadow: none;
}

.composer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.side-panel {
  padding: 16px;
}

.side-panel h2 {
  margin: 0 0 12px;
  color: #f1f5f9;
  font-size: 16px;
}

.side-panel ul {
  margin: 0 0 16px;
  padding-left: 18px;
  color: #cbd5e1;
  line-height: 1.9;
  font-size: 13px;
}

.side-panel a {
  color: #60a5fa;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
}

@media (max-width: 900px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    order: -1;
  }
}

@media (max-width: 640px) {
  .ai-page {
    padding: 16px 12px 36px;
  }

  .ai-header {
    flex-direction: column;
  }

  .status-grid {
    grid-template-columns: 1fr;
  }

  .chat-panel {
    min-height: 560px;
  }

  .messages {
    max-height: 430px;
    padding: 14px;
  }

  .message {
    max-width: 92%;
  }
}
</style>
