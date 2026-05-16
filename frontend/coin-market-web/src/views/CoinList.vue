<template>
  <div class="market-page">
    <div class="page-header">
      <div class="title-row">
        <h1 class="title">加密货币实时行情</h1>
        <span class="live-dot" v-if="!error"></span>
        <span class="live-text" v-if="!error">实时</span>
      </div>
      <div class="header-right">
        <div class="fng-card" v-if="fng" :class="fngClass">
          <span class="fng-label">Fear & Greed</span>
          <div class="fng-meter">
            <div class="fng-bar">
              <div class="fng-fill" :style="{ width: fng.value + '%' }"></div>
            </div>
            <span class="fng-value">{{ fng.value }}</span>
          </div>
          <span class="fng-class">{{ fng.classification }}</span>
        </div>
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索币种..."
            clearable
            size="large"
            class="search-input"
          />
        </div>
      </div>
    </div>

    <el-alert
      v-if="error" :title="error" type="error" show-icon closable
      @close="error = ''" class="error-alert">
      <template #default>
        <el-button text type="primary" size="small" @click="fetchData">重试</el-button>
      </template>
    </el-alert>

    <div v-if="loading && allCoins.length === 0" class="skeleton-area">
      <div class="glass-card">
        <el-skeleton :rows="10" animated />
      </div>
    </div>

    <div v-else class="content-area">
      <div class="table-glass">
        <el-table
          :data="filteredCoins"
          stripe style="width: 100%"
          v-loading="loading"
          element-loading-background="rgba(11,14,20,0.6)"
          @row-click="onRowClick"
          :header-cell-style="headerStyle"
          :cell-style="cellStyle"
        >
          <el-table-column label="#" width="60" align="center">
            <template #default="{ $index }">
              <span class="rank-num">{{ $index + 1 }}</span>
            </template>
          </el-table-column>

          <el-table-column label="币种" min-width="180">
            <template #default="{ row }">
              <div class="coin-cell">
                <div class="coin-icon-fallback" :style="{ background: coinColor(row) }">
                  {{ coinInitial(row) }}
                </div>
                <div class="coin-text">
                  <span class="coin-symbol-text">{{ symbolOf(row) }}</span>
                  <span class="coin-name-text">{{ nameOf(row) }}</span>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="最新价" min-width="140" align="right">
            <template #default="{ row }">
              <span class="price-text">{{ formatPrice(priceOf(row)) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="24h涨跌幅" min-width="130" align="right">
            <template #default="{ row }">
              <span class="change-tag" :class="changeDir(row)">
                <span class="change-arrow">{{ changeArrow(row) }}</span>
                {{ formatChange(changeOf(row)) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="24h成交量" min-width="140" align="right">
            <template #default="{ row }">
              <span class="volume-text">{{ formatVolume(volumeOf(row)) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="mobile-cards">
        <div
          class="mobile-card"
          v-for="(row, idx) in filteredCoins"
          :key="coinIdOf(row) || idx"
          @click="onRowClick(row)"
        >
          <div class="mc-top">
            <div class="coin-icon-fallback" :style="{ background: coinColor(row) }">
              {{ coinInitial(row) }}
            </div>
            <div class="mc-info">
              <span class="coin-symbol-text">{{ symbolOf(row) }}</span>
              <span class="coin-name-text">{{ nameOf(row) }}</span>
            </div>
            <span class="mc-rank">#{{ idx + 1 }}</span>
          </div>
          <div class="mc-bottom">
            <div class="mc-stat">
              <span class="mc-label">Price</span>
              <span class="price-text">{{ formatPrice(priceOf(row)) }}</span>
            </div>
            <div class="mc-stat">
              <span class="mc-label">24h</span>
              <span class="change-tag" :class="changeDir(row)">
                {{ formatChange(changeOf(row)) }}
              </span>
            </div>
            <div class="mc-stat">
              <span class="mc-label">Vol</span>
              <span class="volume-text">{{ formatVolume(volumeOf(row)) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="filteredCoins.length === 0 && !loading && !error" class="empty-state">
      <el-empty description="暂无数据" :image-size="80" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCoinList, getFearGreed } from '../api/coin.js'

const router = useRouter()

const allCoins = ref([])
const loading = ref(false)
const error = ref('')
const searchKeyword = ref('')
const fng = ref(null)

let pollTimer = null

const headerStyle = () => ({
  background: 'rgba(255,255,255,0.04)',
  color: '#64748b', fontWeight: 600, fontSize: '12px',
  borderBottom: '1px solid rgba(255,255,255,0.06)', height: '46px'
})

const cellStyle = () => ({
  borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer', height: '56px'
})

const fngClass = computed(() => {
  if (!fng.value) return ''
  const v = fng.value.value
  if (v <= 25) return 'fng-extreme-fear'
  if (v <= 45) return 'fng-fear'
  if (v <= 55) return 'fng-neutral'
  if (v <= 75) return 'fng-greed'
  return 'fng-extreme-greed'
})

function safeProp(row, key) { return row ? (row[key] ?? '') : '' }
function coinIdOf(row) { return safeProp(row, 'coin_id') || safeProp(row, 'coinId') }
function nameOf(row) { return safeProp(row, 'name') }
function symbolOf(row) {
  const sym = safeProp(row, 'symbol')
  return sym ? sym.toUpperCase() : ''
}
function priceOf(row) {
  const v = row?.current_price ?? row?.currentPrice
  return v != null ? Number(v) : null
}
function changeOf(row) {
  const v = row?.price_change_percentage_24h ?? row?.priceChangePercentage24h
  return v != null ? Number(v) : null
}
function volumeOf(row) {
  const v = row?.total_volume ?? row?.totalVolume ?? row?.base_volume ?? row?.baseVolume
  return v != null ? Number(v) : null
}

function coinInitial(row) {
  const name = nameOf(row)
  if (name) return name.charAt(0).toUpperCase()
  const sym = symbolOf(row)
  return sym ? sym.charAt(0) : '?'
}

function coinColor(row) {
  const str = nameOf(row) || symbolOf(row) || '?'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return `hsl(${Math.abs(hash) % 360}, 55%, 45%)`
}

function changeDir(row) {
  const v = changeOf(row)
  if (v == null) return 'neutral'
  if (v > 0) return 'up'
  if (v < 0) return 'down'
  return 'neutral'
}

function changeArrow(row) {
  const v = changeOf(row)
  if (v == null) return ''
  if (v > 0) return '▲'
  if (v < 0) return '▼'
  return ''
}

function formatPrice(price) {
  if (price == null) return '$ --'
  const num = Number(price)
  if (num === 0) return '$0.00'
  if (num >= 1) return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (num >= 0.01) return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 })
}

function formatChange(change) {
  if (change == null) return '--'
  return Math.abs(Number(change)).toFixed(2) + '%'
}

function formatVolume(vol) {
  if (vol == null) return '--'
  if (vol === 0) return '$0'
  const num = Number(vol)
  if (num >= 1e12) return '$' + (num / 1e12).toFixed(2) + 'T'
  if (num >= 1e9) return '$' + (num / 1e9).toFixed(2) + 'B'
  if (num >= 1e6) return '$' + (num / 1e6).toFixed(2) + 'M'
  if (num >= 1e3) return '$' + (num / 1e3).toFixed(2) + 'K'
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const filteredCoins = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  if (!kw) return allCoins.value
  return allCoins.value.filter(row => {
    const name = nameOf(row).toLowerCase()
    const sym = symbolOf(row).toLowerCase()
    return name.includes(kw) || sym.includes(kw)
  })
})

function onRowClick(row) {
  const id = coinIdOf(row)
  if (id) router.push('/coin/' + id)
}

async function fetchData() {
  try {
    loading.value = true
    error.value = ''
    const res = await getCoinList()
    allCoins.value = res.data?.data ?? res.data ?? []
  } catch (err) {
    console.error('Failed to fetch coin list:', err)
    if (allCoins.value.length === 0) error.value = '网络请求失败，请检查网络连接后重试'
  } finally {
    loading.value = false
  }
}

async function fetchFng() {
  try {
    const res = await getFearGreed()
    fng.value = res.data?.data ?? res.data ?? null
  } catch (err) {
    console.error('Failed to fetch F&G:', err)
  }
}

onMounted(() => {
  fetchData()
  fetchFng()
  pollTimer = setInterval(() => {
    fetchData()
    fetchFng()
  }, 60000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.market-page {
  min-height: 100vh;
  padding: 24px 16px 60px;
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 22px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.live-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 6px rgba(52,211,153,0.5);
  animation: pulse-dot 2s ease-in-out infinite;
}

.live-text {
  font-size: 11px;
  font-weight: 600;
  color: #34d399;
  text-transform: uppercase;
}

@keyframes pulse-dot {
  0%,100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fng-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 8px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
  transition: border-color 0.3s;
}

.fng-card.fng-extreme-fear { border-color: rgba(239,68,68,0.5); }
.fng-card.fng-fear { border-color: rgba(245,158,11,0.5); }
.fng-card.fng-neutral { border-color: rgba(148,163,184,0.5); }
.fng-card.fng-greed { border-color: rgba(34,197,94,0.5); }
.fng-card.fng-extreme-greed { border-color: rgba(34,197,94,0.8); }

.fng-label {
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.fng-meter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fng-bar {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 3px;
  overflow: hidden;
}

.fng-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s;
  background: linear-gradient(90deg, #ef4444, #f59e0b, #eab308, #22c55e, #16a34a);
  background-size: 200% 100%;
}

.fng-value {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  font-variant-numeric: tabular-nums;
  min-width: 28px;
  text-align: right;
}

.fng-class {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

.search-box {
  width: 180px;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  box-shadow: none;
  height: 40px;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(255,255,255,0.14);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(59,130,246,0.5);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

.search-input :deep(.el-input__inner) {
  color: #e2e8f0;
  font-size: 13px;
}

.search-input :deep(.el-input__inner::placeholder) {
  color: #475569;
}

.error-alert {
  margin-bottom: 16px;
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: 12px;
}

.error-alert :deep(.el-alert__title) { color: #fca5a5; }

.skeleton-area { margin-top: 4px; }

.glass-card {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 28px;
}

.glass-card :deep(.el-skeleton__item) {
  background: rgba(255,255,255,0.06);
  border-radius: 6px;
}

.content-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.table-glass {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  overflow: hidden;
}

.table-glass :deep(.el-table) {
  background: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255,255,255,0.05);
  --el-table-border-color: rgba(255,255,255,0.04);
  --el-table-text-color: #e2e8f0;
  font-size: 14px;
}

.table-glass :deep(.el-table th.el-table__cell) { background: rgba(255,255,255,0.03); }
.table-glass :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background: rgba(255,255,255,0.02); }
.table-glass :deep(.el-table .el-table__body tr:hover > td) { background: rgba(255,255,255,0.06); }
.table-glass :deep(.el-loading-mask) { background: rgba(11,14,20,0.6); backdrop-filter: blur(4px); }

.rank-num { color: #64748b; font-size: 13px; font-weight: 500; }

.coin-cell { display: flex; align-items: center; gap: 12px; }

.coin-icon-fallback {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 15px;
  flex-shrink: 0;
}

.coin-text { display: flex; flex-direction: column; line-height: 1.3; }
.coin-symbol-text { font-size: 13px; font-weight: 600; color: #e2e8f0; text-transform: uppercase; }
.coin-name-text { font-size: 11px; color: #64748b; }

.price-text { font-weight: 600; color: #e2e8f0; font-size: 14px; font-variant-numeric: tabular-nums; }

.change-tag {
  font-weight: 600; font-size: 13px;
  font-variant-numeric: tabular-nums;
  display: inline-flex; align-items: center; gap: 2px;
  padding: 2px 7px; border-radius: 5px;
}
.change-tag.up { color: #34d399; background: rgba(52,211,153,0.1); }
.change-tag.down { color: #f87171; background: rgba(248,113,113,0.1); }
.change-tag.neutral { color: #64748b; }
.change-arrow { font-size: 9px; }

.volume-text { font-weight: 500; color: #94a3b8; font-size: 13px; font-variant-numeric: tabular-nums; }

.mobile-cards { display: none; flex-direction: column; gap: 8px; }

.mobile-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.mobile-card:active { background: rgba(255,255,255,0.06); }

.mc-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.mc-info { display: flex; flex-direction: column; line-height: 1.3; flex: 1; }
.mc-rank { color: #64748b; font-size: 12px; font-weight: 600; }

.mc-bottom { display: flex; justify-content: space-between; gap: 8px; }
.mc-stat { display: flex; flex-direction: column; gap: 2px; }
.mc-label { font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 500; }

.empty-state { margin-top: 40px; }
.empty-state :deep(.el-empty__description) { color: #64748b; }

@media (min-width: 769px) {
  .mobile-cards { display: none !important; }
}

@media (max-width: 768px) {
  .table-glass { display: none !important; }
  .mobile-cards { display: flex !important; }

  .market-page { padding: 16px 12px 40px; }
  .page-header { flex-direction: column; align-items: stretch; gap: 10px; }

  .header-right {
    flex-direction: column;
    gap: 8px;
  }

  .search-box { width: 100%; }

  .fng-card {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    width: 100%;
  }

  .fng-label { flex-shrink: 0; }
  .fng-meter { flex: 1; }
  .fng-class { flex-shrink: 0; }
  .fng-value { font-size: 16px; min-width: 24px; }

  .title { font-size: 20px; }

  .mc-bottom .price-text { font-size: 14px; }
  .mc-bottom .change-tag { font-size: 12px; }
  .mc-bottom .volume-text { font-size: 12px; }
}
</style>
