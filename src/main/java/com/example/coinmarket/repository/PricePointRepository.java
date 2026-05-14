package com.example.coinmarket.repository;

import com.example.coinmarket.entity.PricePoint;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface PricePointRepository extends JpaRepository<PricePoint, Long> {

    List<PricePoint> findByCoinIdAndTimestampBetweenOrderByTimestampAsc(
            String coinId, LocalDateTime start, LocalDateTime end);

    Optional<PricePoint> findTopByCoinIdOrderByTimestampDesc(String coinId);

    @Modifying
    @Transactional
    @Query("DELETE FROM PricePoint p WHERE p.coinId = ?1 AND p.timestamp BETWEEN ?2 AND ?3")
    void deleteByCoinIdAndTimestampBetween(String coinId, LocalDateTime start, LocalDateTime end);

}
