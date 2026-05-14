package com.example.coinmarket.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.cache.Cache;
import org.springframework.cache.caffeine.CaffeineCache;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.TimeUnit;

@Configuration
public class CacheConfig {

    public static final String PRICE_POINTS_CACHE = "pricePointsCache";

    @Bean
    public Cache pricePointsCache() {
        return new CaffeineCache(PRICE_POINTS_CACHE,
                Caffeine.newBuilder()
                        .expireAfterWrite(30, TimeUnit.MINUTES)
                        .build());
    }

}
