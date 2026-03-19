-- 情绪日记表迁移脚本
-- 运行此脚本在现有数据库中创建情绪日记表

CREATE TABLE IF NOT EXISTS emotion_diary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日记ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    title VARCHAR(200) COMMENT '日记标题',
    content TEXT NOT NULL COMMENT '日记内容',
    mood_tags JSON COMMENT '心情标签',
    emotion_type VARCHAR(20) COMMENT '主要情绪类型',
    weather VARCHAR(20) COMMENT '天气',
    location VARCHAR(100) COMMENT '地点',
    is_archived TINYINT DEFAULT 0 COMMENT '是否归档',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_emotion_type (emotion_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪日记表';

SELECT '情绪日记表创建成功!' AS result;