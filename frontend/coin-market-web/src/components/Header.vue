<template>
  <header class="border-b border-zinc-900 bg-[#07080c]/90 backdrop-blur-md sticky top-0 z-50 px-4 md:px-6 h-16 flex items-center justify-between">
    <div class="flex items-center gap-2 shrink-0" id="header-logo">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-550 via-indigo-600 to-emerald-500 p-[1.5px] shadow-lg shadow-indigo-950/20">
        <div class="w-full h-full bg-[#0d0e14] rounded-[10px] flex items-center justify-center">
          <Coin class="w-5.5 h-5.5 text-indigo-400" />
        </div>
      </div>
      <div class="flex flex-col">
        <span class="font-sans font-black text-white tracking-tight text-sm md:text-base leading-none">
          CoinMarketCap Web3
        </span>
        <span class="text-[9px] text-zinc-500 font-mono tracking-wider uppercase font-bold mt-1">
          MySQL + Redis Board
        </span>
      </div>
    </div>

    <div class="hidden md:flex items-center gap-4 lg:gap-6 overflow-x-auto px-4 max-w-[50%] lg:max-w-[65%] border-x border-zinc-900/60 h-10 scrollbar-hide">
      <span class="text-[10px] text-zinc-500 font-extrabold uppercase shrink-0">实时底池行情:</span>
      <template v-if="tokens.length > 0">
        <div v-for="token in tokens" :key="token.id" class="flex items-center gap-1.5 shrink-0 text-xs">
          <span class="font-bold text-white uppercase">{{ token.symbol }}</span>
          <span class="font-mono text-zinc-300">{{ formatPrice(token.price) }}</span>
          <span class="font-mono text-[10px] font-bold" :class="token.change24h >= 0 ? 'text-emerald-400' : 'text-rose-500'">
            {{ token.change24h >= 0 ? '+' : '' }}{{ token.change24h.toFixed(1) }}%
          </span>
        </div>
      </template>
      <div v-else class="flex items-center gap-1.5 text-zinc-600 text-xs">
        <Refresh class="w-3.5 h-3.5 animate-spin" />
        <span>正在连接 Spring Boot 行情源...</span>
      </div>
    </div>

    <div class="flex items-center gap-3 shrink-0" id="header-interactive-status">
      <div v-if="globalStats" class="flex items-center gap-2 bg-[#0c0e15] border border-zinc-900 px-3 py-1.5 rounded-xl">
        <span class="text-[10px] text-zinc-500 font-bold hidden sm:inline">恐慌与贪婪</span>
        <div class="flex items-center gap-1.5">
          <span class="font-mono text-white font-extrabold bg-[#1a1710] border border-amber-500/20 px-1.5 py-0.5 rounded text-amber-400 text-xs leading-none">
            {{ globalStats.fearAndGreedValue }}
          </span>
          <span class="text-[9.5px] font-black px-2 py-0.5 rounded-full" :class="greedClass">
            {{ greedLabel }}
          </span>
        </div>
      </div>
      <div v-else class="text-[10px] text-zinc-500 font-bold">读取采集数据中...</div>

      <div class="items-center gap-1 text-[10px] bg-indigo-950/20 border border-indigo-900/30 text-indigo-400 px-2.5 py-1.5 rounded-xl font-bold hidden lg:flex">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
        <span>REST-RELIABLE</span>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Coin, Refresh } from '@element-plus/icons-vue'
import type { GlobalStats, Token } from '../types'
import { formatPrice } from '../utils/marketAdapter'

const props = defineProps<{
  globalStats: GlobalStats | null
  tokens: Token[]
}>()

const greedLabel = computed(() => {
  const value = props.globalStats?.fearAndGreedValue ?? 0
  if (value >= 75) return '极度贪婪'
  if (value >= 55) return '贪婪'
  if (value >= 45) return '中性'
  if (value >= 25) return '恐慌'
  return '极度恐慌'
})

const greedClass = computed(() => {
  const value = props.globalStats?.fearAndGreedValue ?? 0
  if (value >= 75) return 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/30'
  if (value >= 55) return 'bg-yellow-950/40 text-yellow-400 border border-yellow-904/30'
  return 'bg-red-950/40 text-red-400 border border-red-900/40'
})
</script>
