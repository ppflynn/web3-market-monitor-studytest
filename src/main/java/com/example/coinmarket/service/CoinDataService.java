package com.example.coinmarket.service;

import com.example.coinmarket.config.CacheConfig;
import com.example.coinmarket.entity.Coin;
import com.example.coinmarket.entity.PricePoint;
import com.example.coinmarket.repository.CoinRepository;
import com.example.coinmarket.repository.PricePointRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.Cache;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class CoinDataService {

    private static final String CACHE_NAME = CacheConfig.ALL_COINS_CACHE;
    private static final String CACHE_KEY = "coinList";
    private static final List<String> PRIORITY_COIN_IDS = Arrays.asList(
            "btc", "eth", "bnb", "sol", "xrp", "ada", "doge", "dot", "link",
            "ltc", "bch", "avax", "matic", "uni", "shib", "trx", "etc",
            "apt", "near", "op", "arb"
    );

    private final CoinRepository coinRepository;
    private final PricePointRepository pricePointRepository;
    private final CacheManager cacheManager;

    @Cacheable(value = CACHE_NAME, key = "'coinList'")
    public List<Coin> getAllCoins() {
        log.info("Cache miss for allCoins, loading from database");
        List<Coin> coins = coinRepository.findAll();
        coins.sort(Comparator.comparingInt(CoinDataService::priorityOf)
                .thenComparing(coin -> coin.getSymbol() == null ? "" : coin.getSymbol(),
                        String.CASE_INSENSITIVE_ORDER));
        return coins;
    }

    public List<PricePoint> getHistoricalPrices(String coinId, int days) {
        String cacheKey = coinId + ":" + days;
        Cache pricePointsCache = cacheManager.getCache(CacheConfig.PRICE_POINTS_CACHE);
        @SuppressWarnings("unchecked")
        List<PricePoint> cached = pricePointsCache == null ? null : pricePointsCache.get(cacheKey, List.class);
        if (cached != null) {
            log.debug("Cache hit for historical prices: coinId={}, days={}", coinId, days);
            return cached;
        }

        log.info("Cache miss for historical prices: coinId={}, days={}", coinId, days);

        LocalDateTime from = LocalDateTime.now().minusDays(days);
        LocalDateTime to = LocalDateTime.now();
        List<PricePoint> points = pricePointRepository.findByCoinIdAndTimestampBetweenOrderByTimestampAsc(
                coinId, from, to);

        if (pricePointsCache != null) {
            pricePointsCache.put(cacheKey, points);
        }
        log.info("Historical prices loaded from DB and cached: coinId={}, count={}", coinId, points.size());
        return points;
    }

    private static int priorityOf(Coin coin) {
        if (coin == null || coin.getCoinId() == null) {
            return Integer.MAX_VALUE;
        }
        int index = PRIORITY_COIN_IDS.indexOf(coin.getCoinId().toLowerCase());
        return index >= 0 ? index : PRIORITY_COIN_IDS.size();
    }

    public List<Map<String, Object>> getCoinHistory(String coinId, int days) {
        log.info("Fetching coin history: coinId={}, days={}", coinId, days);
        List<PricePoint> points = getHistoricalPrices(coinId, days);
        List<Map<String, Object>> history = new ArrayList<>();
        for (PricePoint point : points) {
            Map<String, Object> entry = new HashMap<>();
            entry.put("timestamp", point.getTimestamp());
            entry.put("price", point.getPrice());
            history.add(entry);
        }
        log.debug("Returning {} history entries for coinId={}", history.size(), coinId);
        return history;
    }

}
