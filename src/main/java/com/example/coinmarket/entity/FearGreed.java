package com.example.coinmarket.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "fear_greed")
public class FearGreed {

    @Id
    private Integer id = 1;

    private Integer value;

    private String classification;

    private Long unixTimestamp;

    private LocalDateTime updatedAt;

}
