package com.emohealer.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("healing_plan")
public class HealingPlan {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private LocalDate planDate;
    private String tasks;
    private BigDecimal completionRate;
    private String status;
    private String aiSummary;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
