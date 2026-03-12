package com.emohealer.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("chat_record")
public class ChatRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String userMessage;
    private String aiReply;
    private String emotionType;
    private BigDecimal emotionScore;
    private Integer isCrisis;
    private LocalDateTime createdAt;
}
