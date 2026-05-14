package com.example.coinmarket.controller;

import com.example.coinmarket.service.FearGreedService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class FearGreedController {

    private final FearGreedService fearGreedService;

    @GetMapping("/fear-greed")
    public ResponseEntity<Map<String, Object>> getFearGreed() {
        log.info("GET /api/fear-greed");
        return ResponseEntity.ok(fearGreedService.getFearGreedIndex());
    }

}
