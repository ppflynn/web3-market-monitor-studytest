package com.example.coinmarket.service;

import com.example.coinmarket.dto.SystemStatusResponse;
import com.example.coinmarket.entity.Coin;
import com.example.coinmarket.entity.FearGreed;
import com.example.coinmarket.entity.PricePoint;
import com.example.coinmarket.repository.CoinRepository;
import com.example.coinmarket.repository.FearGreedRepository;
import com.example.coinmarket.repository.PricePointRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class SystemStatusService {

    private static final int CURRENT_FEAR_GREED_ID = 1;

    private final CoinRepository coinRepository;
    private final PricePointRepository pricePointRepository;
    private final FearGreedRepository fearGreedRepository;

    public SystemStatusResponse getSystemStatus() {
        log.info("Fetching system status");

        Long coinCount = coinRepository.count();
        Long pricePointCount = pricePointRepository.count();
        LocalDateTime latestCoinUpdate = coinRepository.findTopByOrderByLastUpdatedDesc()
                .map(Coin::getLastUpdated)
                .orElse(null);
        LocalDateTime latestPriceUpdate = pricePointRepository.findTopByOrderByTimestampDesc()
                .map(PricePoint::getTimestamp)
                .orElse(null);
        Integer fearGreedValue = fearGreedRepository.findById(CURRENT_FEAR_GREED_ID)
                .map(FearGreed::getValue)
                .orElse(null);

        return new SystemStatusResponse(
                coinCount,
                pricePointCount,
                latestCoinUpdate,
                latestPriceUpdate,
                fearGreedValue,
                "成功运行"
        );
    }

}
