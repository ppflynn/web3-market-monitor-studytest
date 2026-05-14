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

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("collector")


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
                    INDEX idx_coin_id_timestamp (coin_id, timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
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

    def upsert_coin(self, coin_id, symbol, name, price, change_pct):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM coins WHERE coin_id = %s", (coin_id,))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """UPDATE coins SET symbol=%s, name=%s, current_price=%s,
                       market_cap=0, price_change_percentage_24h=%s,
                       last_updated=NOW()
                       WHERE coin_id=%s""",
                    (symbol, name, price, change_pct, coin_id)
                )
            else:
                cur.execute(
                    """INSERT INTO coins (coin_id, symbol, name, current_price,
                       market_cap, price_change_percentage_24h, last_updated)
                       VALUES (%s, %s, %s, %s, 0, %s, NOW())""",
                    (coin_id, symbol, name, price, change_pct)
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

    def delete_old_price_points(self, coin_id, days):
        since = datetime.now() - timedelta(days=days)
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM price_points WHERE coin_id=%s AND timestamp < %s",
                (coin_id, since)
            )
        self.conn.commit()

    def upsert_fear_greed(self, value, classification, unix_ts):
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO fear_greed (id, value, classification, unix_timestamp, updated_at)
                   VALUES (1, %s, %s, %s, NOW())
                   ON DUPLICATE KEY UPDATE
                   value=VALUES(value), classification=VALUES(classification),
                   unix_timestamp=VALUES(unix_timestamp), updated_at=NOW()""",
                (value, classification, unix_ts)
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


def fetch_coingecko_history(cg_id, days):
    url = config.COINGECKO_CHART_URL.format(cg_id, days)
    try:
        resp = requests.get(url, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        prices = resp.json().get("prices", [])
        if not prices:
            return []
        result = []
        for entry in prices:
            ts = datetime.fromtimestamp(entry[0] / 1000)
            result.append((ts, float(entry[1])))
        return result
    except Exception as e:
        log.error("Failed CoinGecko history for %s (days=%s): %s", cg_id, days, e)
        return None


def collect_tickers(db):
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
        usdt_pairs.append((whitelist_set.get(base.lower(), 999999), ticker, base))

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
        count += 1

    log.info("Updated %d coins from Gate.io", count)
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
            points = fetch_coingecko_history(cg_id, days)
            if points is None or not points:
                time.sleep(config.HISTORY_REQUEST_DELAY)
                continue
            db.delete_old_price_points(coin_id, days)
            db.batch_replace_price_points(coin_id, points)
            log.info("Stored %d history points for %s", len(points), coin_id)
            time.sleep(config.HISTORY_REQUEST_DELAY)


def main():
    log.info("=== Coin Data Collector Started ===")
    db = Database()

    last_fng = 0
    last_history = 0
    saved_coin_ids = []

    try:
        saved_coin_ids = collect_tickers(db) or saved_coin_ids
        collect_fear_greed(db)
        last_fng = time.time()
        if saved_coin_ids:
            collect_history(db, saved_coin_ids[:config.HISTORY_COIN_LIMIT])
            last_history = time.time()

        while True:
            now = time.time()
            saved_coin_ids = collect_tickers(db) or saved_coin_ids

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
