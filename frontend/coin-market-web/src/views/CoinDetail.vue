<template>
  <div class="coin-detail-page">
    <div class="detail-header">
      <el-button class="back-btn" @click="goBack" :icon="ArrowLeft" text>Back</el-button>
      <div class="coin-info" v-if="coin">
        <div class="coin-icon-fallback" :style="{ background: coinColor(coin) }">
          {{ coinInitial(coin) }}
        </div>
        <div class="coin-title">
          <h1 class="coin-name">{{ coin.name }}</h1>
          <span class="coin-symbol">{{ coin.symbol }}</span>
        </div>
      </div>
    </div>

    <el-alert
      v-if="errorMsg" :title="errorMsg" type="error" show-icon closable
      @close="errorMsg = ''" class="error-alert"
    />

    <div v-loading="detailLoading" class="stats-grid">
      <div class="stat-card">
        <span class="stat-label">Price</span>
        <span class="stat-value price-value">{{ formatPrice(coin?.current_price) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">24h Change</span>
        <span class="stat-value" :class="changeClass(coin?.price_change_percentage_24h)">
          <el-icon v-if="coin?.price_change_percentage_24h > 0"><CaretTop /></el-icon>
          <el-icon v-else-if="coin?.price_change_percentage_24h < 0"><CaretBottom /></el-icon>
          {{ formatChange(coin?.price_change_percentage_24h) }}
        </span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Market Cap</span>
        <span class="stat-value">{{ formatMarketCap(coin?.market_cap) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Last Updated</span>
        <span class="stat-value stat-time">{{ formatTime(coin?.last_updated) }}</span>
      </div>
    </div>

    <div class="chart-section">
      <div class="chart-header">
        <h2 class="chart-title">Price Chart</h2>
        <el-button-group class="time-toggle">
          <el-button
            :type="selectedDays === 7 ? 'primary' : 'default'"
            size="small" @click="selectDays(7)">7d</el-button>
          <el-button
            :type="selectedDays === 30 ? 'primary' : 'default'"
            size="small" @click="selectDays(30)">30d</el-button>
        </el-button-group>
      </div>

      <div v-loading="chartLoading" class="chart-wrapper">
        <v-chart
          v-if="chartOption"
          :option="chartOption"
          :autoresize="true"
          class="chart"
        />
        <div v-else-if="!chartLoading" class="chart-empty">
          <el-empty description="No history data available" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CaretTop, CaretBottom } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import 'echarts'
import { getCoinDetail, getCoinHistory } from '../api/coin.js'

const route = useRoute()
const router = useRouter()

const coin = ref(null)
const historyData = ref([])
const detailLoading = ref(false)
const chartLoading = ref(false)
const errorMsg = ref('')
const selectedDays = ref(7)

function coinInitial(c) {
  const name = c?.name
  if (name) return name.charAt(0).toUpperCase()
  const sym = c?.symbol
  return sym ? sym.charAt(0) : '?'
}

function coinColor(c) {
  const str = c?.name || c?.symbol || '?'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return `hsl(${Math.abs(hash) % 360}, 55%, 45%)`
}

function formatPrice(price) {
  if (price == null) return '$0.00'
  const num = Number(price)
  if (num >= 1) return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (num >= 0.01) return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 })
}

function formatChange(change) {
  if (change == null) return '0.00%'
  return Math.abs(Number(change)).toFixed(2) + '%'
}

function changeClass(change) {
  if (change == null) return 'neutral'
  const num = Number(change)
  if (num > 0) return 'positive'
  if (num < 0) return 'negative'
  return 'neutral'
}

function formatMarketCap(cap) {
  if (cap == null) return '$0'
  const num = Number(cap)
  if (num >= 1e12) return '$' + (num / 1e12).toFixed(2) + 'T'
  if (num >= 1e9) return '$' + (num / 1e9).toFixed(2) + 'B'
  if (num >= 1e6) return '$' + (num / 1e6).toFixed(2) + 'M'
  if (num >= 1e3) return '$' + (num / 1e3).toFixed(2) + 'K'
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatTime(time) {
  if (!time) return 'N/A'
  const d = new Date(time)
  if (isNaN(d.getTime())) return time
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function goBack() { router.push({ name: 'CoinList' }) }

function selectDays(days) { selectedDays.value = days; fetchHistory() }

const chartOption = computed(() => {
  if (!historyData.value.length) return null
  const dates = historyData.value.map(d => {
    const date = new Date(d.timestamp || d.date || d.time)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  })
  const prices = historyData.value.map(d => d.price ?? d.close ?? d.value)
  const lineColor = prices.length > 1 && prices[prices.length - 1] >= prices[0] ? '#34d399' : '#f87171'

  return {
    backgroundColor: 'transparent',
    grid: { top: 20, right: 20, bottom: 50, left: 60 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20,24,35,0.95)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: '#e2e8f0', fontSize: 13 },
      formatter: (params) => {
        const p = params[0]
        const val = Number(p.value)
        const formatted = val >= 1
          ? '$' + val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          : '$' + val.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 })
        return `<span style="color:#94a3b8">${p.axisValue}</span><br/><span style="font-weight:700;color:#e2e8f0">${formatted}</span>`
      }
    },
    xAxis: {
      type: 'category', data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisTick: { show: false },
      axisLabel: { color: '#64748b', fontSize: 11, interval: Math.max(Math.floor(dates.length / 8), 0) },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: {
        color: '#64748b', fontSize: 11,
        formatter: (val) => {
          if (val >= 1e6) return '$' + (val / 1e6).toFixed(2) + 'M'
          if (val >= 1e3) return '$' + (val / 1e3).toFixed(2) + 'K'
          if (val >= 1) return '$' + val.toFixed(2)
          return '$' + val.toFixed(6)
        }
      },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }
    },
    dataZoom: [
      {
        type: 'slider', start: 0, end: 100, height: 20, bottom: 6,
        backgroundColor: 'rgba(255,255,255,0.03)',
        dataBackground: {
          lineStyle: { color: 'rgba(255,255,255,0.06)' },
          areaStyle: { color: 'rgba(255,255,255,0.04)' }
        },
        selectedDataBackground: {
          lineStyle: { color: lineColor },
          areaStyle: { color: lineColor + '30' }
        },
        handleStyle: { color: lineColor },
        textStyle: { color: '#64748b', fontSize: 10 },
        fillerColor: lineColor + '20'
      }
    ],
    series: [{
      type: 'line', data: prices, smooth: true, showSymbol: false,
      lineStyle: { color: lineColor, width: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: lineColor + '30' },
            { offset: 1, color: lineColor + '02' }
          ]
        }
      }
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
    errorMsg.value = err.response?.data?.message || 'Failed to load coin details.'
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
.coin-detail-page {
  min-height: 100vh;
  padding: 24px 16px 60px;
  max-width: 1200px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.back-btn { color: #94a3b8; font-size: 14px; }
.back-btn:hover { color: #e2e8f0; }

.coin-info { display: flex; align-items: center; gap: 12px; }

.coin-icon-fallback {
  width: 42px; height: 42px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 18px; flex-shrink: 0;
}

.coin-title { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.coin-name { font-size: 24px; font-weight: 700; color: #f1f5f9; margin: 0; }
.coin-symbol { font-size: 15px; font-weight: 600; color: #64748b; text-transform: uppercase; }

.error-alert {
  margin-bottom: 20px;
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: 12px;
}
.error-alert :deep(.el-alert__title) { color: #fca5a5; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 32px;
}

.stat-card {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 16px 18px;
  display: flex; flex-direction: column; gap: 6px;
}

.stat-label { font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.03em; }
.stat-value { font-size: 18px; font-weight: 700; color: #e2e8f0; font-variant-numeric: tabular-nums; }
.stat-value.positive { color: #34d399; }
.stat-value.negative { color: #f87171; }
.stat-value.neutral { color: #e2e8f0; }
.stat-time { font-size: 14px; font-weight: 500; }

.price-value { font-size: 20px; }

.chart-section {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.chart-title { font-size: 16px; font-weight: 600; color: #e2e8f0; margin: 0; }

.time-toggle :deep(.el-button) {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  color: #94a3b8;
}
.time-toggle :deep(.el-button--primary) {
  background: rgba(59,130,246,0.2);
  border-color: rgba(59,130,246,0.4);
  color: #60a5fa;
}

.chart-wrapper { position: relative; min-height: 300px; }
.chart { width: 100%; height: 380px; }
.chart-empty { padding: 40px 0; }
.chart-empty :deep(.el-empty__description) { color: #64748b; }

@media (max-width: 768px) {
  .coin-detail-page { padding: 16px 12px 40px; }
  .coin-name { font-size: 20px; }
  .coin-icon-fallback { width: 36px; height: 36px; font-size: 16px; }

  .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .stat-card { padding: 12px 14px; }
  .stat-value { font-size: 16px; }
  .price-value { font-size: 18px; }
  .stat-time { font-size: 12px; }

  .chart-section { padding: 14px; }
  .chart { height: 280px; }
  .chart-wrapper { min-height: 240px; }
}
</style>
