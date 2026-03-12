package com.emohealer.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("crisis_alert")
public class CrisisAlert {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String alertLevel;
    private String reason;
    private String keywords;
    private Long chatRecordId;
    private Integer isHandled;
    private Long handlerId;
    private String handlerNote;
    private LocalDateTime createdAt;
    private LocalDateTime handledAt;
}
