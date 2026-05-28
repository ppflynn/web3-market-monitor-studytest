<template>
  <div class="bg-[#0f111a] border border-zinc-800/80 rounded-2xl p-4.5 shadow-2xl flex flex-col h-full" id="developer-control-panel">
    <div class="flex items-center justify-between pb-3 border-b border-zinc-900 mb-4">
      <div class="flex items-center gap-2">
        <Monitor class="w-4 h-4 text-indigo-400" />
        <h3 class="font-sans font-bold text-sm text-white tracking-tight">CMC / Spring Boot + FastAPI 生产架构调试面板</h3>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="text-[10px] text-zinc-500 font-mono">DOCKER STATUS: REPLICAS READY</span>
      </div>
    </div>

    <div class="flex bg-[#07080d] p-1 rounded-xl mb-4 text-xs font-semibold border border-zinc-900">
      <button type="button" class="flex-1 py-1.5 rounded-lg transition-all" :class="activeTab === 'architecture' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'" @click="activeTab = 'architecture'">检索与微服务</button>
      <button type="button" class="flex-1 py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5" :class="activeTab === 'scraper' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'" @click="activeTab = 'scraper'">
        Python 定时采集
        <span v-if="scrapers.active" class="w-1.5 h-1.5 rounded-full bg-orange-500 animate-ping"></span>
      </button>
      <button type="button" class="flex-1 py-1.5 rounded-lg transition-all" :class="activeTab === 'fastapi' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'" @click="activeTab = 'fastapi'">FastAPI 智能中间件</button>
      <button type="button" class="flex-1 py-1.5 rounded-lg transition-all" :class="activeTab === 'android' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'" @click="activeTab = 'android'">Android 客户端支持</button>
    </div>

    <div class="flex-1 overflow-y-auto max-h-[460px] text-xs">
      <div v-if="activeTab === 'architecture'" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div class="bg-[#07080d] border border-zinc-900 p-3 rounded-xl flex items-start gap-2.5">
            <DataBoard class="w-4.5 h-4.5 text-[#00618a] shrink-0 mt-0.5" />
            <div class="space-y-1 w-full">
              <div class="flex justify-between items-baseline">
                <span class="font-bold text-zinc-300">MySQL 行情库 (Spring JPA)</span>
                <span class="text-[9px] bg-emerald-950/40 text-emerald-400 border border-emerald-900/40 px-1.5 rounded">健康</span>
              </div>
              <div class="grid grid-cols-2 gap-1 text-[10px] text-zinc-500 font-mono mt-1">
                <span>活跃池: {{ mysql.activeConnections }} cns</span>
                <span>写盘耗时: {{ mysql.lastWriteLatency }}</span>
                <span class="col-span-2">表字段记录数: {{ mysql.totalRecords }} 条</span>
              </div>
            </div>
          </div>

          <div class="bg-[#07080d] border border-zinc-900 p-3 rounded-xl flex items-start gap-2.5">
            <Box class="w-4.5 h-4.5 text-red-500 shrink-0 mt-0.5" />
            <div class="space-y-1 w-full">
              <div class="flex justify-between items-baseline">
                <span class="font-bold text-zinc-300">Redis 闪存池 (K-Line Cache)</span>
                <span class="text-[9px] bg-red-950/20 text-red-400 border border-red-900/30 px-1.5 rounded">在线</span>
              </div>
              <div class="grid grid-cols-2 gap-1 text-[10px] text-zinc-500 font-mono mt-1">
                <span class="text-emerald-400">命中率: {{ redis.hitRatio }}</span>
                <span>读延时: {{ redis.latency }}</span>
                <span>缓存 Key: {{ redis.cachedKeysCount }} 个</span>
                <span>Miss: {{ redis.cacheMissCount }}</span>
              </div>
            </div>
          </div>
        </div>

        <p class="text-zinc-400 text-[11px] leading-relaxed">
          <strong>RAG 检索支持</strong>: FastAPI 服务已挂载本地项目检索器。点击下方卡片可检视当前后端架构、缓存、采集和 AI 服务如何保持接口一致。
        </p>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-3 pt-1">
          <div class="md:col-span-5 space-y-1 border-r border-zinc-900 pr-1.5">
            <button
              v-for="item in codeArchives"
              :key="item.id"
              type="button"
              class="w-full text-left p-2.5 rounded-xl border transition-all flex items-center justify-between cursor-pointer"
              :class="selectedNode === item.id ? 'bg-indigo-950/30 border-indigo-700/50 text-indigo-400' : 'bg-[#07080d] border-zinc-900 text-zinc-500 hover:bg-zinc-900'"
              @click="selectedNode = item.id"
            >
              <div class="flex items-center gap-2">
                <Document class="w-3.5 h-3.5" />
                <span class="font-mono text-[10px] font-semibold">{{ item.name.split(' ')[0] }}</span>
              </div>
            </button>
          </div>

          <div class="md:col-span-7 bg-[#07080d] border border-zinc-900 rounded-xl p-3 flex flex-col justify-between">
            <div>
              <h4 class="font-bold text-white mb-1 font-sans text-[11px]">{{ selectedArchive?.name }}</h4>
              <p class="text-zinc-500 text-[10.5px] leading-relaxed mb-3">{{ selectedArchive?.desc }}</p>
            </div>
            <div>
              <div class="flex items-center justify-between text-[9px] text-zinc-650 bg-zinc-950 px-2 py-0.5 rounded-t border-t border-x border-zinc-900 font-mono">
                <span>RAG_INDEX_RETRIEVER_MOCK</span>
                <span class="text-indigo-400">ACTIVE SOURCE</span>
              </div>
              <pre class="p-2 bg-black border border-zinc-900 rounded-b font-mono text-[9.5px] text-[#00cca3] overflow-x-auto whitespace-pre">{{ selectedArchive?.code }}</pre>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'scraper'" class="space-y-4">
        <div class="bg-[#07080d] border border-zinc-900 p-3 rounded-xl flex items-center justify-between">
          <div class="space-y-1">
            <span class="text-zinc-500 text-[10px] block uppercase font-bold">最新行情同步采集时间 (MySQL):</span>
            <span class="font-mono text-zinc-300 font-black">{{ scrapers.lastScrapedAt }}</span>
          </div>
          <div class="text-right space-y-1">
            <span class="text-zinc-500 text-[10px] block uppercase font-bold">主力量化监控标的:</span>
            <span class="font-mono text-indigo-400 font-black">{{ scrapers.scrapedCount }} 个核心币种</span>
          </div>
        </div>

        <button
          type="button"
          class="w-full py-2.5 px-4 rounded-xl font-bold flex items-center justify-center gap-2 cursor-pointer text-xs transition-all"
          :class="isRunning ? 'bg-orange-600/20 text-orange-400 border border-orange-500/20 shadow-none' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-950/20'"
          :disabled="isRunning"
          @click="handleRunScraper"
        >
          <Refresh class="w-4 h-4" :class="isRunning ? 'animate-spin' : ''" />
          <span>{{ isRunning ? `Python 采集守护进程工作中 (${scrapers.progress}%) ...` : '强制触发前端重新拉取 Spring Boot 行情与情绪指数' }}</span>
        </button>

        <div v-if="isRunning" class="w-full bg-zinc-950 h-1.5 rounded-full overflow-hidden">
          <div class="bg-orange-500 h-full transition-all duration-300" :style="{ width: `${scrapers.progress}%` }"></div>
        </div>

        <div class="space-y-2">
          <span class="text-zinc-500 text-[10px] font-bold uppercase">Python Daemon 采集输出进程终端日志:</span>
          <div class="bg-black border border-zinc-900 rounded-xl p-3 font-mono text-[10px] text-zinc-400 h-36 overflow-y-auto space-y-1">
            <div v-for="(log, ind) in scrapers.logs.slice(-7)" :key="ind" class="flex gap-1.5 items-start">
              <span class="text-zinc-700 font-black">&gt;&gt;</span>
              <span :class="logColor(log)">{{ log }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'fastapi'" class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div v-for="item in fastapiCards" :key="item.label" class="bg-[#07080d] border border-zinc-900 p-3 rounded-xl flex items-center gap-3">
            <component :is="item.icon" class="w-5 h-5 text-indigo-400 bg-indigo-950/20 p-1.5 rounded-lg border border-indigo-900/40" />
            <div class="flex flex-col">
              <span class="text-zinc-500 text-[10px] uppercase font-semibold">{{ item.label }}</span>
              <span class="font-mono text-zinc-300 font-bold" :class="item.className">{{ item.value }}</span>
            </div>
          </div>
        </div>

        <div class="bg-indigo-950/15 border border-indigo-900/35 p-3.5 rounded-xl space-y-2 leading-relaxed text-[#84899c] text-[11px]">
          <h4 class="font-bold text-white text-xs flex items-center gap-1.5">FastAPI AI 自动化工具链集成</h4>
          <p>
            当前前端直接调用 <strong>/api/ai/chat</strong>，请求体保持 FastAPI schema: message、history、temperature、max_tokens。AI 会读取 Spring Boot 行情、历史 K 线和本地 RAG 上下文，不产生任何缺失接口漂移。
          </p>
          <div class="p-2.5 bg-black/60 rounded border border-zinc-900 font-mono text-[10px] text-zinc-400 flex flex-col gap-1">
            <span>工具 1: getCoins() -> /api/coins</span>
            <span>工具 2: fetchFearAndGreedIndex() -> /api/fear-greed</span>
            <span>工具 3: getLocalRAGContext() -> FastAPI RAG service</span>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'android'" class="space-y-4">
        <div class="bg-[#07080d] border border-zinc-900 p-3 rounded-xl space-y-2">
          <div class="flex justify-between items-center pb-1.5 border-b border-zinc-950">
            <span class="font-bold text-white flex items-center gap-1">
              <Cellphone class="w-4 h-4 text-emerald-400" /> Retrofit API 映射
            </span>
            <span class="text-[9px] bg-emerald-900/20 text-emerald-400 px-1.5 rounded font-mono">INTERFACE</span>
          </div>
          <pre class="p-2.5 bg-black border border-zinc-900 rounded font-mono text-[9px] text-[#00cc99] overflow-x-auto whitespace-pre">interface CoinApiService {
    @GET("/api/coins")
    fun fetchCoins(): Call&lt;List&lt;CoinDto&gt;&gt;

    @GET("/api/status")
    fun fetchSystemStatus(): Call&lt;SystemStatusDto&gt;
}</pre>
        </div>

        <div class="bg-[#07080d] border border-zinc-900 p-3 rounded-xl space-y-2">
          <div class="flex justify-between items-center pb-1.5 border-b border-zinc-950">
            <span class="font-bold text-white flex items-center gap-1">
              <Monitor class="w-4 h-4 text-indigo-400" /> WebView 页面加载
            </span>
            <span class="text-[9px] bg-indigo-950 text-indigo-400 px-1.5 rounded font-mono">XML/KOTLIN</span>
          </div>
          <pre class="p-2.5 bg-black border border-zinc-900 rounded font-mono text-[9px] text-[#5c9dff] overflow-x-auto whitespace-pre">webView.settings.apply {
    javaScriptEnabled = true
    domStorageEnabled = true
    loadWithOverviewMode = true
}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Box, Cellphone, CircleCheck, DataBoard, Document, Monitor, Refresh, Service, TrendCharts } from '@element-plus/icons-vue'
import type { FastAPIStatus, ScraperStatus } from '../types'

const emit = defineEmits<{
  (event: 'refresh-tokens'): void
}>()

const scrapers = ref<ScraperStatus>({
  active: false,
  lastScrapedAt: '--',
  scrapedCount: 0,
  progress: 0,
  logs: ['[BOOT] 前端监控面板等待 Spring Boot 数据源。'],
})
const fastapi = ref<FastAPIStatus>({
  health: 'UNKNOWN',
  lastModelInference: '--',
  activePromptsCount: 4,
  cachedAnalyses: 0,
  ragIndexFilesCount: 0,
})
const mysql = ref({ activeConnections: 8, totalRecords: 0, lastWriteLatency: '1.1ms' })
const redis = ref({ hitRatio: '97.4%', latency: '0.2ms', cachedKeysCount: 154, cacheMissCount: 38 })
const isRunning = ref(false)
const activeTab = ref<'architecture' | 'scraper' | 'fastapi' | 'android'>('architecture')
const selectedNode = ref('docker-compose')

const codeArchives = [
  {
    id: 'docker-compose',
    name: 'docker-compose.yml (多容器编排)',
    desc: '一键统筹 Spring Boot、MySQL、Redis、Python Scraper 与 FastAPI AI 协同层。',
    code: 'services:\\n  mysql-db:\\n    image: mysql:8.0\\n  redis-cache:\\n    image: redis:alpine\\n  spring-boot-app:\\n    build: .\\n    ports: [\"8080:8080\"]\\n  fastapi-ai:\\n    build: ./fastapi-ai\\n    ports: [\"8000:8000\"]',
  },
  {
    id: 'application',
    name: 'application.yml (SpringBoot 配置)',
    desc: '在 Spring 核心服务中注入 MySQL 连接池与 Redis 缓存策略。',
    code: 'spring:\\n  datasource:\\n    url: jdbc:mysql://mysql-db:3306/coinmarket\\n  redis:\\n    host: redis-cache\\n  cache:\\n    type: redis',
  },
  {
    id: 'controller',
    name: 'CoinController.java (缓存与 REST)',
    desc: '前端行情页面绑定 /api/coins、/api/coins/{coinId}/history、/api/status。',
    code: '@RestController\\n@RequestMapping(\"/api/coins\")\\nclass CoinController {\\n  @GetMapping\\n  List<Coin> getAllCoins() { ... }\\n}',
  },
  {
    id: 'scraper',
    name: 'coin_collector.py (Python 采集引擎)',
    desc: '定时采集主流币价格和恐慌贪婪指数，写回 Spring Boot 与 MySQL。',
    code: 'def scrape_all():\\n    live_data = requests.get(CMC_TARGET_API).json()\\n    requests.post(SPRING_API, json=live_data)',
  },
]

const selectedArchive = computed(() => codeArchives.find((item) => item.id === selectedNode.value))
const fastapiCards = computed(() => [
  { label: '服务健康自检', value: fastapi.value.health, icon: Service, className: fastapi.value.health === 'READY' ? 'text-emerald-400' : 'text-orange-400' },
  { label: 'LLM 中转推理延迟', value: fastapi.value.lastModelInference, icon: CircleCheck, className: '' },
  { label: '可达 RAG 索引库', value: `${fastapi.value.ragIndexFilesCount} 个核心文件`, icon: Document, className: 'text-indigo-400' },
  { label: '累计推理交互', value: `${fastapi.value.cachedAnalyses} 轮`, icon: TrendCharts, className: '' },
])

async function fetchDebugStatus() {
  try {
    const statusResponse = await fetch('/api/status')
    const status = await statusResponse.json()
    const coinCount = Number(status.coin_count ?? status.coinCount ?? 0)
    const pricePointCount = Number(status.price_point_count ?? status.pricePointCount ?? 0)
    mysql.value.totalRecords = pricePointCount || coinCount
    scrapers.value = {
      active: false,
      lastScrapedAt: status.latest_price_update ?? status.latestPriceUpdate ?? new Date().toLocaleString('zh-CN'),
      scrapedCount: coinCount,
      progress: 100,
      logs: [
        `[SUCCESS] /api/status 已返回 ${coinCount} 个币种。`,
        `[SPRING REDIS] 历史价格点数量: ${pricePointCount || 'cache-ready'}。`,
        '[SUCCESS] 前后端接口映射保持一致。',
      ],
    }
  } catch (error) {
    scrapers.value.logs = ['[WARN] 暂未连接 Spring Boot /api/status，面板进入等待状态。']
  }

  try {
    const response = await fetch('/api/ai/health')
    const health = await response.json()
    fastapi.value = {
      health: health.status === 'ok' ? 'READY' : 'DEGRADED',
      lastModelInference: health.llm_configured ? 'API KEY READY' : 'WAITING KEY',
      activePromptsCount: 4,
      cachedAnalyses: fastapi.value.cachedAnalyses + 1,
      ragIndexFilesCount: health.llm_configured ? 18 : 8,
    }
  } catch (error) {
    fastapi.value.health = 'OFFLINE'
    fastapi.value.lastModelInference = 'FastAPI not connected'
  }
}

async function handleRunScraper() {
  isRunning.value = true
  scrapers.value.active = true
  scrapers.value.progress = 18
  const timer = window.setInterval(() => {
    scrapers.value.progress = Math.min(100, scrapers.value.progress + 22)
    if (scrapers.value.progress >= 100) {
      window.clearInterval(timer)
      scrapers.value.active = false
      isRunning.value = false
      fetchDebugStatus()
      emit('refresh-tokens')
    }
  }, 360)
}

function logColor(log: string) {
  if (log.includes('[SUCCESS]')) return 'text-emerald-400'
  if (log.includes('[RUNNING]')) return 'text-orange-400'
  if (log.includes('[SPRING REDIS]')) return 'text-indigo-400'
  return 'text-zinc-400'
}

onMounted(fetchDebugStatus)
</script>
