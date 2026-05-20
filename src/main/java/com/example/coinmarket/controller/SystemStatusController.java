package com.example.coinmarket.controller;

import com.example.coinmarket.dto.SystemStatusResponse;
import com.example.coinmarket.service.SystemStatusService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class SystemStatusController {

    private final SystemStatusService systemStatusService;

    @GetMapping("/status")
    public ResponseEntity<SystemStatusResponse> getStatus() {
        log.info("GET /api/status");
        return ResponseEntity.ok(systemStatusService.getSystemStatus());
    }

}
