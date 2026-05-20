package com.example.coinmarket.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SystemStatusResponse {

    private Long coinCount;

    private Long pricePointCount;

    private LocalDateTime latestCoinUpdate;

    private LocalDateTime latestPriceUpdate;

    private Integer fearGreedValue;

    private String system_status;

}
