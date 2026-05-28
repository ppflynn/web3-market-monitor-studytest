<template>
  <div class="market-page">
    <section class="page-title">
      <div>
        <h1>代币行情</h1>
        <p>跟踪项目数据库里的币种价格、24h 涨跌、市值与更新时间。</p>
      </div>
      <button type="button" class="refresh-button" :disabled="loading" @click="refreshAll">
        {{ loading ? '刷新中' : '刷新' }}
      </button>
    </section>

    <section class="market-card">
      <div class="top-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="toolbar">
        <label class="search-box">
          <span>搜索</span>
          <input v-model="searchKeyword" type="search" placeholder="搜索代币名称 / Symbol" />
        </label>

        <div class="sort-pills" aria-label="排序">
          <button
            v-for="item in sortOptions"
            :key="item.value"
            type="button"
            :class="{ active: sortKey === item.value }"
            @click="sortKey = item.value"
          >
            {{ item.label }}
          </button>
        </div>
      </div>

      <div class="status-strip" v-if="fng || systemStatus">
        <div v-if="fng">
          <span>恐惧贪婪指数</span>
          <strong>{{ fngValue }}</strong>
          <em>{{ fngClassificationLabel(fng.classification) }}</em>
        </div>
        <div v-if="systemStatus">
          <span>系统状态</span>
          <strong>{{ systemStatusOf(systemStatus) }}</strong>
          <em>{{ numberOf(systemStatus, 'coin_count', 'coinCount') }} coins</em>
        </div>
        <div v-if="systemStatus">
          <span>最近更新</span>
          <strong>{{ formatStatusTime(timeOf(systemStatus, 'latest_price_update', 'latestPriceUpdate')) }}</strong>
        </div>
      </div>

      <el-alert
        v-if="error"
        :title="error"
        type="error"
        show-icon
        closable
        class="error-alert"
        @close="error = ''"
      >
        <template #default>
          <el-button text type="primary" size="small" @click="refreshAll">重试</el-button>
        </template>
      </el-alert>

      <div v-if="loading && allCoins.length === 0" class="skeleton-card">
        <el-skeleton :rows="9" animated />
      </div>

      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>代币</th>
              <th class="right">价格</th>
              <th class="right">24h 涨跌</th>
              <th class="right">市值</th>
              <th class="right">最后更新</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in sortedCoins" :key="coinIdOf(row) || index">
              <td>
                <div class="token-cell">
                  <span class="rank">{{ index + 1 }}</span>
                  <span class="token-icon" :style="{ background: coinColor(row) }">{{ coinInitial(row) }}</span>
                  <span class="token-copy">
                    <strong>{{ symbolOf(row) }}</strong>
                    <small>{{ nameOf(row) }}</small>
                  </span>
                </div>
              </td>
              <td class="right number primary">{{ formatPrice(priceOf(row)) }}</td>
              <td class="right">
                <span class="change" :class="changeDir(row)">
                  {{ formatSignedChange(changeOf(row)) }}
                </span>
              </td>
              <td class="right number">{{ formatMarketCap(marketCapOf(row)) }}</td>
              <td class="right number muted">{{ formatStatusTime(lastUpdatedOf(row)) }}</td>
              <td class="right actions">
                <button type="button" @click="openDetail(row)">详情</button>
                <button type="button" @click="openAiFor(row)">AI</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="sortedCoins.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无匹配币种" :image-size="82" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCoinList, getFearGreed, getSystemStatus } from '../api/coin.js'
import { formatAppDateTime } from '../utils/time.js'

const router = useRouter()

const allCoins = ref([])
const loading = ref(false)
const error = ref('')
const searchKeyword = ref('')
const sortKey = ref('default')
const activeTab = ref('all')
const fng = ref(null)
const systemStatus = ref(null)
let pollTimer = null

const tabs = [
  { label: '热门', value: 'all' },
  { label: '上涨', value: 'gainers' },
  { label: '下跌', value: 'losers' },
  { label: '大市值', value: 'large' }
]

const sortOptions = [
  { label: '默认', value: 'default' },
  { label: '市值', value: 'marketCap' },
  { label: '价格', value: 'price' },
  { label: '涨幅', value: 'changeUp' },
  { label: '跌幅', value: 'changeDown' }
]

const fngValue = computed(() => Number(fng.value?.value ?? 0))

const tabbedCoins = computed(() => {
  if (activeTab.value === 'gainers') return allCoins.value.filter(row => numForSort(changeOf(row)) > 0)
  if (activeTab.value === 'losers') return allCoins.value.filter(row => numForSort(changeOf(row)) < 0)
  if (activeTab.value === 'large') {
    const marketCaps = allCoins.value.map(marketCapOf).filter(v => v != null).sort((a, b) => b - a)
    const threshold = marketCaps[Math.min(9, marketCaps.length - 1)] ?? 0
    return allCoins.value.filter(row => numForSort(marketCapOf(row)) >= threshold)
  }
  return allCoins.value
})

const filteredCoins = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  if (!kw) return tabbedCoins.value
  return tabbedCoins.value.filter(row => {
    return nameOf(row).toLowerCase().includes(kw) || symbolOf(row).toLowerCase().includes(kw)
  })
})

const sortedCoins = computed(() => {
  const list = [...filteredCoins.value]
  if (sortKey.value === 'marketCap') return list.sort((a, b) => numForSort(marketCapOf(b)) - numForSort(marketCapOf(a)))
  if (sortKey.value === 'price') return list.sort((a, b) => numForSort(priceOf(b)) - numForSort(priceOf(a)))
  if (sortKey.value === 'changeUp') return list.sort((a, b) => numForSort(changeOf(b)) - numForSort(changeOf(a)))
  if (sortKey.value === 'changeDown') return list.sort((a, b) => numForSort(changeOf(a)) - numForSort(changeOf(b)))
  return list
})

function safeProp(row, key) { return row ? (row[key] ?? '') : '' }
function valueOf(row, snakeKey, camelKey) {
  return row ? (row[snakeKey] ?? row[camelKey] ?? null) : null
}
function numberOf(row, snakeKey, camelKey) {
  const value = valueOf(row, snakeKey, camelKey)
  return value != null ? Number(value).toLocaleString('en-US') : '--'
}
function timeOf(row, snakeKey, camelKey) { return valueOf(row, snakeKey, camelKey) }
function systemStatusOf(row) {
  return row ? (row.system_status ?? row.systemStatus ?? row.status ?? '--') : '--'
}
function fngClassificationLabel(value) {
  const text = String(value || '').toLowerCase()
  if (text.includes('extreme fear')) return '极度恐惧'
  if (text.includes('fear')) return '恐惧'
  if (text.includes('neutral')) return '中性'
  if (text.includes('extreme greed')) return '极度贪婪'
  if (text.includes('greed')) return '贪婪'
  return value || '--'
}
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
  const v = row?.price_change_percentage_24h ?? row?.price_change_percentage24h ?? row?.priceChangePercentage24h
  return v != null ? Number(v) : null
}
function marketCapOf(row) {
  const v = row?.market_cap ?? row?.marketCap
  return v != null ? Number(v) : null
}
function lastUpdatedOf(row) {
  return row?.last_updated ?? row?.lastUpdated ?? null
}
function coinInitial(row) {
  const sym = symbolOf(row)
  return sym ? sym.slice(0, 2) : (nameOf(row).charAt(0).toUpperCase() || '?')
}
function coinColor(row) {
  const str = nameOf(row) || symbolOf(row) || '?'
  let hash = 0
  for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash)
  return `hsl(${Math.abs(hash) % 360}, 72%, 45%)`
}
function changeDir(row) {
  const v = changeOf(row)
  if (v == null || v === 0) return 'neutral'
  return v > 0 ? 'up' : 'down'
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
function formatMarketCap(cap) {
  if (cap == null) return '--'
  const num = Number(cap)
  if (num >= 1e12) return '$' + (num / 1e12).toFixed(2) + 'T'
  if (num >= 1e9) return '$' + (num / 1e9).toFixed(2) + 'B'
  if (num >= 1e6) return '$' + (num / 1e6).toFixed(2) + 'M'
  if (num >= 1e3) return '$' + (num / 1e3).toFixed(2) + 'K'
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function formatStatusTime(value) {
  return formatAppDateTime(value)
}
function numForSort(value) {
  return value == null || Number.isNaN(Number(value)) ? -Infinity : Number(value)
}
function openDetail(row) {
  const id = coinIdOf(row)
  if (id) router.push('/coin/' + id)
}
function openAiFor(row) {
  router.push({
    name: 'AiAssistant',
    query: {
      q: `${symbolOf(row) || coinIdOf(row)} 最近走势怎么看？请基于项目数据库和历史价格做信息分析，不要给投资建议。`
    }
  })
}
async function fetchData() {
  try {
    loading.value = true
    error.value = ''
    const res = await getCoinList()
    allCoins.value = res.data?.data ?? res.data ?? []
  } catch (err) {
    console.error('Failed to fetch coin list:', err)
    if (allCoins.value.length === 0) error.value = '网络请求失败，请检查后端服务后重试'
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
async function fetchStatus() {
  try {
    const res = await getSystemStatus()
    systemStatus.value = res.data?.data ?? res.data ?? null
  } catch (err) {
    console.error('Failed to fetch system status:', err)
  }
}
function refreshAll() {
  fetchData()
  fetchFng()
  fetchStatus()
}
onMounted(() => {
  refreshAll()
  pollTimer = setInterval(refreshAll, 60000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.market-page {
  width: min(1280px, 100%);
  min-height: calc(100vh - 64px);
  margin: 0 auto;
  padding: 28px 24px 56px;
}

.page-title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.page-title h1 {
  margin: 0;
  color: #111;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 0;
}

.page-title p {
  margin: 8px 0 0;
  color: #707a8a;
  font-size: 14px;
}

button {
  font-family: inherit;
}

.refresh-button {
  min-width: 72px;
  min-height: 36px;
  border: 0;
  border-radius: 18px;
  color: #fff;
  background: #111;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: default;
}

.market-card {
  overflow: hidden;
  border: 1px solid #ebedf0;
  border-radius: 16px;
  background: #fff;
}

.top-tabs {
  display: flex;
  gap: 26px;
  padding: 0 24px;
  border-bottom: 1px solid #ebedf0;
}

.top-tabs button {
  position: relative;
  height: 56px;
  border: 0;
  color: #707a8a;
  background: transparent;
  cursor: pointer;
  font-size: 15px;
  font-weight: 700;
}

.top-tabs button.active {
  color: #111;
}

.top-tabs button.active::after {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 3px;
  border-radius: 999px 999px 0 0;
  background: #111;
  content: "";
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 24px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  width: min(360px, 100%);
}

.search-box span {
  position: absolute;
  left: 14px;
  color: #707a8a;
  font-size: 13px;
  font-weight: 700;
}

.search-box input {
  width: 100%;
  height: 40px;
  border: 1px solid #ebedf0;
  border-radius: 20px;
  padding: 0 16px 0 52px;
  outline: none;
  color: #111;
  background: #f7f8fa;
  font-size: 14px;
}

.search-box input:focus {
  border-color: #111;
  background: #fff;
}

.sort-pills {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.sort-pills button {
  height: 32px;
  border: 1px solid #ebedf0;
  border-radius: 16px;
  padding: 0 12px;
  color: #3f4656;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.sort-pills button.active {
  color: #111;
  border-color: #111;
  background: #f5f5f5;
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin: 0 24px 16px;
  overflow: hidden;
  border: 1px solid #ebedf0;
  border-radius: 12px;
  background: #ebedf0;
}

.status-strip div {
  min-width: 0;
  padding: 13px 14px;
  background: #fff;
}

.status-strip span {
  display: block;
  color: #707a8a;
  font-size: 12px;
  font-weight: 700;
}

.status-strip strong {
  display: block;
  overflow: hidden;
  margin-top: 5px;
  color: #111;
  font-size: 16px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-strip em {
  display: block;
  margin-top: 4px;
  color: #707a8a;
  font-style: normal;
  font-size: 12px;
}

.error-alert {
  margin: 0 24px 16px;
  border-radius: 12px;
}

.skeleton-card {
  padding: 0 24px 24px;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
}

thead {
  background: #fafafa;
}

tr {
  border-top: 1px solid #ebedf0;
}

th,
td {
  height: 60px;
  padding: 0 16px;
  text-align: left;
  white-space: nowrap;
}

th {
  color: #707a8a;
  font-size: 12px;
  font-weight: 700;
}

td {
  color: #111;
  font-size: 14px;
  font-weight: 600;
}

tbody tr:hover {
  background: #fafafa;
}

.right {
  text-align: right;
}

.token-cell {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 10px;
}

.rank {
  width: 24px;
  color: #9aa1ad;
  font-size: 13px;
}

.token-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  flex-shrink: 0;
}

.token-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.token-copy strong {
  color: #111;
  font-size: 14px;
  font-weight: 800;
}

.token-copy small {
  overflow: hidden;
  max-width: 220px;
  color: #707a8a;
  font-size: 12px;
  text-overflow: ellipsis;
}

.number {
  font-variant-numeric: tabular-nums;
}

.number.primary {
  font-weight: 800;
}

.muted {
  color: #707a8a;
  font-size: 13px;
}

.change {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.change.up {
  color: #16a34a;
}

.change.down {
  color: #ef4444;
}

.change.neutral {
  color: #707a8a;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.actions button {
  height: 30px;
  border: 1px solid #ebedf0;
  border-radius: 15px;
  padding: 0 12px;
  color: #111;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}

.actions button:hover {
  border-color: #111;
}

.empty-state {
  padding: 36px 0;
}

@media (max-width: 760px) {
  .market-page {
    padding: 20px 12px 40px;
  }

  .page-title,
  .toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .page-title h1 {
    font-size: 26px;
  }

  .top-tabs {
    gap: 18px;
    overflow-x: auto;
    padding: 0 16px;
  }

  .toolbar {
    padding: 16px;
  }

  .search-box {
    width: 100%;
  }

  .status-strip {
    grid-template-columns: 1fr;
    margin: 0 16px 16px;
  }
}
</style>
