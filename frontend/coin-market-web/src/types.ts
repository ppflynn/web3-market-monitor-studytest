export type ChainId = 'bitcoin' | 'ethereum' | 'solana' | 'bsc' | 'ripple'

export interface Token {
  id: string
  name: string
  symbol: string
  logoColor: string
  chain: ChainId
  price: number
  change2h: number
  change24h: number
  volume24h: number
  liquidity: number
  marketCap: number
  address: string
  creator: string
  securityScore: number
  createdTime: string
  holders: number
  securityFlags: {
    isHoneypot: boolean
    buyTax: number
    sellTax: number
    isMintable: boolean
    ownerPrivilegeRenounced: boolean
    contractVerified: boolean
    isProxy: boolean
    liquidityLockedPercent: number
  }
}

export interface GlobalStats {
  totalMarketCap: number
  volume24h: number
  btcDominance: number
  activeWallets: number
  fearAndGreedValue: number
  fearAndGreedClassification: 'Extreme Fear' | 'Fear' | 'Neutral' | 'Greed' | 'Extreme Greed'
  coinCount?: number
  pricePointCount?: number
  latestPriceUpdate?: string | null
}

export interface ChartPoint {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'model'
  text: string
  timestamp: string
  usedTools?: string[]
  retrievedFiles?: string[]
}

export interface ScraperStatus {
  active: boolean
  lastScrapedAt: string
  scrapedCount: number
  progress: number
  logs: string[]
}

export interface FastAPIStatus {
  health: string
  lastModelInference: string
  activePromptsCount: number
  cachedAnalyses: number
  ragIndexFilesCount: number
}
