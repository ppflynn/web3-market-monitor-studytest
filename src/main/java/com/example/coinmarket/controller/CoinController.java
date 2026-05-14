package com.example.coinmarket.controller;

import com.example.coinmarket.entity.Coin;
import com.example.coinmarket.repository.CoinRepository;
import com.example.coinmarket.service.CoinDataService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Slf4j
@RestController
@RequestMapping("/api/coins")
@RequiredArgsConstructor
public class CoinController {

    private final CoinDataService coinDataService;
    private final CoinRepository coinRepository;

    @GetMapping
    public ResponseEntity<List<Coin>> getAllCoins() {
        log.info("GET /api/coins - Fetching all coins from cache/database");
        List<Coin> coins = coinDataService.getAllCoins();
        log.debug("Returning {} coins", coins.size());
        return ResponseEntity.ok(coins);
    }

    @GetMapping("/{coinId}")
    public ResponseEntity<Coin> getCoinByCoinId(@PathVariable String coinId) {
        log.info("GET /api/coins/{} - Fetching coin detail", coinId);
        Optional<Coin> coin = coinRepository.findByCoinId(coinId);
        return coin.map(ResponseEntity::ok)
                .orElseGet(() -> {
                    log.warn("Coin not found: {}", coinId);
                    return ResponseEntity.notFound().build();
                });
    }

    @GetMapping("/{coinId}/history")
    public ResponseEntity<List<Map<String, Object>>> getCoinHistory(
            @PathVariable String coinId,
            @RequestParam(defaultValue = "7") int days) {
        log.info("GET /api/coins/{}/history - days={}", coinId, days);
        List<Map<String, Object>> history = coinDataService.getCoinHistory(coinId, days);
        return ResponseEntity.ok(history);
    }

    @GetMapping("/search")
    public ResponseEntity<Page<Coin>> searchCoins(
            @RequestParam String keyword,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        log.info("GET /api/coins/search - keyword={}, page={}, size={}", keyword, page, size);
        Pageable pageable = PageRequest.of(page, size);
        Page<Coin> result = coinRepository.findByNameContainingIgnoreCaseOrSymbolContainingIgnoreCase(
                keyword, keyword, pageable);
        log.debug("Search returned {} results for keyword '{}'", result.getTotalElements(), keyword);
        return ResponseEntity.ok(result);
    }

}
