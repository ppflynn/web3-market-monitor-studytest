"""
Cryptocurrency Data Collector
Fetches real-time data from Gate.io, Fear & Greed Index, and CoinGecko historical
data, then stores everything into MySQL. Java Spring Boot reads from MySQL only.
"""
import pymysql
import requests
import time
import logging
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("collector")
APP_TZ = ZoneInfo(config.APP_TIMEZONE)


def app_now():
    return datetime.now(APP_TZ).replace(tzinfo=None)


def from_unix_ms(timestamp_ms):
    return datetime.fromtimestamp(timestamp_ms / 1000, APP_TZ).replace(tzinfo=None)


def from_unix_seconds(timestamp):
    return datetime.fromtimestamp(timestamp, APP_TZ).replace(tzinfo=None)


class Database:
    def __init__(self):
        self.conn = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset="utf8mb4",
            autocommit=False
        )
        self.ensure_tables()

    def ensure_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS coins (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    coin_id VARCHAR(50) UNIQUE NOT NULL,
                    symbol VARCHAR(20),
                    name VARCHAR(100),
                    current_price DOUBLE,
                    market_cap DOUBLE DEFAULT 0,
                    price_change_percentage_24h DOUBLE,
                    last_updated DATETIME
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS price_points (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    coin_id VARCHAR(50) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    price DOUBLE,
                    INDEX idx_coin_id_timestamp (coin_id, timestamp),
                    UNIQUE KEY uk_coin_id_timestamp (coin_id, timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            self.ensure_price_points_unique_index(cur)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fear_greed (
                    id INT PRIMARY KEY DEFAULT 1,
                    value INT DEFAULT 50,
                    classification VARCHAR(50) DEFAULT 'Neutral',
                    unix_timestamp BIGINT DEFAULT 0,
                    updated_at DATETIME
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            self.conn.commit()
        log.info("Database tables verified")

    def ensure_price_points_unique_index(self, cur):
        cur.execute("""
            SELECT COUNT(1)
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'price_points'
              AND index_name = 'uk_coin_id_timestamp'
        """)
        exists = cur.fetchone()[0]
        if exists:
            return

        cur.execute("""
            DELETE p1 FROM price_points p1
            INNER JOIN price_points p2
              ON p1.coin_id = p2.coin_id
             AND p1.timestamp = p2.timestamp
             AND p1.id > p2.id
        """)
        cur.execute("ALTER TABLE price_points ADD UNIQUE KEY uk_coin_id_timestamp (coin_id, timestamp)")
        log.info("Added unique index uk_coin_id_timestamp to price_points")

    def upsert_coin(self, coin_id, symbol, name, price, change_pct):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM coins WHERE coin_id = %s", (coin_id,))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """UPDATE coins SET symbol=%s, name=%s, current_price=%s,
                       market_cap=0, price_change_percentage_24h=%s,
                       last_updated=%s
                       WHERE coin_id=%s""",
                    (symbol, name, price, change_pct, app_now(), coin_id)
                )
            else:
                cur.execute(
                    """INSERT INTO coins (coin_id, symbol, name, current_price,
                       market_cap, price_change_percentage_24h, last_updated)
                       VALUES (%s, %s, %s, %s, 0, %s, %s)""",
                    (coin_id, symbol, name, price, change_pct, app_now())
                )
        self.conn.commit()

    def upsert_price_point(self, coin_id, timestamp, price):
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO price_points (coin_id, timestamp, price)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE price=VALUES(price)""",
                (coin_id, timestamp, price)
            )
        self.conn.commit()

    def batch_replace_price_points(self, coin_id, points):
        with self.conn.cursor() as cur:
            for ts, price in points:
                cur.execute(
                    """INSERT INTO price_points (coin_id, timestamp, price)
                       VALUES (%s, %s, %s)
                       ON DUPLICATE KEY UPDATE price=VALUES(price)""",
                    (coin_id, ts, price)
                )
        self.conn.commit()

    def delete_price_points_window(self, coin_id, days):
        since = app_now() - timedelta(days=days)
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM price_points WHERE coin_id=%s AND timestamp >= %s",
                (coin_id, since)
            )
        self.conn.commit()

    def upsert_fear_greed(self, value, classification, unix_ts):
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO fear_greed (id, value, classification, unix_timestamp, updated_at)
                   VALUES (1, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   value=VALUES(value), classification=VALUES(classification),
                   unix_timestamp=VALUES(unix_timestamp), updated_at=VALUES(updated_at)""",
                (value, classification, unix_ts, app_now())
            )
        self.conn.commit()

    def close(self):
        self.conn.close()


def fetch_gateio_tickers():
    try:
        resp = requests.get(config.GATEIO_TICKERS_URL, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.error("Failed to fetch Gate.io tickers: %s", e)
        return None


def fetch_fear_greed():
    try:
        resp = requests.get(config.FNG_URL, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            return None
        item = data[0]
        return {
            "value": int(item.get("value", 50)),
            "classification": item.get("value_classification", "Neutral"),
            "timestamp": int(item.get("timestamp", 0))
        }
    except Exception as e:
        log.error("Failed to fetch Fear & Greed: %s", e)
        return None


def looks_rate_limited(resp):
    if resp.status_code in (403, 429):
        return True
    retry_after = resp.headers.get("Retry-After")
    if retry_after:
        return True
    body = resp.text.lower()
    return "rate limit" in body or "too many requests" in body


def fetch_coingecko_history(coin_id, cg_id, days):
    url = config.COINGECKO_CHART_URL.format(cg_id, days)
    try:
        log.info("Requesting history price: coin_id=%s, cg_id=%s, days=%s", coin_id, cg_id, days)
        resp = requests.get(url, timeout=config.REQUEST_TIMEOUT)
        log.info("CoinGecko history HTTP status: coin_id=%s, status_code=%s", coin_id, resp.status_code)
        if resp.status_code != 200:
            log.error(
                "CoinGecko history request failed: coin_id=%s, cg_id=%s, days=%s, status_code=%s, response=%s",
                coin_id,
                cg_id,
                days,
                resp.status_code,
                resp.text[:500]
            )
            if looks_rate_limited(resp):
                log.warning("\u53ef\u80fd\u89e6\u53d1 API \u9650\u6d41")
            return None
        prices = resp.json().get("prices", [])
        if not prices:
            return []
        result = []
        for entry in prices:
            ts = from_unix_ms(entry[0])
            result.append((ts, float(entry[1])))
        return result
    except Exception as e:
        log.error("Failed CoinGecko history for coin_id=%s, cg_id=%s (days=%s): %s", coin_id, cg_id, days, e)
        return None


def parse_gateio_candle(entry):
    """Return (timestamp, close_price) from Gate.io candlestick response."""
    if isinstance(entry, dict):
        timestamp = entry.get("t")
        close_price = entry.get("c")
    elif isinstance(entry, (list, tuple)) and len(entry) >= 3:
        timestamp = entry[0]
        close_price = entry[2]
    else:
        return None

    try:
        ts = from_unix_seconds(int(float(timestamp)))
        price = float(close_price)
        return ts, price
    except (TypeError, ValueError):
        return None


def fetch_gateio_history(coin_id, days):
    pair = f"{coin_id.upper()}{config.USDT_SUFFIX}"
    now = int(time.time())
    start = now - days * 24 * 60 * 60
    params = {
        "currency_pair": pair,
        "interval": config.HISTORY_CANDLE_INTERVAL,
        "from": start,
        "to": now
    }

    try:
        log.info(
            "Requesting Gate.io history price: coin_id=%s, pair=%s, days=%s, interval=%s",
            coin_id,
            pair,
            days,
            config.HISTORY_CANDLE_INTERVAL
        )
        resp = requests.get(config.GATEIO_CANDLESTICKS_URL, params=params, timeout=config.REQUEST_TIMEOUT)
        log.info("Gate.io history HTTP status: coin_id=%s, status_code=%s", coin_id, resp.status_code)
        if resp.status_code != 200:
            log.error(
                "Gate.io history request failed: coin_id=%s, pair=%s, days=%s, status_code=%s, response=%s",
                coin_id,
                pair,
                days,
                resp.status_code,
                resp.text[:500]
            )
            return None

        points = []
        data = resp.json()
        for entry in data:
            parsed = parse_gateio_candle(entry)
            if parsed:
                points.append(parsed)
        if not points:
            sample = data[:2] if isinstance(data, list) else data
            log.warning("Gate.io history response parsed zero points: coin_id=%s, sample=%s", coin_id, sample)
        points.sort(key=lambda item: item[0])
        return points
    except Exception as e:
        log.error("Failed Gate.io history for coin_id=%s, pair=%s (days=%s): %s", coin_id, pair, days, e)
        return None


def collect_tickers(db, record_history=False):
    log.info("Fetching Gate.io tickers...")
    data = fetch_gateio_tickers()
    if data is None:
        return

    whitelist_set = {c: i for i, c in enumerate(config.WHITELIST)}
    usdt_pairs = []

    for ticker in data:
        pair = ticker.get("currency_pair", "")
        if not pair.endswith(config.USDT_SUFFIX):
            continue
        base = pair[:pair.index("_")]
        coin_id = base.lower()
        if coin_id not in whitelist_set:
            continue
        usdt_pairs.append((whitelist_set[coin_id], ticker, base))

    usdt_pairs.sort(key=lambda x: x[0])
    usdt_pairs = usdt_pairs[:config.MAX_COINS]

    count = 0
    for _, ticker, base in usdt_pairs:
        coin_id = base.lower()
        symbol = base.upper()
        name = symbol
        try:
            price = float(ticker.get("last", "0") or "0")
        except (ValueError, TypeError):
            price = 0.0
        try:
            change = float(ticker.get("change_percentage", "0") or "0")
        except (ValueError, TypeError):
            change = 0.0

        db.upsert_coin(coin_id, symbol, name, price, change)
        if record_history and price > 0:
            snapshot_ts = app_now().replace(second=0, microsecond=0)
            db.upsert_price_point(coin_id, snapshot_ts, price)
        count += 1

    log.info("Updated %d coins from Gate.io", count)
    if record_history:
        log.info("Recorded realtime price snapshot for %d coins", count)
    return [base.lower() for _, _, base in usdt_pairs]


def collect_fear_greed(db):
    log.info("Fetching Fear & Greed Index...")
    data = fetch_fear_greed()
    if data is None:
        return
    db.upsert_fear_greed(data["value"], data["classification"], data["timestamp"])
    log.info("Fear & Greed: %s/100 (%s)", data["value"], data["classification"])


def collect_history(db, coin_ids):
    for coin_id in coin_ids:
        cg_id = config.CG_ID_MAP.get(coin_id, coin_id)
        for days in config.HISTORY_DAYS_LIST:
            log.info("Fetching history for %s (%s days)...", coin_id, days)
            if getattr(config, "HISTORY_SOURCE", "gateio").lower() == "coingecko":
                points = fetch_coingecko_history(coin_id, cg_id, days)
            else:
                points = fetch_gateio_history(coin_id, days)
            if points is None or not points:
                time.sleep(config.HISTORY_REQUEST_DELAY)
                continue
            db.delete_price_points_window(coin_id, days)
            db.batch_replace_price_points(coin_id, points)
            log.info("Stored %d history points for %s", len(points), coin_id)
            time.sleep(config.HISTORY_REQUEST_DELAY)


def main():
    log.info("=== Coin Data Collector Started ===")
    db = Database()

    last_fng = 0
    last_history = 0
    last_realtime_history = 0
    saved_coin_ids = []

    try:
        saved_coin_ids = collect_tickers(db, record_history=True) or saved_coin_ids
        last_realtime_history = time.time()
        collect_fear_greed(db)
        last_fng = time.time()
        if saved_coin_ids:
            collect_history(db, saved_coin_ids[:config.HISTORY_COIN_LIMIT])
            last_history = time.time()

        while True:
            now = time.time()
            should_record_history = now - last_realtime_history >= config.REALTIME_HISTORY_INTERVAL
            saved_coin_ids = collect_tickers(db, record_history=should_record_history) or saved_coin_ids
            if should_record_history:
                last_realtime_history = now

            if now - last_fng >= config.FNG_INTERVAL:
                collect_fear_greed(db)
                last_fng = now

            if now - last_history >= config.HISTORY_INTERVAL:
                if saved_coin_ids:
                    collect_history(db, saved_coin_ids[:config.HISTORY_COIN_LIMIT])
                last_history = now

            time.sleep(config.COLLECT_INTERVAL)

    except KeyboardInterrupt:
        log.info("Shutting down gracefully...")
    finally:
        db.close()
        log.info("=== Collector Stopped ===")


if __name__ == "__main__":
    main()
