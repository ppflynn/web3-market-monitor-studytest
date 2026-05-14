package com.example.coinmarket.repository;

import com.example.coinmarket.entity.FearGreed;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface FearGreedRepository extends JpaRepository<FearGreed, Integer> {
}
