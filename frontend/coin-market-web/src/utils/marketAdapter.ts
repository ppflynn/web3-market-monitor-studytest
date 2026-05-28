import type { ChainId, GlobalStats, Token } from '../types'

const chainBySymbol: Record<string, ChainId> = {
  BTC: 'bitcoin',
  ETH: 'ethereum',
  SOL: 'solana',
  BNB: 'bsc',
  XRP: 'ripple',
}

const logoByChain: Record<ChainId, string> = {
  bitcoin: 'from-amber-550 via-orange-500 to-yellow-300',
  ethereum: 'from-blue-500 via-indigo-500 to-sky-400',
  solana: 'from-purple-500 via-fuchsia-500 to-emerald-400',
  bsc: 'from-yellow-500 via-amber-500 to-orange-400',
  ripple: 'from-sky-500 via-blue-500 to-zinc-300',
}

const addressByChain: Record<ChainId, string> = {
  bitcoin: 'bc1qcmcweb3marketwatch0000000000000000000btc',
  ethereum: '0x0000000000000000000000000000000000000eth',
  solana: 'So11111111111111111111111111111111111111112',
  bsc: '0x0000000000000000000000000000000000000bnb',
  ripple: 'rCMCWeb3MarketBoardXRP000000000000000000',
}

function toNumber(value: unknown, fallback = 0) {
  const num = Number(value)
  return Number.isFinite(num) ? num : fallback
}

function pick<T>(row: Record<string, any>, snake: string, camel: string, fallback: T): T {
  return (row?.[snake] ?? row?.[camel] ?? fallback) as T
}

function hashText(text: string) {
  let hash = 0
  for (let i = 0; i < text.length; i += 1) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash)
}

export function normalizeCoin(row: Record<string, any>, index = 0): Token {
  const symbol = String(row?.symbol ?? 'N/A').toUpperCase()
  const id = String(pick(row, 'coin_id', 'coinId', symbol.toLowerCase())).toLowerCase()
  const chain = chainBySymbol[symbol] ?? (['bitcoin', 'ethereum', 'solana', 'bsc', 'ripple'][index % 5] as ChainId)
  const price = toNumber(pick(row, 'current_price', 'currentPrice', 0))
  const change24h = toNumber(
    row?.price_change_percentage_24h ?? row?.priceChangePercentage24h ?? row?.price_change_percentage24h,
  )
  const marketCap = toNumber(pick(row, 'market_cap', 'marketCap', price * 100000000))
  const seed = hashText(`${id}-${symbol}`)
  const volume24h = Math.max(marketCap * (0.025 + (seed % 9) / 100), price * 100000)
  const liquidity = Math.max(volume24h * (0.22 + (seed % 7) / 100), price * 25000)

  return {
    id,
    name: String(row?.name ?? symbol),
    symbol,
    logoColor: logoByChain[chain],
    chain,
    price,
    change2h: change24h / 12,
    change24h,
    volume24h,
    liquidity,
    marketCap,
    address: addressByChain[chain],
    creator: 'CoinMarketCap Web3 Collector',
    securityScore: 88 + (seed % 11),
    createdTime: String(row?.last_updated ?? row?.lastUpdated ?? '2026-05-25 00:00'),
    holders: 24000 + (seed % 860000),
    securityFlags: {
      isHoneypot: false,
      buyTax: 0,
      sellTax: 0,
      isMintable: false,
      ownerPrivilegeRenounced: true,
      contractVerified: true,
      isProxy: false,
      liquidityLockedPercent: 100,
    },
  }
}

export function buildGlobalStats(tokens: Token[], status: Record<string, any> | null, fearGreed: Record<string, any> | null): GlobalStats {
  const totalMarketCap = tokens.reduce((sum, token) => sum + token.marketCap, 0)
  const volume24h = tokens.reduce((sum, token) => sum + token.volume24h, 0)
  const btcCap = tokens.find((token) => token.symbol === 'BTC')?.marketCap ?? 0
  const fngValue = toNumber(
    fearGreed?.value ?? status?.fearGreedValue ?? status?.fear_greed_value ?? status?.fearGreed ?? 68,
    68,
  )

  return {
    totalMarketCap,
    volume24h,
    btcDominance: totalMarketCap ? (btcCap / totalMarketCap) * 100 : 0,
    activeWallets: tokens.reduce((sum, token) => sum + token.holders, 0),
    fearAndGreedValue: fngValue,
    fearAndGreedClassification: classifyFearGreed(fngValue),
    coinCount: toNumber(status?.coin_count ?? status?.coinCount, tokens.length),
    pricePointCount: toNumber(status?.price_point_count ?? status?.pricePointCount, 0),
    latestPriceUpdate: status?.latest_price_update ?? status?.latestPriceUpdate ?? null,
  }
}

export function classifyFearGreed(value: number): GlobalStats['fearAndGreedClassification'] {
  if (value >= 75) return 'Extreme Greed'
  if (value >= 55) return 'Greed'
  if (value >= 45) return 'Neutral'
  if (value >= 25) return 'Fear'
  return 'Extreme Fear'
}

export function formatCompact(num: number) {
  if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`
  if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`
  if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`
  if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`
  return `$${num.toLocaleString('zh-CN')}`
}

export function formatPrice(price: number) {
  if (price >= 1000) {
    return `$${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }
  if (price >= 1) return `$${price.toFixed(3)}`
  return `$${price.toFixed(6)}`
}
