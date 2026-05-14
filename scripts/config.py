import os


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "coinmarketdb")

GATEIO_TICKERS_URL = "https://api.gateio.ws/api/v4/spot/tickers"
FNG_URL = "https://api.alternative.me/fng/"
COINGECKO_CHART_URL = "https://api.coingecko.com/api/v3/coins/{}/market_chart?vs_currency=usd&days={}"

USDT_SUFFIX = "_USDT"
MAX_COINS = 100

WHITELIST = [
    "btc", "eth", "bnb", "sol", "xrp", "ada", "doge", "dot", "link",
    "ltc", "bch", "avax", "matic", "uni", "shib", "trx", "etc",
    "apt", "near", "op", "arb"
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
HISTORY_REQUEST_DELAY = 15

COLLECT_INTERVAL = 60
FNG_INTERVAL = 15 * 60
HISTORY_INTERVAL = 3600

REQUEST_TIMEOUT = 30
