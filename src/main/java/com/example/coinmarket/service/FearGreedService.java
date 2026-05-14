package com.example.coinmarket.service;

import com.example.coinmarket.entity.FearGreed;
import com.example.coinmarket.repository.FearGreedRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class FearGreedService {

    private final FearGreedRepository fearGreedRepository;

    public Map<String, Object> getFearGreedIndex() {
        Optional<FearGreed> opt = fearGreedRepository.findById(1);
        Map<String, Object> result = new HashMap<>();
        if (opt.isPresent()) {
            FearGreed fg = opt.get();
            result.put("value", fg.getValue() != null ? fg.getValue() : 50);
            result.put("classification", fg.getClassification() != null ? fg.getClassification() : "Neutral");
            result.put("timestamp", fg.getUnixTimestamp() != null ? fg.getUnixTimestamp() : 0L);
        } else {
            result.put("value", 50);
            result.put("classification", "Neutral");
            result.put("timestamp", 0L);
        }
        return result;
    }

}
