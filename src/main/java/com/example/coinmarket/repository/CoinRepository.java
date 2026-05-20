package com.example.coinmarket.repository;

import com.example.coinmarket.entity.Coin;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CoinRepository extends JpaRepository<Coin, Long> {

    Optional<Coin> findByCoinId(String coinId);

    Optional<Coin> findBySymbolIgnoreCase(String symbol);

    Optional<Coin> findTopByOrderByLastUpdatedDesc();

    Page<Coin> findAllByOrderByMarketCapDesc(Pageable pageable);

    Page<Coin> findByNameContainingIgnoreCaseOrSymbolContainingIgnoreCase(
            String nameKeyword, String symbolKeyword, Pageable pageable);

}
