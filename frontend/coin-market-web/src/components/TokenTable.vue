<template>
  <div class="bg-[#0c0e16] border border-zinc-800/85 rounded-2xl p-5 shadow-2xl flex flex-col gap-4">
    <div class="flex flex-col md:flex-row gap-3.5 items-stretch md:items-center justify-between">
      <div class="flex items-center gap-2">
        <Coin class="text-indigo-400 w-4.5 h-4.5" />
        <span class="text-xs text-white font-bold">主力行情速核 (MySQL 稳定数据源)</span>
      </div>

      <div class="relative flex-1 max-w-md">
        <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-zinc-500">
          <Search class="w-4 h-4" />
        </span>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="在 BTC、ETH、SOL、BNB、XRP 中快速索引..."
          class="w-full bg-[#07080d] border border-zinc-900 focus:border-indigo-650 rounded-xl py-2 pl-10 pr-4 text-xs font-semibold placeholder-zinc-500 focus:outline-none transition-all text-white"
        />
      </div>
    </div>

    <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide border-b border-zinc-900/60">
      <button
        v-for="chain in chains"
        :key="chain.id"
        type="button"
        class="px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap cursor-pointer transition-all border"
        :class="chainFilter === chain.id ? 'bg-white text-black border-white' : 'bg-zinc-900/40 text-zinc-400 border-zinc-905 hover:border-zinc-800'"
        @click="chainFilter = chain.id"
      >
        {{ chain.name }}
      </button>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse min-w-[700px]">
        <thead>
          <tr class="border-b border-zinc-900 font-bold text-zinc-500 text-[11px] uppercase tracking-wider h-10 select-none">
            <th class="w-10 text-center">#</th>
            <th class="px-3 cursor-pointer hover:text-white transition-all" @click="requestSort('name')">主链币种</th>
            <th class="px-2 text-right cursor-pointer hover:text-white transition-all" @click="requestSort('price')">现货价格 (USDT)</th>
            <th class="px-2 text-right cursor-pointer hover:text-white transition-all" @click="requestSort('change24h')">24H 涨跌幅</th>
            <th class="px-2 text-right cursor-pointer hover:text-white transition-all" @click="requestSort('volume24h')">24H 交易额</th>
            <th class="px-2 text-right cursor-pointer hover:text-white transition-all" @click="requestSort('liquidity')">流动支撑 (Dex Pool)</th>
            <th class="px-2 text-right cursor-pointer hover:text-white transition-all" @click="requestSort('marketCap')">流通市值 (Spring REST)</th>
            <th class="px-2 text-center cursor-pointer hover:text-white transition-all" @click="requestSort('securityScore')">智能风控审计</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-950/60 text-xs text-zinc-305">
          <tr
            v-for="(token, index) in sortedTokens"
            :key="token.id"
            class="h-14 hover:bg-[#121422]/60 cursor-pointer transition-all"
            :class="selectedTokenId === token.id ? 'bg-indigo-950/15 border-l-2 border-indigo-500' : ''"
            @click="$emit('select-token', token)"
          >
            <td class="text-center font-mono text-zinc-500 font-bold">{{ index + 1 }}</td>
            <td class="px-3">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr p-[1.5px] shrink-0 shadow-lg" :class="token.logoColor">
                  <div class="w-full h-full bg-zinc-950 rounded-[9px] flex items-center justify-center font-sans font-black text-[12px] text-white">
                    {{ token.symbol }}
                  </div>
                </div>
                <div class="flex flex-col">
                  <div class="flex items-center gap-1.5">
                    <span class="font-sans font-bold text-white text-[13px] leading-none">{{ token.symbol }}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase" :class="getChainBadge(token.chain)">
                      {{ token.chain }}
                    </span>
                  </div>
                  <span class="text-zinc-500 text-[10.5px] font-semibold mt-0.5">{{ token.name }}</span>
                </div>
              </div>
            </td>
            <td class="px-2 text-right font-mono font-bold text-zinc-100">{{ formatPrice(token.price) }}</td>
            <td class="px-2 text-right font-mono font-bold" :class="token.change24h >= 0 ? 'text-[#00e676]' : 'text-[#ff3860]'">
              <span class="flex items-center justify-end gap-0.5">
                <ArrowUp v-if="token.change24h >= 0" class="w-3.5 h-3.5" />
                <ArrowDown v-else class="w-3.5 h-3.5" />
                {{ token.change24h >= 0 ? '+' : '' }}{{ token.change24h.toFixed(2) }}%
              </span>
            </td>
            <td class="px-2 text-right font-mono text-zinc-400 font-medium">{{ formatCompact(token.volume24h) }}</td>
            <td class="px-2 text-right font-mono text-zinc-400 font-medium">{{ formatCompact(token.liquidity) }}</td>
            <td class="px-2 text-right font-mono text-zinc-200 font-bold">{{ formatCompact(token.marketCap) }}</td>
            <td class="px-2">
              <div class="flex justify-center items-center">
                <div class="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-emerald-950/20 text-[#00e575] border border-emerald-900/30">
                  <CircleCheck class="w-3.5 h-3.5" />
                  <span class="font-mono">{{ token.securityScore }}分</span>
                  <span class="text-[9px] font-sans text-emerald-400/80">(已开源)</span>
                </div>
              </div>
            </td>
          </tr>
          <tr v-if="sortedTokens.length === 0">
            <td colspan="8" class="text-center py-12 text-zinc-500 font-medium">未检索到任何匹配该关键字的主力代币。</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, ArrowUp, CircleCheck, Coin, Search } from '@element-plus/icons-vue'
import type { ChainId, Token } from '../types'
import { formatCompact, formatPrice } from '../utils/marketAdapter'

const props = defineProps<{
  tokens: Token[]
  selectedTokenId: string | null
}>()

defineEmits<{
  (event: 'select-token', token: Token): void
}>()

type SortField = keyof Token
type ChainFilter = ChainId | 'all'

const chainFilter = ref<ChainFilter>('all')
const searchQuery = ref('')
const sortField = ref<SortField>('marketCap')
const sortAsc = ref(false)

const chains: { id: ChainFilter; name: string }[] = [
  { id: 'all', name: '全部公网资产' },
  { id: 'bitcoin', name: 'Bitcoin' },
  { id: 'ethereum', name: 'Ethereum' },
  { id: 'solana', name: 'Solana' },
  { id: 'bsc', name: 'BNB Chain' },
  { id: 'ripple', name: 'Ripple' },
]

const sortedTokens = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const filtered = props.tokens.filter((token) => {
    if (chainFilter.value !== 'all' && token.chain !== chainFilter.value) return false
    if (!query) return true
    return token.symbol.toLowerCase().includes(query) || token.name.toLowerCase().includes(query) || token.address.toLowerCase().includes(query)
  })

  return [...filtered].sort((a, b) => {
    let aVal = a[sortField.value] as any
    let bVal = b[sortField.value] as any
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase()
      bVal = String(bVal).toLowerCase()
    }
    if (aVal < bVal) return sortAsc.value ? -1 : 1
    if (aVal > bVal) return sortAsc.value ? 1 : -1
    return 0
  })
})

function requestSort(field: SortField) {
  if (sortField.value === field) {
    sortAsc.value = !sortAsc.value
  } else {
    sortField.value = field
    sortAsc.value = false
  }
}

function getChainBadge(chain: string) {
  switch (chain) {
    case 'bitcoin': return 'bg-amber-950/40 text-amber-500 border border-amber-900/40'
    case 'ethereum': return 'bg-blue-900/20 text-blue-400 border border-blue-900/30'
    case 'solana': return 'bg-purple-900/25 text-purple-400 border border-purple-900/20'
    case 'bsc': return 'bg-yellow-950/30 text-yellow-500 border border-yellow-905/30'
    case 'ripple': return 'bg-sky-950/30 text-sky-400 border border-sky-900/30'
    default: return 'bg-zinc-900 text-zinc-400 border border-zinc-800'
  }
}
</script>
