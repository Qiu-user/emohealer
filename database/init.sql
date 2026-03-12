-- =====================================================
-- EmoHealer AI 情绪疗愈平台数据库初始化脚本
-- 数据库: MySQL 8.0
-- 创建时间: 2026-03-10
-- =====================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS emohealer DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE emohealer;

-- =====================================================
-- 1. 用户表
-- =====================================================
DROP TABLE IF EXISTS user;
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    nickname VARCHAR(50) COMMENT '昵称',
    avatar_url VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
    bio TEXT COMMENT '个人简介',
    gender VARCHAR(10) DEFAULT 'unknown' COMMENT '性别: male-female-unknown',
    birthday DATE DEFAULT NULL COMMENT '生日',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用 1-正常',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色: user-普通用户 admin-管理员',
    last_login DATETIME DEFAULT NULL COMMENT '最后登录时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 用户登录Token表
DROP TABLE IF EXISTS user_token;
CREATE TABLE user_token (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    token VARCHAR(255) UNIQUE NOT NULL COMMENT 'Token',
    expires_at DATETIME NOT NULL COMMENT '过期时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户Token表';

-- =====================================================
-- 2. 对话记录表
-- =====================================================
DROP TABLE IF EXISTS chat_record;
CREATE TABLE chat_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '对话ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    user_message TEXT NOT NULL COMMENT '用户消息',
    ai_reply TEXT COMMENT 'AI回复',
    emotion_type VARCHAR(20) DEFAULT NULL COMMENT '情绪类型: happy-开心 sad-难过 anxious-焦虑 angry-愤怒 tired-疲惫 neutral-中性',
    emotion_score DECIMAL(5,2) DEFAULT NULL COMMENT '情绪得分 0-100',
    is_crisis TINYINT DEFAULT 0 COMMENT '是否危机: 0-否 1-是',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_emotion_type (emotion_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话记录表';

-- =====================================================
-- 3. 情绪日志表
-- =====================================================
DROP TABLE IF EXISTS emotion_log;
CREATE TABLE emotion_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    emotion_type VARCHAR(20) NOT NULL COMMENT '情绪类型',
    emotion_score DECIMAL(5,2) COMMENT '情绪得分 0-100',
    confidence DECIMAL(5,4) COMMENT '置信度 0-1',
    source VARCHAR(20) DEFAULT 'text' COMMENT '来源: text-文本 voice-语音 video-视频',
    trigger_context TEXT COMMENT '触发上下文',
    context_tags JSON COMMENT '上下文标签',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_emotion_type (emotion_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪日志表';

-- =====================================================
-- 4. 疗愈方案表
-- =====================================================
DROP TABLE IF EXISTS healing_plan;
CREATE TABLE healing_plan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '方案ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    plan_date DATE NOT NULL COMMENT '计划日期',
    tasks JSON NOT NULL COMMENT '任务列表 JSON格式',
    completion_rate DECIMAL(5,2) DEFAULT 0.00 COMMENT '完成率 0-100',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending-待执行 in_progress-进行中 completed-已完成',
    ai_summary TEXT COMMENT 'AI总结',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_plan_date (plan_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='疗愈方案表';

-- =====================================================
-- 5. 危机预警表
-- =====================================================
DROP TABLE IF EXISTS crisis_alert;
CREATE TABLE crisis_alert (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '预警ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    alert_level VARCHAR(20) NOT NULL COMMENT '预警级别: low-低危 medium-中危 high-高危 critical-危急',
    reason TEXT COMMENT '触发原因',
    keywords JSON COMMENT '触发关键词',
    chat_record_id BIGINT DEFAULT NULL COMMENT '关联对话ID',
    is_handled TINYINT DEFAULT 0 COMMENT '是否处理: 0-未处理 1-已处理',
    handler_id BIGINT DEFAULT NULL COMMENT '处理人ID',
    handler_note TEXT COMMENT '处理备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    handled_at DATETIME DEFAULT NULL COMMENT '处理时间',
    INDEX idx_user_id (user_id),
    INDEX idx_alert_level (alert_level),
    INDEX idx_is_handled (is_handled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='危机预警表';

-- =====================================================
-- 6. 心理测评表
-- =====================================================
DROP TABLE IF EXISTS psychological_assessment;
CREATE TABLE psychological_assessment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '测评ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    assessment_type VARCHAR(50) NOT NULL COMMENT '测评类型: PHQ-9抑郁筛查 GAD-7焦虑筛查',
    total_score INT COMMENT '总分',
    level VARCHAR(20) COMMENT '严重程度: none-无 mild-轻度 moderate-中度 severe-重度',
    answers JSON COMMENT '答题记录',
    suggestions TEXT COMMENT '建议',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_assessment_type (assessment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='心理测评表';

-- =====================================================
-- 7. 咨询预约表
-- =====================================================
DROP TABLE IF EXISTS consultation_appointment;
CREATE TABLE consultation_appointment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '预约ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    counselor_name VARCHAR(50) COMMENT '咨询师姓名',
    counselor_id BIGINT DEFAULT NULL COMMENT '咨询师ID',
    appointment_time DATETIME NOT NULL COMMENT '预约时间',
    duration INT DEFAULT 50 COMMENT '时长(分钟)',
    consultation_type VARCHAR(20) DEFAULT 'video' COMMENT '咨询方式: video-视频 voice-语音 chat-文字',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending-待确认 confirmed-已确认 completed-已完成 cancelled-已取消',
    ai_pre_report TEXT COMMENT 'AI预诊报告',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_appointment_time (appointment_time),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='咨询预约表';

-- =====================================================
-- 8. 系统配置表
-- =====================================================
DROP TABLE IF EXISTS system_config;
CREATE TABLE system_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(50) UNIQUE NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(255) COMMENT '描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 初始化系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('crisis_keywords', '["自杀", "自伤", "放弃", "不想活", "结束一切", "绝望"]', '危机关键词列表'),
('emotion_threshold_anxious', '70', '焦虑情绪阈值'),
('emotion_threshold_sad', '75', '抑郁情绪阈值'),
('max_daily_conversations', '100', '每日最大对话次数'),
('ai_model', 'wenxin', 'AI模型: wenxin-文心一言 chatglm-ChatGLM'),
('crisis_alert_email', 'support@emohealer.com', '危机预警通知邮箱');

SELECT '数据库初始化完成！' AS result;
