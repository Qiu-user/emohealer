package com.emohealer.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("emotion_log")
public class EmotionLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String emotionType;
    private BigDecimal emotionScore;
    private BigDecimal confidence;
    private String source;
    private String triggerContext;
    private String contextTags;
    private LocalDateTime createdAt;
}
