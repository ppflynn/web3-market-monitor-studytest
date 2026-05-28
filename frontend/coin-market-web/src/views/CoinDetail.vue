<template>
  <div class="detail-page">
    <section class="detail-title">
      <div>
        <el-button class="back-btn" @click="goBack" :icon="ArrowLeft" text>返回行情</el-button>
        <div class="coin-heading" v-if="coin">
          <span class="coin-icon" :style="{ background: coinColor(coin) }">{{ coinInitial(coin) }}</span>
          <div>
            <h1>{{ nameOf(coin) }}</h1>
            <p>{{ symbolOf(coin) }} / USD</p>
          </div>
        </div>
      </div>
      <div class="price-summary" v-if="coin">
        <span>当前价格</span>
        <strong>{{ formatPrice(priceOf(coin)) }}</strong>
        <em :class="changeClass(changeOf(coin))">{{ formatSignedChange(changeOf(coin)) }}</em>
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

    <section class="detail-layout">
      <main class="panel chart-panel">
        <div class="panel-head">
          <div>
            <h2>价格走势</h2>
            <p>{{ selectedDays }} 天历史价格序列</p>
          </div>
          <div class="chart-actions">
            <button type="button" @click="openAiAssistant">AI 分析</button>
            <button type="button" :class="{ active: selectedDays === 7 }" @click="selectDays(7)">7D</button>
            <button type="button" :class="{ active: selectedDays === 30 }" @click="selectDays(30)">30D</button>
          </div>
        </div>
        <div v-loading="chartLoading" class="chart-wrapper">
          <v-chart v-if="chartOption" :option="chartOption" :autoresize="true" class="chart" />
          <div v-else-if="!chartLoading" class="chart-empty">
            <el-empty description="暂无历史数据" />
          </div>
        </div>
      </main>

      <aside class="side-stack">
        <section v-loading="detailLoading" class="panel side-panel">
          <h3>币种数据</h3>
          <div class="metric-list">
            <div><span>当前价格</span><strong>{{ formatPrice(priceOf(coin)) }}</strong></div>
            <div><span>24h 涨跌</span><strong :class="changeClass(changeOf(coin))">{{ formatSignedChange(changeOf(coin)) }}</strong></div>
            <div><span>市值</span><strong>{{ formatMarketCap(marketCapOf(coin)) }}</strong></div>
            <div><span>最后更新</span><strong>{{ formatTime(lastUpdatedOf(coin)) }}</strong></div>
          </div>
        </section>

        <section class="panel ai-panel">
          <h3>AI 信息分析</h3>
          <p>基于当前币种、历史价格和项目数据库上下文进入 AI 助手，不提供投资建议。</p>
          <button type="button" @click="openAiAssistant">打开 AI 助手</button>
        </section>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import 'echarts'
import { getCoinDetail, getCoinHistory } from '../api/coin.js'
import { formatAppDateTime, formatAppShortDate } from '../utils/time.js'

const route = useRoute()
const router = useRouter()
const coin = ref(null)
const historyData = ref([])
const detailLoading = ref(false)
const chartLoading = ref(false)
const errorMsg = ref('')
const selectedDays = ref(7)

function valueOf(row, snakeKey, camelKey) { return row ? (row[snakeKey] ?? row[camelKey] ?? null) : null }
function nameOf(row) { return row?.name ?? '' }
function symbolOf(row) { return row?.symbol ? String(row.symbol).toUpperCase() : '' }
function priceOf(row) { const v = valueOf(row, 'current_price', 'currentPrice'); return v != null ? Number(v) : null }
function changeOf(row) {
  const v = row?.price_change_percentage_24h ?? row?.price_change_percentage24h ?? row?.priceChangePercentage24h
  return v != null ? Number(v) : null
}
function marketCapOf(row) { const v = valueOf(row, 'market_cap', 'marketCap'); return v != null ? Number(v) : null }
function lastUpdatedOf(row) { return valueOf(row, 'last_updated', 'lastUpdated') }
function coinInitial(c) { const sym = symbolOf(c); return sym ? sym.slice(0, 2) : (nameOf(c).charAt(0).toUpperCase() || '?') }
function coinColor(c) {
  const str = nameOf(c) || symbolOf(c) || '?'
  let hash = 0
  for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash)
  return `hsl(${Math.abs(hash) % 360}, 72%, 45%)`
}
function formatPrice(price) {
  if (price == null) return '$ --'
  const num = Number(price)
  if (num === 0) return '$0.00'
  if (num >= 1) return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (num >= 0.01) return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 })
}
function formatSignedChange(change) {
  if (change == null) return '--'
  const num = Number(change)
  const sign = num > 0 ? '+' : num < 0 ? '-' : ''
  return sign + Math.abs(num).toFixed(2) + '%'
}
function changeClass(change) {
  if (change == null || Number(change) === 0) return 'neutral'
  return Number(change) > 0 ? 'positive' : 'negative'
}
function formatMarketCap(cap) {
  if (cap == null) return '--'
  const num = Number(cap)
  if (num >= 1e12) return '$' + (num / 1e12).toFixed(2) + 'T'
  if (num >= 1e9) return '$' + (num / 1e9).toFixed(2) + 'B'
  if (num >= 1e6) return '$' + (num / 1e6).toFixed(2) + 'M'
  if (num >= 1e3) return '$' + (num / 1e3).toFixed(2) + 'K'
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function formatTime(time) { return formatAppDateTime(time, '暂无') }
function goBack() { router.push({ name: 'CoinList' }) }
function openAiAssistant() {
  router.push({
    name: 'AiAssistant',
    query: { q: `${symbolOf(coin.value) || route.params.coinId} 最近走势怎么看？请基于项目数据库和历史价格做信息分析，不要给投资建议。` }
  })
}
function selectDays(days) { if (selectedDays.value !== days) { selectedDays.value = days; fetchHistory() } }

const chartOption = computed(() => {
  if (!historyData.value.length) return null
  const dates = historyData.value.map(d => formatAppShortDate(d.timestamp || d.date || d.time))
  const prices = historyData.value.map(d => Number(d.price ?? d.close ?? d.value)).filter(v => !Number.isNaN(v))
  if (!prices.length) return null
  const lineColor = prices.length > 1 && prices[prices.length - 1] >= prices[0] ? '#16a34a' : '#ef4444'
  return {
    backgroundColor: 'transparent',
    grid: { top: 24, right: 24, bottom: 42, left: 68 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#ebedf0',
      textStyle: { color: '#111', fontSize: 12 },
      formatter: (params) => `${params[0].axisValue}<br/><b>${formatPrice(Number(params[0].value))}</b>`
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#ebedf0' } },
      axisTick: { show: false },
      axisLabel: { color: '#707a8a', fontSize: 11, interval: Math.max(Math.floor(dates.length / 7), 0) }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#707a8a', fontSize: 11 },
      splitLine: { lineStyle: { color: '#ebedf0' } }
    },
    series: [{
      type: 'line',
      data: prices,
      smooth: true,
      showSymbol: false,
      lineStyle: { color: lineColor, width: 2 },
      areaStyle: { color: lineColor + '18' }
    }]
  }
})

async function fetchDetail() {
  const coinId = route.params.coinId
  if (!coinId) return
  try {
    detailLoading.value = true
    errorMsg.value = ''
    const res = await getCoinDetail(coinId)
    coin.value = res.data?.data ?? res.data ?? null
  } catch (err) {
    console.error('Failed to fetch coin detail:', err)
    errorMsg.value = err.response?.data?.message || '币种详情加载失败，请稍后重试。'
  } finally {
    detailLoading.value = false
  }
}
async function fetchHistory() {
  const coinId = route.params.coinId
  if (!coinId) return
  try {
    chartLoading.value = true
    const res = await getCoinHistory(coinId, selectedDays.value)
    historyData.value = res.data?.data ?? res.data ?? []
  } catch (err) {
    console.error('Failed to fetch history:', err)
    historyData.value = []
  } finally {
    chartLoading.value = false
  }
}
watch(() => route.params.coinId, () => { fetchDetail(); fetchHistory() })
onMounted(() => { fetchDetail(); fetchHistory() })
</script>

<style scoped>
.detail-page {
  width: min(1280px, 100%);
  min-height: calc(100vh - 64px);
  margin: 0 auto;
  padding: 28px 24px 56px;
}

.detail-title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

.back-btn {
  margin-bottom: 12px;
  color: #707a8a;
  font-weight: 700;
}

.coin-heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.coin-icon {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.coin-heading h1 {
  margin: 0;
  color: #111;
  font-size: 30px;
  font-weight: 800;
}

.coin-heading p,
.price-summary span,
.panel-head p,
.ai-panel p {
  margin: 4px 0 0;
  color: #707a8a;
  font-size: 13px;
}

.price-summary {
  text-align: right;
}

.price-summary strong {
  display: block;
  margin: 6px 0 3px;
  color: #111;
  font-size: 28px;
  font-weight: 800;
}

.price-summary em {
  font-style: normal;
  font-weight: 800;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
}

.panel {
  border: 1px solid #ebedf0;
  border-radius: 16px;
  background: #fff;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid #ebedf0;
}

.panel-head h2,
.side-panel h3,
.ai-panel h3 {
  margin: 0;
  color: #111;
  font-size: 18px;
  font-weight: 800;
}

.chart-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-actions button,
.ai-panel button {
  height: 32px;
  border: 1px solid #ebedf0;
  border-radius: 16px;
  padding: 0 12px;
  color: #111;
  background: #fff;
  cursor: pointer;
  font-weight: 700;
}

.chart-actions button.active,
.chart-actions button:hover,
.ai-panel button:hover {
  border-color: #111;
}

.chart-wrapper {
  min-height: 410px;
  padding: 8px;
}

.chart {
  width: 100%;
  height: 400px;
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.side-panel,
.ai-panel {
  padding: 18px;
}

.metric-list {
  display: grid;
  margin-top: 14px;
  border-top: 1px solid #ebedf0;
}

.metric-list div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #ebedf0;
}

.metric-list span {
  color: #707a8a;
  font-size: 13px;
}

.metric-list strong {
  color: #111;
  font-size: 13px;
  font-weight: 800;
  text-align: right;
}

.positive {
  color: #16a34a !important;
}

.negative {
  color: #ef4444 !important;
}

.neutral {
  color: #707a8a !important;
}

.ai-panel button {
  width: 100%;
  margin-top: 14px;
  color: #fff;
  border-color: #111;
  background: #111;
}

@media (max-width: 900px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .detail-page {
    padding: 20px 12px 40px;
  }
  .detail-title,
  .panel-head {
    align-items: stretch;
    flex-direction: column;
  }
  .price-summary {
    text-align: left;
  }
}
</style>
