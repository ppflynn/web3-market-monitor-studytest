from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Awaitable, Callable
from urllib.parse import quote

import httpx

from app.config import Settings


ToolFetcher = Callable[[], Awaitable[Any]]


@dataclass(frozen=True)
class ToolRunResult:
    context_text: str | None
    calls: list[dict[str, Any]]


class MarketToolService:
    """Structured market-data tools backed by the Spring Boot API."""

    TOOL_DEFINITIONS: list[dict[str, Any]] = [
        {
            "name": "list_market_coins",
            "description": "List coins currently tracked by the project with latest price, 24h change, and market cap.",
            "parameters": {},
        },
        {
            "name": "get_coin_detail",
            "description": "Get one tracked coin by coin_id, for example btc, eth, sol, bnb, or xrp.",
            "parameters": {"coin_id": "string"},
        },
        {
            "name": "get_coin_history",
            "description": "Get historical price points for a tracked coin.",
            "parameters": {"coin_id": "string", "days": "integer"},
        },
        {
            "name": "get_fear_greed",
            "description": "Get the latest Fear & Greed market sentiment index.",
            "parameters": {},
        },
        {
            "name": "search_coins",
            "description": "Search tracked coins by name or symbol.",
            "parameters": {"keyword": "string", "page": "integer", "size": "integer"},
        },
        {
            "name": "get_top_movers",
            "description": "Rank tracked coins by 24h price change.",
            "parameters": {"direction": "gainers|losers", "limit": "integer"},
        },
    ]

    MARKET_KEYWORDS = [
        "行情",
        "币价",
        "价格",
        "走势",
        "市场",
        "涨跌",
        "涨幅",
        "跌幅",
        "市值",
        "恐惧",
        "贪婪",
        "情绪",
        "排行",
        "榜",
        "market",
        "price",
        "trend",
        "history",
        "fear",
        "greed",
        "gainer",
        "loser",
    ]
    HISTORY_KEYWORDS = ["走势", "历史", "最近", "近", "trend", "history", "days", "day", "week"]
    FEAR_GREED_KEYWORDS = ["恐惧", "贪婪", "情绪", "fear", "greed", "sentiment"]
    SEARCH_KEYWORDS = ["搜索", "查找", "查询", "找", "search"]
    TOP_GAINER_KEYWORDS = ["涨幅", "上涨", "涨得", "涨最多", "gainer", "gainers", "top gain"]
    TOP_LOSER_KEYWORDS = ["跌幅", "下跌", "跌得", "跌最多", "loser", "losers", "top loss"]

    COIN_ALIASES = {
        "btc": "btc",
        "bitcoin": "btc",
        "比特币": "btc",
        "eth": "eth",
        "ethereum": "eth",
        "以太坊": "eth",
        "sol": "sol",
        "solana": "sol",
        "bnb": "bnb",
        "binance": "bnb",
        "xrp": "xrp",
        "ripple": "xrp",
        "瑞波": "xrp",
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.spring_api_base_url.rstrip("/")

    def list_tools(self) -> list[dict[str, Any]]:
        return self.TOOL_DEFINITIONS

    async def execute_for_question(self, question: str) -> ToolRunResult:
        if not self.settings.market_tools_enabled or not self._needs_market_tools(question):
            return ToolRunResult(context_text=None, calls=[])

        calls: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=self.settings.spring_api_timeout_seconds) as client:
            coins = await self._record_api_call(
                calls,
                "list_market_coins",
                {},
                lambda: self._get_json(client, "/coins"),
            )
            coin_list = coins if isinstance(coins, list) else []
            matched_coins = self._match_coins(question, coin_list)

            if self._needs_search(question):
                keyword = self._extract_search_keyword(question, matched_coins)
                if keyword:
                    await self._record_api_call(
                        calls,
                        "search_coins",
                        {"keyword": keyword, "page": 0, "size": 20},
                        lambda keyword=keyword: self._get_json(
                            client,
                            f"/coins/search?keyword={quote(keyword)}&page=0&size=20",
                        ),
                    )

            if self._needs_fear_greed(question) or self._is_broad_market_question(question):
                await self._record_api_call(calls, "get_fear_greed", {}, lambda: self._get_json(client, "/fear-greed"))

            direction = self._top_mover_direction(question)
            if direction and coin_list:
                self._record_derived_call(
                    calls,
                    "get_top_movers",
                    {"direction": direction, "limit": 5},
                    self._top_movers(coin_list, direction=direction, limit=5),
                )

            days = self._extract_days(question)
            should_load_history = self._needs_history(question)
            for coin in matched_coins[:3]:
                coin_id = self._value(coin, "coin_id", "coinId")
                if not coin_id:
                    continue
                await self._record_api_call(
                    calls,
                    "get_coin_detail",
                    {"coin_id": coin_id},
                    lambda coin_id=coin_id: self._get_json(client, f"/coins/{coin_id}"),
                )
                if should_load_history:
                    await self._record_api_call(
                        calls,
                        "get_coin_history",
                        {"coin_id": coin_id, "days": days},
                        lambda coin_id=coin_id, days=days: self._get_json(client, f"/coins/{coin_id}/history?days={days}"),
                    )

        return ToolRunResult(context_text=self._to_context_text(calls), calls=calls)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> ToolRunResult:
        arguments = arguments or {}
        calls: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=self.settings.spring_api_timeout_seconds) as client:
            if tool_name == "list_market_coins":
                await self._record_api_call(calls, tool_name, {}, lambda: self._get_json(client, "/coins"))
            elif tool_name == "get_coin_detail":
                coin_id = str(arguments.get("coin_id") or "").lower().strip()
                await self._record_api_call(calls, tool_name, {"coin_id": coin_id}, lambda: self._get_json(client, f"/coins/{coin_id}"))
            elif tool_name == "get_coin_history":
                coin_id = str(arguments.get("coin_id") or "").lower().strip()
                days = self._normalize_days(arguments.get("days"))
                await self._record_api_call(
                    calls,
                    tool_name,
                    {"coin_id": coin_id, "days": days},
                    lambda: self._get_json(client, f"/coins/{coin_id}/history?days={days}"),
                )
            elif tool_name == "get_fear_greed":
                await self._record_api_call(calls, tool_name, {}, lambda: self._get_json(client, "/fear-greed"))
            elif tool_name == "search_coins":
                keyword = str(arguments.get("keyword") or "").strip()
                page = self._safe_int(arguments.get("page"), default=0, minimum=0, maximum=100)
                size = self._safe_int(arguments.get("size"), default=20, minimum=1, maximum=100)
                await self._record_api_call(
                    calls,
                    tool_name,
                    {"keyword": keyword, "page": page, "size": size},
                    lambda: self._get_json(client, f"/coins/search?keyword={quote(keyword)}&page={page}&size={size}"),
                )
            elif tool_name == "get_top_movers":
                direction = str(arguments.get("direction") or "gainers").lower().strip()
                if direction not in {"gainers", "losers"}:
                    direction = "gainers"
                limit = self._safe_int(arguments.get("limit"), default=5, minimum=1, maximum=20)
                coins = await self._record_api_call(calls, "list_market_coins", {}, lambda: self._get_json(client, "/coins"))
                if isinstance(coins, list):
                    self._record_derived_call(
                        calls,
                        tool_name,
                        {"direction": direction, "limit": limit},
                        self._top_movers(coins, direction=direction, limit=limit),
                    )
            else:
                calls.append(
                    {
                        "name": tool_name,
                        "arguments": arguments,
                        "result": None,
                        "error": f"Unknown tool: {tool_name}",
                    }
                )

        return ToolRunResult(context_text=self._to_context_text(calls), calls=calls)

    async def _get_json(self, client: httpx.AsyncClient, path: str) -> Any:
        response = await client.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()

    async def _record_api_call(
        self,
        calls: list[dict[str, Any]],
        name: str,
        arguments: dict[str, Any],
        fetcher: ToolFetcher,
    ) -> Any:
        try:
            result = await fetcher()
            result = self._compact_result(name, result)
            calls.append({"name": name, "arguments": arguments, "result": result, "error": None})
            return result
        except httpx.HTTPStatusError as exc:
            error = f"Spring API returned HTTP {exc.response.status_code}"
        except httpx.RequestError as exc:
            error = f"Spring API request failed: {exc.__class__.__name__}"
        except Exception as exc:
            error = f"Tool execution failed: {exc.__class__.__name__}"
        calls.append({"name": name, "arguments": arguments, "result": None, "error": error})
        return None

    def _record_derived_call(
        self,
        calls: list[dict[str, Any]],
        name: str,
        arguments: dict[str, Any],
        result: Any,
    ) -> None:
        calls.append({"name": name, "arguments": arguments, "result": result, "error": None})

    def _compact_result(self, name: str, result: Any) -> Any:
        if name == "list_market_coins" and isinstance(result, list):
            return [self._coin_snapshot(coin) for coin in result if isinstance(coin, dict)]
        if name == "search_coins" and isinstance(result, dict):
            content = result.get("content")
            if isinstance(content, list):
                compact = dict(result)
                compact["content"] = [self._coin_snapshot(coin) for coin in content if isinstance(coin, dict)]
                return compact
        if name == "get_coin_detail" and isinstance(result, dict):
            return self._coin_snapshot(result)
        if name == "get_coin_history":
            return self._summarize_history(result)
        return result

    def _to_context_text(self, calls: list[dict[str, Any]]) -> str | None:
        useful_calls = [call for call in calls if call.get("result") is not None or call.get("error")]
        if not useful_calls:
            return None

        lines = [
            "[Market tool context]",
            "These are structured results from project tools backed by the Spring Boot API and MySQL/Redis data.",
            "Use these results first for market questions. Do not invent prices or rankings not present here.",
            "",
        ]
        for index, call in enumerate(useful_calls, start=1):
            lines.append(f"Tool {index}: {call['name']}")
            lines.append(f"Arguments: {json.dumps(call.get('arguments') or {}, ensure_ascii=False)}")
            if call.get("error"):
                lines.append(f"Error: {call['error']}")
            else:
                lines.append(f"Result: {json.dumps(call.get('result'), ensure_ascii=False, default=str)}")
            lines.append("")

        text = "\n".join(lines).strip()
        max_chars = self.settings.market_tool_max_context_chars
        return text if len(text) <= max_chars else f"{text[:max_chars].rstrip()}..."

    def _needs_market_tools(self, question: str) -> bool:
        normalized = question.lower()
        if any(keyword in normalized for keyword in self.MARKET_KEYWORDS):
            return True
        return any(self._contains_token(normalized, alias.lower()) for alias in self.COIN_ALIASES)

    def _needs_history(self, question: str) -> bool:
        normalized = question.lower()
        if any(keyword in normalized for keyword in self.HISTORY_KEYWORDS):
            return True
        return bool(re.search(r"\d{1,3}\s*天|\d{1,3}\s*(?:day|days|d)\b", question, flags=re.IGNORECASE))

    def _needs_fear_greed(self, question: str) -> bool:
        normalized = question.lower()
        return any(keyword in normalized for keyword in self.FEAR_GREED_KEYWORDS)

    def _needs_search(self, question: str) -> bool:
        normalized = question.lower()
        return any(keyword in normalized for keyword in self.SEARCH_KEYWORDS)

    def _is_broad_market_question(self, question: str) -> bool:
        normalized = question.lower()
        return any(keyword in normalized for keyword in ["行情", "市场", "market", "情绪", "整体"])

    def _top_mover_direction(self, question: str) -> str | None:
        normalized = question.lower()
        if any(keyword in normalized for keyword in self.TOP_LOSER_KEYWORDS):
            return "losers"
        if any(keyword in normalized for keyword in self.TOP_GAINER_KEYWORDS):
            return "gainers"
        return None

    def _match_coins(self, question: str, coins: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = question.lower()
        alias_coin_ids = {
            coin_id
            for alias, coin_id in self.COIN_ALIASES.items()
            if self._contains_token(normalized, alias.lower())
        }
        matched: list[dict[str, Any]] = []
        for coin in coins:
            coin_id = str(self._value(coin, "coin_id", "coinId") or "").lower()
            symbol = str(self._value(coin, "symbol") or "").lower()
            name = str(self._value(coin, "name") or "").lower()
            candidates = [value for value in [coin_id, symbol, name] if value]
            if coin_id in alias_coin_ids or any(self._contains_token(normalized, candidate) for candidate in candidates):
                matched.append(coin)
        return matched

    def _extract_search_keyword(self, question: str, matched_coins: list[dict[str, Any]]) -> str | None:
        if matched_coins:
            return str(self._value(matched_coins[0], "symbol", "coin_id", "coinId") or "").strip()
        patterns = [
            r"(?:搜索|查找|查询|找)\s*([A-Za-z0-9_-]{2,20})",
            r"search\s+([A-Za-z0-9_-]{2,20})",
        ]
        for pattern in patterns:
            match = re.search(pattern, question, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        ascii_terms = re.findall(r"[A-Za-z0-9_-]{2,20}", question)
        stop_words = {"search", "market", "price", "coin", "coins"}
        for term in ascii_terms:
            if term.lower() not in stop_words:
                return term
        return None

    def _extract_days(self, question: str) -> int:
        patterns = [
            r"(\d{1,3})\s*天",
            r"(\d{1,3})\s*(?:day|days|d)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, question, flags=re.IGNORECASE)
            if match:
                return self._normalize_days(match.group(1))
        if "周" in question or "week" in question.lower():
            return self._normalize_days(7)
        return self._normalize_days(self.settings.market_tool_default_history_days)

    def _normalize_days(self, value: Any) -> int:
        return self._safe_int(
            value,
            default=self.settings.market_tool_default_history_days,
            minimum=1,
            maximum=self.settings.market_tool_max_history_days,
        )

    def _top_movers(self, coins: list[dict[str, Any]], direction: str, limit: int) -> list[dict[str, Any]]:
        snapshots = [self._coin_snapshot(coin) for coin in coins if isinstance(coin, dict)]
        snapshots = [coin for coin in snapshots if coin["price_change_24h_percent"] is not None]
        reverse = direction == "gainers"
        return sorted(snapshots, key=lambda coin: float(coin["price_change_24h_percent"]), reverse=reverse)[:limit]

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

    def _contains_token(self, text: str, token: str) -> bool:
        if not token:
            return False
        if len(token) <= 4 and token.isascii():
            pattern = rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])"
            return re.search(pattern, text, flags=re.IGNORECASE) is not None
        return token in text

    def _safe_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(parsed, maximum))

    def _value(self, data: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data:
                return data[key]
        return None
