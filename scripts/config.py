import os

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Shanghai")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "CmkDb_2026_R9vQ7mT4zP8sL2nX")
DB_NAME = os.getenv("DB_NAME", "coinmarketdb")

GATEIO_TICKERS_URL = "https://api.gateio.ws/api/v4/spot/tickers"
GATEIO_CANDLESTICKS_URL = "https://api.gateio.ws/api/v4/spot/candlesticks"
FNG_URL = "https://api.alternative.me/fng/"
COINGECKO_CHART_URL = "https://api.coingecko.com/api/v3/coins/{}/market_chart?vs_currency=usd&days={}"

USDT_SUFFIX = "_USDT"
MAX_COINS = 5

WHITELIST = [
    "btc", "eth", "sol", "bnb", "xrp"
]

CG_ID_MAP = {
    "btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin",
    "sol": "solana", "xrp": "ripple", "ada": "cardano",
    "doge": "dogecoin", "dot": "polkadot", "link": "chainlink",
    "ltc": "litecoin", "bch": "bitcoin-cash", "avax": "avalanche-2",
    "matic": "matic-network", "uni": "uniswap", "shib": "shiba-inu",
    "trx": "tron", "etc": "ethereum-classic", "apt": "aptos",
    "near": "near", "op": "optimism", "arb": "arbitrum"
}

HISTORY_DAYS_LIST = [7]
HISTORY_COIN_LIMIT = 5
HISTORY_SOURCE = "gateio"
HISTORY_CANDLE_INTERVAL = "1h"
HISTORY_REQUEST_DELAY = 15
REALTIME_HISTORY_INTERVAL = 300

COLLECT_INTERVAL = 6
FNG_INTERVAL = 15 * 60
HISTORY_INTERVAL = 3600

REQUEST_TIMEOUT = 30
