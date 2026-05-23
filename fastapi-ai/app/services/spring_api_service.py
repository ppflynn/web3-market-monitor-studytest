from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings


class SpringApiService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.spring_api_base_url.rstrip("/")

    async def build_market_context(self, question: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=self.settings.spring_api_timeout_seconds) as client:
                coins = await self._get_json(client, "/coins")
                fear_greed = await self._get_json(client, "/fear-greed")
                if not isinstance(coins, list):
                    return None

                matched = self._match_coins(question, coins)
                include_market = self._needs_market_context(question) or bool(matched)
                if not include_market:
                    return None

                history_summaries = []
                for coin in matched[:3]:
                    coin_id = self._value(coin, "coin_id", "coinId")
                    if not coin_id:
                        continue
                    history = await self._get_json(client, f"/coins/{coin_id}/history?days=7")
                    history_summaries.append(
                        {
                            "coin_id": coin_id,
                            "symbol": self._value(coin, "symbol"),
                            "history_7d": self._summarize_history(history),
                        }
                    )

                context = {
                    "data_source": "Spring Boot API backed by MySQL collector data",
                    "usage_rule": "回答行情问题时必须优先使用这些数据。不能编造未提供的数据。必须说明内容仅用于信息分析，不构成投资建议。",
                    "market_snapshot": [self._coin_snapshot(coin) for coin in coins],
                    "matched_coins": [self._coin_snapshot(coin) for coin in matched],
                    "fear_greed": fear_greed if isinstance(fear_greed, dict) else None,
                    "history_summaries": history_summaries,
                }
                return self._to_context_text(context)
        except httpx.RequestError:
            return None
        except Exception:
            return None

    async def _get_json(self, client: httpx.AsyncClient, path: str) -> Any:
        response = await client.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()

    def _match_coins(self, question: str, coins: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = question.lower()
        matched: list[dict[str, Any]] = []
        for coin in coins:
            coin_id = str(self._value(coin, "coin_id", "coinId") or "").lower()
            symbol = str(self._value(coin, "symbol") or "").lower()
            name = str(self._value(coin, "name") or "").lower()
            candidates = [value for value in [coin_id, symbol, name] if value]
            if any(self._contains_token(normalized, candidate) for candidate in candidates):
                matched.append(coin)
        return matched

    def _needs_market_context(self, question: str) -> bool:
        keywords = [
            "币",
            "币价",
            "行情",
            "走势",
            "价格",
            "市场",
            "涨跌",
            "恐惧",
            "贪婪",
            "fear",
            "greed",
            "market",
            "price",
        ]
        normalized = question.lower()
        return any(keyword in normalized for keyword in keywords)

    def _contains_token(self, text: str, token: str) -> bool:
        if not token:
            return False
        if len(token) <= 4 and token.isascii():
            padded = f" {text} "
            separators = " ,.;:!?()[]{}<>，。！？、：；\n\t"
            for sep in separators:
                padded = padded.replace(sep, " ")
            return f" {token} " in padded
        return token in text

    def _coin_snapshot(self, coin: dict[str, Any]) -> dict[str, Any]:
        return {
            "coin_id": self._value(coin, "coin_id", "coinId"),
            "symbol": self._value(coin, "symbol"),
            "name": self._value(coin, "name"),
            "current_price": self._value(coin, "current_price", "currentPrice"),
            "price_change_24h_percent": self._value(
                coin,
                "price_change_percentage_24h",
                "priceChangePercentage24h",
                "price_change_percentage24h",
            ),
            "market_cap": self._value(coin, "market_cap", "marketCap"),
            "last_updated": self._value(coin, "last_updated", "lastUpdated"),
        }

    def _summarize_history(self, history: Any) -> dict[str, Any] | None:
        if not isinstance(history, list) or not history:
            return None

        points = []
        for item in history:
            if not isinstance(item, dict):
                continue
            price = self._value(item, "price", "close", "value")
            timestamp = self._value(item, "timestamp", "date", "time")
            if price is None:
                continue
            points.append({"price": float(price), "timestamp": timestamp})

        if not points:
            return None

        first = points[0]
        last = points[-1]
        first_price = first["price"]
        last_price = last["price"]
        change_pct = ((last_price - first_price) / first_price * 100) if first_price else None
        prices = [point["price"] for point in points]

        return {
            "points": len(points),
            "start_time": first["timestamp"],
            "end_time": last["timestamp"],
            "start_price": round(first_price, 8),
            "latest_price": round(last_price, 8),
            "change_percent": round(change_pct, 4) if change_pct is not None else None,
            "high": round(max(prices), 8),
            "low": round(min(prices), 8),
            "recent_points": points[-8:],
        }

    def _to_context_text(self, context: dict[str, Any]) -> str:
        lines = [
            "【项目真实数据上下文】",
            f"数据来源：{context['data_source']}",
            f"使用规则：{context['usage_rule']}",
            "",
            "当前市场快照：",
        ]
        for coin in context["market_snapshot"]:
            lines.append(f"- {coin}")

        if context["fear_greed"]:
            lines.extend(["", f"恐惧与贪婪指数：{context['fear_greed']}"])

        if context["matched_coins"]:
            lines.extend(["", "用户问题命中的币种："])
            for coin in context["matched_coins"]:
                lines.append(f"- {coin}")

        if context["history_summaries"]:
            lines.extend(["", "命中币种 7 天历史摘要："])
            for item in context["history_summaries"]:
                lines.append(f"- {item}")

        return "\n".join(lines)

    def _value(self, data: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data:
                return data[key]
        return None
