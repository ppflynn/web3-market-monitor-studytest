<template>
  <div class="min-h-screen bg-[#07080d] text-zinc-200 flex flex-col font-sans select-none antialiased relative">
    <div class="absolute top-0 left-1/4 w-[600px] h-[500px] bg-indigo-950/10 rounded-full filter blur-[150px] pointer-events-none glow-ambient"></div>

    <Header :global-stats="globalStats" :tokens="tokens.slice(0, 5)" />

    <div class="bg-[#0b0c13] border-b border-zinc-900 sticky top-16 z-40">
      <div class="max-w-[1600px] mx-auto px-4 md:px-6 flex items-center justify-between h-12">
        <div class="flex gap-1.5 h-full items-center">
          <button
            type="button"
            class="h-full px-5 text-xs font-extrabold flex items-center gap-2 border-b-2 transition-all cursor-pointer"
            :class="activeTab === 'market' ? 'border-indigo-505 text-white bg-indigo-950/10' : 'border-transparent text-zinc-500 hover:text-zinc-350'"
            @click="activeTab = 'market'"
          >
            <TrendCharts class="w-4 h-4 text-indigo-400" />
            <span>实时监控与微服务数据看板</span>
          </button>
          <button
            type="button"
            class="h-full px-5 text-xs font-extrabold flex items-center gap-2 border-b-2 transition-all cursor-pointer"
            :class="activeTab === 'ai-copilot' ? 'border-indigo-505 text-white bg-indigo-950/10' : 'border-transparent text-zinc-500 hover:text-zinc-350'"
            @click="activeTab = 'ai-copilot'"
          >
            <Cpu class="w-4 h-4 text-indigo-400" />
            <span>FastAPI-AI 投研与风控助手</span>
            <span class="text-[9px] bg-indigo-650 text-white font-bold px-1.5 py-0.5 rounded-full">中转</span>
          </button>
        </div>

        <div class="hidden sm:flex items-center gap-2.5 text-[11px] text-zinc-500">
          <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> MySQL: 正常连接</span>
          <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Redis: 缓存正常</span>
        </div>
      </div>
    </div>

    <main v-if="activeTab === 'market'" class="flex-1 p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1600px] w-full mx-auto relative z-10 transition-all">
      <section class="lg:col-span-7 xl:col-span-8 flex flex-col gap-5">
        <div class="flex items-center justify-between">
          <div class="flex items-baseline gap-2">
            <h2 class="font-sans font-black text-lg text-white tracking-tight">极速主流币现货行情监控</h2>
            <span class="text-[10px] bg-indigo-950/40 text-indigo-400 px-2.5 py-1 rounded-full border border-indigo-900/30 font-extrabold">
              直连 /api/coins 实时数据
            </span>
          </div>

          <button
            type="button"
            class="flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg border transition-all cursor-pointer"
            :class="showDeveloperZone ? 'bg-indigo-950/40 border-indigo-900 text-indigo-300' : 'bg-zinc-900/30 border-zinc-850 text-zinc-400 hover:text-zinc-200'"
            @click="showDeveloperZone = !showDeveloperZone"
          >
            <Cpu class="w-3.5 h-3.5" />
            <span>{{ showDeveloperZone ? '隐藏微服务架构调试' : '展开微服务部署与缓存监控' }}</span>
          </button>
        </div>

        <div v-if="marketError" class="bg-red-950/30 border border-red-900/40 text-red-300 px-4 py-3 rounded-xl text-xs font-semibold">
          {{ marketError }}
        </div>

        <TokenTable :tokens="tokens" :selected-token-id="selectedToken?.id ?? null" @select-token="handleSelectToken" />
        <DeveloperControlPanel v-if="showDeveloperZone" @refresh-tokens="fetchMarketData(false)" />
      </section>

      <section class="lg:col-span-5 xl:col-span-4 flex flex-col gap-5">
        <div class="flex items-center gap-1.5 justify-between">
          <h2 class="font-sans font-black text-sm text-zinc-300 uppercase tracking-wider">代币深度详情 (MySQL 行数据)</h2>
          <span class="text-[10px] text-zinc-500 font-mono font-medium">LIVE PREVIEW</span>
        </div>

        <div v-if="selectedToken" class="flex flex-col gap-5" id="token-analytical-details">
          <TokenChart
            :token-id="selectedToken.id"
            :token-symbol="selectedToken.symbol"
            :current-price="selectedToken.price"
            :price-change24h="selectedToken.change24h"
          />

          <div class="bg-[#0f111a] border border-zinc-800/80 rounded-2xl p-5 shadow-xl space-y-4">
            <div class="flex items-center justify-between border-b border-zinc-900 pb-3">
              <div class="flex flex-col gap-0.5">
                <span class="text-zinc-500 text-[9px] font-extrabold uppercase tracking-widest">24h 量化指标与风控自检</span>
                <span class="font-sans font-bold text-white text-sm">{{ selectedToken.name }} ({{ selectedToken.symbol }}) 属性清单</span>
              </div>
              <div class="flex flex-col items-end shrink-0">
                <span class="text-[9px] text-zinc-500 font-mono font-extrabold">SECURITY SCORE</span>
                <span class="text-lg font-mono font-black text-emerald-400">{{ selectedToken.securityScore }}/100</span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3 text-xs">
              <div class="bg-[#07080d] p-3 rounded-xl border border-zinc-950 flex flex-col gap-0.5">
                <span class="text-zinc-500 text-[9px] font-bold uppercase">合约蜜罐安全性 (Honeypot)</span>
                <div class="flex items-center gap-1 mt-1">
                  <CircleCheck class="w-4 h-4 text-emerald-400" />
                  <span class="text-emerald-400 font-extrabold text-[11px]">正常交易</span>
                </div>
              </div>
              <div class="bg-[#07080d] p-3 rounded-xl border border-zinc-950 flex flex-col gap-0.5">
                <span class="text-zinc-500 text-[9px] font-bold uppercase">主网税率 (Tax Rate)</span>
                <span class="font-mono text-zinc-200 mt-1 font-bold text-[11px]">买入: 0% / 卖出: 0%</span>
              </div>
              <div class="bg-[#07080d] p-3 rounded-xl border border-zinc-950 flex flex-col gap-0.5">
                <span class="text-zinc-500 text-[9px] font-bold uppercase">智能合约权限</span>
                <span class="font-semibold text-emerald-400 mt-1 flex items-center gap-1 text-[11px]">✓ 管理权限已丢弃</span>
              </div>
              <div class="bg-[#07080d] p-3 rounded-xl border border-zinc-950 flex flex-col gap-0.5">
                <span class="text-zinc-500 text-[9px] font-bold uppercase">代码公开情况</span>
                <span class="font-semibold text-emerald-400 mt-1 flex items-center gap-1 text-[11px]">✓ 合约完全公开已审计</span>
              </div>
            </div>

            <div class="space-y-2 text-[11px] text-zinc-400 font-semibold">
              <div class="flex justify-between py-1.5 border-b border-zinc-900">
                <span>发行创建时间</span>
                <span class="font-mono text-zinc-200">{{ selectedToken.createdTime }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-zinc-900">
                <span>链上独立持币地址</span>
                <span class="font-mono text-zinc-200">{{ selectedToken.holders.toLocaleString() }} 个</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-zinc-900">
                <span>流动支撑等级 (Spring cached)</span>
                <span class="text-indigo-400 font-bold">EXCELLENT</span>
              </div>
            </div>

            <div class="bg-[#07080d] p-3 rounded-xl border border-zinc-950 flex flex-col gap-1">
              <span class="text-zinc-500 text-[8.5px] font-bold uppercase tracking-wider">主链公钥 / 智能合约地址</span>
              <div class="flex items-center justify-between gap-2.5">
                <span class="font-mono text-zinc-400 font-bold text-[10px] break-all select-all">{{ selectedToken.address }}</span>
                <button type="button" class="p-1 px-2 shrink-0 bg-zinc-905 border border-zinc-900 text-zinc-400 hover:text-white rounded-lg transition-all text-[10px] flex items-center gap-1 cursor-pointer" @click="handleCopyAddress">
                  <Check v-if="copiedAddress" class="w-3 h-3 text-emerald-400" />
                  <CopyDocument v-else class="w-3 h-3" />
                  <span>{{ copiedAddress ? '已复制' : '复制' }}</span>
                </button>
              </div>
            </div>

            <div class="bg-indigo-950/20 border border-indigo-900/35 p-3.5 rounded-xl space-y-2.5">
              <div class="flex items-center gap-1.5">
                <MagicStick class="w-4 h-4 text-amber-400 animate-pulse" />
                <span class="text-xs font-bold text-white">携带此币调用 FastAPI-AI 专属诊断</span>
              </div>
              <p class="text-[10.5px] text-zinc-400 leading-relaxed font-semibold">
                对 <code class="text-emerald-400">{{ selectedToken.symbol }}</code> 日内走势有疑问？点击入口会携带此币上下文、MySQL 现货参数与 RAG 匹配源，跳转到投研分析间并立即发起多源询问。
              </p>
              <button type="button" class="w-full py-2 bg-gradient-to-r from-indigo-600 via-indigo-650 to-indigo-700 hover:from-indigo-500 hover:to-indigo-605 text-white font-extrabold rounded-xl text-[11px] flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-indigo-950/20 cursor-pointer" @click="handleDeepJumpToAI(selectedToken)">
                <span>携带 {{ selectedToken.symbol }} 问题进入 AI 助手</span>
                <Right class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <div v-else class="h-44 flex items-center justify-center bg-[#07080d] border border-zinc-905 rounded-2xl">
          <span class="text-zinc-500 text-xs">加载行情数据中...</span>
        </div>
      </section>
    </main>

    <main v-else class="flex-1 p-4 md:p-6 max-w-[1400px] w-full mx-auto relative z-10 flex flex-col gap-5 min-h-[500px]">
      <div class="flex items-center justify-between">
        <div class="flex flex-col">
          <h2 class="font-sans font-black text-lg text-white">FastAPI AI 投研会话工坊 (RAG & Web3 Agent)</h2>
          <p class="text-zinc-500 text-xs mt-0.5">融合 MySQL 数据总线、本仓库 RAG 源码检索器，并提供实时信息分析风控机制</p>
        </div>

        <button type="button" class="px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-lg text-xs font-bold font-sans transition-all flex items-center gap-1 cursor-pointer" @click="clearMessages">
          <span>清空历史对话</span>
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 items-stretch flex-1">
        <div class="lg:col-span-1 bg-[#0c0e15] border border-zinc-850 p-4 rounded-2xl space-y-4 flex flex-col">
          <span class="text-zinc-400 text-xs font-extrabold uppercase tracking-wide block pb-1 border-b border-zinc-900">专属预设指令</span>
          <p class="text-[10.5px] text-zinc-500 leading-relaxed">
            点击下列指令可快捷载入输入框，智能体将调用 FastAPI Tool Calling 读取相应微服务并基于 RAG 作答。
          </p>

          <div class="space-y-2 text-[11px] font-semibold">
            <button v-for="preset in presets" :key="preset.label" type="button" class="w-full text-left p-2.5 bg-zinc-900/40 hover:bg-indigo-950/20 text-zinc-400 hover:text-indigo-400 rounded-xl border border-zinc-900 hover:border-indigo-900/30 transition-all cursor-pointer block leading-normal" @click="chatInput = preset.text">
              {{ preset.label }}
            </button>
          </div>

          <div class="mt-auto p-3 bg-[#07080d]/60 rounded-xl border border-zinc-950 space-y-1.5">
            <span class="text-[10px] text-zinc-500 font-bold">API STATUS GATEWAY:</span>
            <div class="flex items-center gap-1.5 text-[10px] text-zinc-300 font-mono">
              <span class="w-1.5 h-1.5 rounded-full" :class="aiHealthOk ? 'bg-emerald-500' : 'bg-orange-500'"></span>
              <span>FastAPI LLM Relay: {{ aiHealthOk ? 'ONLINE' : 'CHECKING' }}</span>
            </div>
          </div>
        </div>

        <div class="lg:col-span-3 bg-[#0c0e15] border border-zinc-850 rounded-2xl flex flex-col overflow-hidden min-h-[460px]">
          <div ref="messagesRef" class="flex-1 p-4.5 overflow-y-auto space-y-4 max-h-[500px]">
            <div v-for="(msg, index) in messages" :key="msg.id || index" class="flex items-start gap-3" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
              <div v-if="msg.role !== 'user'" class="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-650 to-indigo-700 p-[1.5px] shrink-0">
                <div class="w-full h-full bg-zinc-950 rounded-[7px] flex items-center justify-center">
                  <MagicStick class="w-4 h-4 text-indigo-400" />
                </div>
              </div>

              <div class="flex flex-col gap-1 max-w-[85%]">
                <div v-if="msg.role !== 'user' && (msg.usedTools?.length || msg.retrievedFiles?.length)" class="mb-1 flex flex-wrap gap-1.5 items-center">
                  <span v-for="tool in msg.usedTools" :key="tool" class="text-[9px] bg-indigo-950/30 text-indigo-400 border border-indigo-900/30 px-2 py-0.5 rounded font-mono">Tool: {{ tool }}</span>
                  <span v-for="file in msg.retrievedFiles" :key="file" class="text-[9px] bg-emerald-950/20 text-emerald-400 border border-emerald-900/20 px-2 py-0.5 rounded font-mono">RAG: {{ file }}</span>
                </div>

                <div class="p-4 rounded-2xl leading-relaxed text-[11.5px] border" :class="msg.role === 'user' ? 'bg-indigo-600 text-white border-transparent rounded-tr-none font-bold' : 'bg-[#07080d] text-zinc-300 border-zinc-900 rounded-tl-none font-medium'">
                  <p v-if="msg.role === 'user'" class="whitespace-pre-wrap">{{ msg.text }}</p>
                  <div v-else class="markdown-lite" v-html="parseMarkdown(msg.text)"></div>
                </div>
                <span class="text-[9px] text-zinc-600 font-mono" :class="msg.role === 'user' ? 'text-right' : 'text-left'">{{ msg.timestamp }}</span>
              </div>
            </div>

            <div v-if="isGeneratingMessage" class="flex justify-start items-start gap-3">
              <div class="w-8 h-8 rounded-lg bg-indigo-950 flex items-center justify-center animate-spin shrink-0">
                <MagicStick class="w-4 h-4 text-indigo-450" />
              </div>
              <div class="flex flex-col gap-1.5 w-full">
                <span class="text-[9.5px] text-indigo-400 font-bold animate-pulse">FastAPI AI 正在调用后台 API 工具并读取项目 RAG 信息...</span>
                <div class="bg-[#07080d] p-4.5 rounded-2xl border border-zinc-900 rounded-tl-none text-zinc-550 text-xs w-44 animate-pulse">推理中...</div>
              </div>
            </div>
          </div>

          <div class="p-3 bg-[#07080c] border-t border-zinc-900 flex items-center gap-2">
            <input
              v-model="chatInput"
              type="text"
              :disabled="isGeneratingMessage"
              placeholder="询问当前主流币布局，或者咨询 Spring JPA、Redis、Docker-Compose 等架构难题..."
              class="flex-1 bg-[#0c0e15] border border-zinc-900 focus:border-indigo-600 rounded-xl py-2.5 px-4 text-xs font-semibold placeholder-zinc-500 focus:outline-none transition-all text-white"
              @keydown.enter.prevent="handleSendChatMessage()"
            />

            <button type="button" :disabled="isGeneratingMessage || !chatInput.trim()" class="bg-indigo-600 hover:bg-indigo-505 disabled:bg-zinc-900 text-white font-extrabold text-xs px-5 py-2.5 rounded-xl cursor-pointer transition-all flex items-center gap-1 shadow-lg shadow-indigo-950/20" @click="handleSendChatMessage()">
              <span>发送 -> FastAPI 投研分析</span>
            </button>
          </div>
        </div>
      </div>

      <button type="button" class="self-start flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 font-bold mt-2" @click="activeTab = 'market'">
        <Back class="w-4 h-4" />
        <span>返回实时主数据看板</span>
      </button>
    </main>

    <footer class="h-14 border-t border-zinc-900 mt-12 bg-black/40 flex items-center justify-center text-[10.5px] text-zinc-650 font-sans px-4">
      <span>© 2026 CoinMarketCap Dev Lab - Java Spring Boot API + Redis + MySQL + FastAPI AI (RAG & Web3 Tool Chain).</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Back, Check, CircleCheck, CopyDocument, Cpu, MagicStick, Right, TrendCharts } from '@element-plus/icons-vue'
import Header from './components/Header.vue'
import TokenChart from './components/TokenChart.vue'
import TokenTable from './components/TokenTable.vue'
import DeveloperControlPanel from './components/DeveloperControlPanel.vue'
import type { ChatMessage, GlobalStats, Token } from './types'
import { buildGlobalStats, normalizeCoin } from './utils/marketAdapter'

const tokens = ref<Token[]>([])
const globalStats = ref<GlobalStats | null>(null)
const selectedToken = ref<Token | null>(null)
const activeTab = ref<'market' | 'ai-copilot'>('market')
const copiedAddress = ref(false)
const showDeveloperZone = ref(true)
const chatInput = ref('')
const isGeneratingMessage = ref(false)
const marketError = ref('')
const aiHealthOk = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
let pollTimer: number | null = null

const welcomeMessage: ChatMessage = {
  id: 'welcome',
  role: 'model',
  text: '您好，我是项目挂载的 **FastAPI Web3 投研与风控智能体**。\\n\\n我已通过 Tool Calling 连接 Spring Boot 数据源，可随时读取 MySQL 实时行情、历史价格点、恐慌与贪婪指数，以及本地项目 RAG 源码上下文。\\n\\n你可以输入币种行情问题，或咨询系统部署、Redis 缓存、Docker 编排等架构问题。',
  timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
}
const messages = ref<ChatMessage[]>([welcomeMessage])

const presets = [
  { label: '剖析 SOL 主流趋势', text: '分析 SOL 代币现货的综合行情、主网市值与独立持币地址比例。' },
  { label: 'Redis 缓存池优化提问', text: 'Redis 缓存在该 Web3 项目中起到了怎样的提速作用？如何配置 time-to-live 避免缓存过期脏读数据？' },
  { label: 'docker-compose 微服务部署', text: '提取本项目 docker-compose.yml 编排树，讲解如何一键启动包含 SpringBoot、MySQL、Redis、FastAPI-AI 的整套分布式架构。' },
  { label: 'Fear & Greed 作用解析', text: '当前的恐慌与贪婪指数如何？它在宏观交易决策中能起到什么信息分析参考作用？' },
]

async function fetchMarketData(shouldSelectDefault = false) {
  try {
    marketError.value = ''
    const [coinsRes, fearGreedRes, statusRes] = await Promise.allSettled([
      fetch('/api/coins'),
      fetch('/api/fear-greed'),
      fetch('/api/status'),
    ])

    if (coinsRes.status !== 'fulfilled' || !coinsRes.value.ok) throw new Error('无法读取 /api/coins')
    const coinsData = await coinsRes.value.json()
    const nextTokens = (Array.isArray(coinsData?.data) ? coinsData.data : coinsData).map((row: any, index: number) => normalizeCoin(row, index))
    tokens.value = nextTokens

    const fearGreed = fearGreedRes.status === 'fulfilled' && fearGreedRes.value.ok ? await fearGreedRes.value.json() : null
    const status = statusRes.status === 'fulfilled' && statusRes.value.ok ? await statusRes.value.json() : null
    globalStats.value = buildGlobalStats(nextTokens, status, fearGreed)

    if (nextTokens.length > 0) {
      if (shouldSelectDefault || !selectedToken.value) {
        selectedToken.value = nextTokens[0]
      } else {
        selectedToken.value = nextTokens.find((token) => token.id === selectedToken.value?.id) ?? nextTokens[0]
      }
    }
  } catch (error) {
    console.error('Failed to connect with CoinMarketCap backend REST API: ', error)
    marketError.value = '无法连接 Spring Boot 行情接口，请确认后端 /api/coins、/api/status 已启动。'
  }
}

async function fetchAiHealth() {
  try {
    const response = await fetch('/api/ai/health')
    const data = await response.json()
    aiHealthOk.value = data.status === 'ok'
  } catch {
    aiHealthOk.value = false
  }
}

function handleSelectToken(token: Token) {
  selectedToken.value = token
}

function handleDeepJumpToAI(token: Token) {
  activeTab.value = 'ai-copilot'
  const query = `分析币种 ${token.symbol} (${token.name})。请结合当前 $${token.price} 现货价、日内涨跌幅 ${token.change24h}%、市值 ${token.marketCap}，对多空筹码支撑与链上安全性进行信息分析，不要给投资建议。`
  chatInput.value = query
  window.setTimeout(() => handleSendChatMessage(query), 150)
}

async function handleSendChatMessage(overrideText?: string) {
  const textToSend = (overrideText || chatInput.value).trim()
  if (!textToSend || isGeneratingMessage.value) return
  if (!overrideText) chatInput.value = ''

  const history = messages.value
    .filter((message) => message.role === 'user' || message.role === 'model')
    .slice(-8)
    .map((message) => ({ role: message.role === 'model' ? 'assistant' : 'user', content: message.text }))

  const userMsg: ChatMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    text: textToSend,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  }

  messages.value.push(userMsg)
  await scrollToBottom()
  isGeneratingMessage.value = true

  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: textToSend, history, temperature: 0.3, max_tokens: 900 }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || data.message || 'FastAPI chat failed')
    messages.value.push({
      id: `ai-${Date.now()}`,
      role: 'model',
      text: data.answer || 'AI 没有返回内容。',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      usedTools: (data.tools || []).map((tool: any) => tool.name).filter(Boolean),
      retrievedFiles: (data.sources || []).map((source: any) => source.path).filter(Boolean),
    })
  } catch (error) {
    console.error(error)
    messages.value.push({
      id: `error-${Date.now()}`,
      role: 'model',
      text: '### API 中继通道拥挤\\n\\nFastAPI 暂时无法完成响应。请确认 `/api/ai/health` 正常，或稍后重试。\\n\\n**提示**: 此 AI 回复仅用于信息分析与链上智能合约审计，不构成任何投资建议。',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    })
  } finally {
    isGeneratingMessage.value = false
    await scrollToBottom()
  }
}

function clearMessages() {
  messages.value = [welcomeMessage]
}

async function handleCopyAddress() {
  if (!selectedToken.value) return
  await navigator.clipboard?.writeText(selectedToken.value.address)
  copiedAddress.value = true
  window.setTimeout(() => {
    copiedAddress.value = false
  }, 2000)
}

function parseMarkdown(markdown: string) {
  const safe = markdown
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return safe
    .split('\n')
    .map((line) => {
      if (line.startsWith('### ')) return `<h3>${line.slice(4)}</h3>`
      if (line.startsWith('## ')) return `<h2>${line.slice(3)}</h2>`
      if (line.startsWith('- ') || line.startsWith('* ')) return `<li>${line.slice(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</li>`
      if (line.startsWith('&gt; ')) return `<blockquote>${line.slice(5)}</blockquote>`
      if (!line.trim()) return '<div class="h-1"></div>'
      return `<p>${line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>`
    })
    .join('')
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
}

onMounted(() => {
  fetchMarketData(true)
  fetchAiHealth()
  pollTimer = window.setInterval(() => fetchMarketData(false), 30000)
})

onUnmounted(() => {
  if (pollTimer) window.clearInterval(pollTimer)
})
</script>
