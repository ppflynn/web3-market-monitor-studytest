<template>
  <div v-if="points.length === 0" class="h-44 flex items-center justify-center bg-[#07080d] rounded-xl border border-zinc-900">
    <div class="flex items-center gap-2 text-zinc-500 text-xs">
      <span class="w-4 h-4 rounded-full border border-zinc-700 border-t-transparent animate-spin"></span>
      <span>加载 K 线走势序列...</span>
    </div>
  </div>

  <div v-else ref="containerRef" class="token-chart-card bg-[#10121d] border border-zinc-850/80 rounded-2xl p-4.5 flex flex-col gap-3">
    <div class="token-chart-head flex flex-col sm:flex-row gap-3 sm:items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="token-chart-hud flex flex-col">
          <div class="flex items-baseline gap-2">
            <span class="font-mono text-2xl font-black text-white">{{ currentPrice.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 8 }) }}</span>
            <span class="text-zinc-500 font-mono text-xs">{{ tokenSymbol }}/USDT</span>
          </div>
          <div class="flex gap-2 text-[10px] text-zinc-400 font-mono mt-0.5" id="hud-stats-read">
            <span class="text-zinc-500">O:</span><span :class="activeHudPoint.close >= activeHudPoint.open ? 'text-emerald-400' : 'text-rose-400'">{{ fixedPrice(activeHudPoint.open) }}</span>
            <span class="text-zinc-500">H:</span><span class="text-zinc-200">{{ fixedPrice(activeHudPoint.high) }}</span>
            <span class="text-zinc-500">L:</span><span class="text-zinc-200">{{ fixedPrice(activeHudPoint.low) }}</span>
            <span class="text-zinc-500">C:</span><span :class="activeHudPoint.close >= activeHudPoint.open ? 'text-emerald-400' : 'text-rose-400'">{{ fixedPrice(activeHudPoint.close) }}</span>
            <span class="text-zinc-500 hidden md:inline">Vol:</span><span class="text-zinc-300 hidden md:inline">{{ (activeHudPoint.volume / 1000).toFixed(1) }}K</span>
            <span v-if="hoveredPoint" class="text-indigo-400 font-semibold">[ 选中时刻: {{ activeHudPoint.time }} ]</span>
          </div>
        </div>
      </div>

      <div class="chart-control-dock flex items-center gap-2 self-end sm:self-auto text-xs font-semibold">
        <div class="flex bg-[#07080d] p-0.5 rounded-lg border border-zinc-900 font-mono">
          <button
            v-for="res in resolutions"
            :key="res"
            type="button"
            class="px-2 py-1 rounded transition-all text-[11px] cursor-pointer"
            :class="resolution === res ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'"
            @click="resolution = res"
          >
            {{ res }}
          </button>
        </div>

        <div class="flex bg-[#07080d] p-0.5 rounded-lg border border-zinc-900 font-mono">
          <button type="button" class="px-2 py-1 rounded transition-all text-[11px] cursor-pointer" :class="chartType === 'candle' ? 'bg-zinc-800 text-white' : 'text-zinc-500'" @click="chartType = 'candle'">蜡烛</button>
          <button type="button" class="px-2 py-1 rounded transition-all text-[11px] cursor-pointer" :class="chartType === 'line' ? 'bg-zinc-800 text-white' : 'text-zinc-500'" @click="chartType = 'line'">折线</button>
        </div>

        <button
          type="button"
          class="p-1.5 rounded-lg border transition-all cursor-pointer"
          :class="showEma ? 'bg-indigo-950/40 border-indigo-900/40 text-indigo-400' : 'bg-zinc-900/30 border-zinc-900 text-zinc-500'"
          title="Toggle EMA 12 Trend Indicator Line"
          @click="showEma = !showEma"
        >
          <DataLine class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <div class="relative border border-zinc-900 bg-[#07080d] rounded-xl overflow-hidden select-none">
      <div class="absolute top-2 right-2 flex flex-col items-end text-[9px] font-mono text-zinc-650 pointer-events-none gap-0.5">
        <span class="bg-zinc-950/80 px-1 py-0.5 rounded">MAX: ${{ maxPrice.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
        <span class="bg-zinc-950/80 px-1 py-0.5 rounded">MIN: ${{ minPrice.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
      </div>

      <svg width="100%" :height="dimensions.height" class="cursor-crosshair overflow-visible" @mousemove="handleMouseMove" @mouseleave="hoveredPoint = null">
        <line :x1="paddingX" :y1="paddingY" :x2="dimensions.width - paddingX" :y2="paddingY" stroke="#12131b" stroke-width="1" stroke-dasharray="3,3" />
        <line :x1="paddingX" :y1="paddingY + drawingHeight * 0.25" :x2="dimensions.width - paddingX" :y2="paddingY + drawingHeight * 0.25" stroke="#12131b" stroke-width="1" stroke-dasharray="3,3" />
        <line :x1="paddingX" :y1="paddingY + drawingHeight * 0.5" :x2="dimensions.width - paddingX" :y2="paddingY + drawingHeight * 0.5" stroke="#12131b" stroke-width="1" stroke-dasharray="3,3" />
        <line :x1="paddingX" :y1="paddingY + drawingHeight * 0.75" :x2="dimensions.width - paddingX" :y2="paddingY + drawingHeight * 0.75" stroke="#12131b" stroke-width="1" stroke-dasharray="3,3" />
        <line :x1="paddingX" :y1="paddingY + drawingHeight" :x2="dimensions.width - paddingX" :y2="paddingY + drawingHeight" stroke="#171926" stroke-width="1" />

        <rect
          v-for="(pt, i) in projectedPoints"
          :key="`vol-${i}`"
          :x="pt.x - 2"
          :y="dimensions.height - paddingY - pt.volumeHeight"
          width="4"
          :height="pt.volumeHeight"
          :class="pt.p.close >= pt.p.open ? 'fill-[#00e676]/15' : 'fill-[#ff3860]/15'"
        />

        <template v-if="chartType === 'line'">
          <path :d="areaPath" :fill="`url(#lineGrad-${priceChange24h >= 0 ? 'up' : 'down'})`" class="opacity-15 transition-all duration-300" />
          <path :d="linePath" fill="none" :class="`${priceChange24h >= 0 ? 'stroke-[#00e676]' : 'stroke-[#ff3860]'} transition-all duration-300`" stroke-width="2" stroke-linecap="round" />
        </template>

        <template v-if="chartType === 'candle'">
          <g v-for="(pt, i) in projectedPoints" :key="`candle-${i}`">
            <line :x1="pt.x" :y1="pt.yHigh" :x2="pt.x" :y2="pt.yLow" :class="pt.p.close >= pt.p.open ? 'stroke-[#00e676]' : 'stroke-[#ff3860]'" stroke-width="1.5" />
            <rect
              :x="pt.x - candleWidth / 2"
              :y="Math.min(pt.yOpen, pt.yClose)"
              :width="candleWidth"
              :height="Math.max(1, Math.abs(pt.yOpen - pt.yClose))"
              :class="pt.p.close >= pt.p.open ? 'fill-[#00e676] stroke-[#00e676]' : 'fill-[#ff3860] stroke-[#ff3860]'"
            />
          </g>
        </template>

        <path v-if="showEma && emaLinePath" :d="emaLinePath" fill="none" stroke="#ebbc5e" stroke-width="1.25" stroke-dasharray="1,1" class="opacity-75" />

        <g v-if="hoveredPoint">
          <line :x1="hoverX" :y1="paddingY" :x2="hoverX" :y2="dimensions.height - paddingY" stroke="#585f80" stroke-width="1" stroke-dasharray="4,4" />
          <circle :cx="hoverX" :cy="projectY(hoveredPoint.close)" r="4.5" fill="#ffffff" stroke="#4361ee" stroke-width="2.5" />
        </g>

        <text
          v-for="(pt, i) in labelPoints"
          :key="`lbl-${i}`"
          :x="pt.x"
          :y="dimensions.height - 4"
          text-anchor="middle"
          class="fill-zinc-650 font-mono text-[9px] font-semibold"
        >
          {{ pt.p.time }}
        </text>

        <defs>
          <linearGradient id="lineGrad-up" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#00e676" stop-opacity="0.8" />
            <stop offset="100%" stop-color="#00e676" stop-opacity="0.0" />
          </linearGradient>
          <linearGradient id="lineGrad-down" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#ff3860" stop-opacity="0.8" />
            <stop offset="100%" stop-color="#ff3860" stop-opacity="0.0" />
          </linearGradient>
        </defs>
      </svg>
    </div>

    <div class="flex justify-between items-center text-[10px] text-zinc-600 bg-[#07080d] px-3.5 py-2.5 rounded-xl border border-zinc-950 font-medium">
      <span class="flex items-center gap-1.5"><View class="w-3.5 h-3.5 text-zinc-500" /> 支持鼠标指针悬停，查看分点 K 线价格多指标细节</span>
      <span v-if="showEma" class="flex items-center gap-1 text-[#ebbc5e]"><TrendCharts class="w-3.5 h-3.5" /> EMA 12 均线波动带上线</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { DataLine, TrendCharts, View } from '@element-plus/icons-vue'
import type { ChartPoint } from '../types'

type Resolution = '1H' | '24H' | '7D' | '30D'
type ChartType = 'candle' | 'line'

const props = defineProps<{
  tokenId: string
  tokenSymbol: string
  currentPrice: number
  priceChange24h: number
}>()

const resolutions: Resolution[] = ['1H', '24H', '7D', '30D']
const resolution = ref<Resolution>('24H')
const chartType = ref<ChartType>('candle')
const showEma = ref(true)
const points = ref<ChartPoint[]>([])
const hoveredPoint = ref<ChartPoint | null>(null)
const containerRef = ref<HTMLElement | null>(null)
const dimensions = ref({ width: 680, height: 280 })
let resizeObserver: ResizeObserver | null = null

const paddingX = 40
const paddingY = 20
const maxPrice = computed(() => Math.max(...points.value.map((p) => p.high)) * 1.002)
const minPrice = computed(() => Math.min(...points.value.map((p) => p.low)) * 0.998)
const priceRange = computed(() => maxPrice.value - minPrice.value || 1)
const maxVolume = computed(() => Math.max(...points.value.map((p) => p.volume)) || 1)
const drawingWidth = computed(() => dimensions.value.width - paddingX * 2)
const drawingHeight = computed(() => dimensions.value.height - paddingY * 2)
const activeHudPoint = computed(() => hoveredPoint.value || points.value[points.value.length - 1])
const candleWidth = computed(() => Math.max(2, Math.floor(drawingWidth.value / points.value.length) * 0.75))

const projectedPoints = computed(() => points.value.map((p, i) => ({
  x: projectX(i),
  yOpen: projectY(p.open),
  yClose: projectY(p.close),
  yHigh: projectY(p.high),
  yLow: projectY(p.low),
  volumeHeight: (p.volume / maxVolume.value) * 45,
  p,
})))

const linePath = computed(() => {
  if (!projectedPoints.value.length) return ''
  return `M ${projectedPoints.value[0].x} ${projectedPoints.value[0].yClose} ${projectedPoints.value.slice(1).map((p) => `L ${p.x} ${p.yClose}`).join(' ')}`
})

const areaPath = computed(() => {
  if (!projectedPoints.value.length) return ''
  const last = projectedPoints.value[projectedPoints.value.length - 1]
  const first = projectedPoints.value[0]
  return `${linePath.value} L ${last.x} ${dimensions.value.height - paddingY} L ${first.x} ${dimensions.value.height - paddingY} Z`
})

const emaLinePath = computed(() => {
  const ema = calculateEMA(12).map((val, i) => ({ x: projectX(i), y: projectY(val) }))
  if (!ema.length) return ''
  return `M ${ema[0].x} ${ema[0].y} ${ema.slice(1).map((p) => `L ${p.x} ${p.y}`).join(' ')}`
})

const hoverX = computed(() => {
  if (!hoveredPoint.value) return 0
  return projectX(points.value.indexOf(hoveredPoint.value))
})

const labelPoints = computed(() => {
  const step = Math.max(2, Math.floor(points.value.length / 5))
  return projectedPoints.value.filter((_, idx) => idx % step === 0)
})

function projectX(index: number) {
  if (points.value.length <= 1) return paddingX
  return paddingX + (index / (points.value.length - 1)) * drawingWidth.value
}

function projectY(price: number) {
  const fraction = (price - minPrice.value) / priceRange.value
  return paddingY + drawingHeight.value - fraction * drawingHeight.value
}

function fixedPrice(price: number) {
  return price.toFixed(price > 100 ? 2 : 4)
}

function calculateEMA(period: number) {
  const emaValue: number[] = []
  if (!points.value.length) return emaValue
  const k = 2 / (period + 1)
  let currentEma = points.value[0].close
  emaValue.push(currentEma)
  for (let i = 1; i < points.value.length; i += 1) {
    currentEma = points.value[i].close * k + currentEma * (1 - k)
    emaValue.push(currentEma)
  }
  return emaValue
}

function handleMouseMove(event: MouseEvent) {
  const rect = (event.currentTarget as SVGSVGElement).getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  let minDiff = Infinity
  let closestIndex = 0
  projectedPoints.value.forEach((point, index) => {
    const diff = Math.abs(point.x - mouseX)
    if (diff < minDiff) {
      minDiff = diff
      closestIndex = index
    }
  })
  hoveredPoint.value = minDiff < 45 ? points.value[closestIndex] : null
}

async function fetchChartData() {
  const days = resolution.value === '30D' ? 30 : resolution.value === '7D' ? 7 : 1
  try {
    const response = await fetch(`/api/coins/${props.tokenId}/history?days=${days}`)
    const data = await response.json()
    const rows = Array.isArray(data?.data) ? data.data : Array.isArray(data) ? data : []
    points.value = buildChartPoints(rows)
  } catch (error) {
    console.error(error)
    points.value = buildFallbackPoints()
  }
}

function buildChartPoints(rows: any[]): ChartPoint[] {
  const usefulRows = rows.length ? rows : buildFallbackPoints()
  return usefulRows.map((row: any, index: number) => {
    if ('open' in row && 'close' in row) return row as ChartPoint
    const close = Number(row.price ?? row.close ?? props.currentPrice)
    const prev = index > 0 ? Number(usefulRows[index - 1].price ?? usefulRows[index - 1].close ?? close) : close * (1 - props.priceChange24h / 100 / 12)
    const spread = Math.max(Math.abs(close - prev), close * 0.0015)
    const timestamp = String(row.timestamp ?? row.date ?? row.time ?? index)
    return {
      time: formatPointTime(timestamp, index),
      open: prev,
      high: Math.max(close, prev) + spread * 0.45,
      low: Math.min(close, prev) - spread * 0.45,
      close,
      volume: Math.max(900, close * (1200 + index * 37)),
    }
  })
}

function buildFallbackPoints(): ChartPoint[] {
  const total = resolution.value === '30D' ? 44 : resolution.value === '7D' ? 34 : 28
  const base = props.currentPrice || 1
  return Array.from({ length: total }, (_, index) => {
    const drift = props.priceChange24h / 100
    const wave = Math.sin(index / 3) * 0.012 + Math.cos(index / 5) * 0.006
    const close = base * (1 + drift * ((index + 1) / total - 1) + wave)
    const open = index === 0 ? close * (1 - wave / 2) : base * (1 + drift * (index / total - 1) + Math.sin((index - 1) / 3) * 0.012)
    const spread = Math.max(Math.abs(close - open), base * 0.002)
    return {
      time: `${String(index + 1).padStart(2, '0')}:00`,
      open,
      high: Math.max(open, close) + spread * 0.8,
      low: Math.min(open, close) - spread * 0.8,
      close,
      volume: 12000 + index * 600 + Math.abs(wave) * 100000,
    }
  })
}

function formatPointTime(value: string, index: number) {
  const date = new Date(value)
  if (!Number.isNaN(date.getTime())) {
    return resolution.value === '1H' || resolution.value === '24H'
      ? date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      : date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }
  return String(index + 1)
}

function handleResize() {
  if (!containerRef.value) return
  dimensions.value = { width: Math.max(containerRef.value.clientWidth - 36, 320), height: 280 }
}

watch(() => [props.tokenId, resolution.value], fetchChartData)
watch(() => props.currentPrice, (price) => {
  if (!points.value.length) return
  const copy = [...points.value]
  const last = { ...copy[copy.length - 1] }
  last.close = price
  last.high = Math.max(last.high, price)
  last.low = Math.min(last.low, price)
  copy[copy.length - 1] = last
  points.value = copy
})

onMounted(async () => {
  await fetchChartData()
  await nextTick()
  handleResize()
  window.addEventListener('resize', handleResize)
  resizeObserver = new ResizeObserver(handleResize)
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
})
</script>

<style scoped>
.token-chart-card {
  position: relative;
}

.token-chart-head {
  align-items: flex-start;
}

.token-chart-hud {
  min-width: 0;
}

.chart-control-dock {
  position: sticky;
  top: 0;
  z-index: 3;
  flex-shrink: 0;
  min-height: 34px;
  border-radius: 12px;
}

@media (min-width: 640px) {
  .token-chart-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .chart-control-dock {
    justify-self: end;
  }
}

@media (max-width: 639px) {
  .token-chart-card {
    padding: 14px;
  }

  .token-chart-head {
    gap: 12px;
  }

  .token-chart-hud :global(.text-2xl) {
    font-size: 1.2rem;
    line-height: 1.6rem;
  }

  #hud-stats-read {
    flex-wrap: wrap;
    gap: 5px 8px;
    max-width: 100%;
  }

  .chart-control-dock {
    width: 100%;
    justify-content: space-between;
    align-self: stretch;
    overflow-x: auto;
    padding: 4px;
    background: rgba(7, 8, 13, 0.82);
    border: 1px solid rgba(24, 24, 27, 0.95);
    backdrop-filter: blur(10px);
  }

  .chart-control-dock > div {
    flex-shrink: 0;
  }

  .chart-control-dock button {
    min-width: 36px;
  }
}
</style>
