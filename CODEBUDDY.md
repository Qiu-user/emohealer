# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 项目概述

EmoHealer 是一个基于AI的情绪疗愈平台，为18-35岁用户提供7×24小时的情绪支持服务。

## 常用命令

### 启动后端服务
```bash
cd backend
python main.py
# 默认端口: 8092
```

### 启动前端服务
```bash
cd frontend
python -m http.server 5000
# 访问: http://localhost:5000/emohealer2.html
```

### 直接访问后端API页面
```
http://localhost:8092/emohealer
http://localhost:8092/docs (API文档)
```

## 项目架构

### 技术栈
- **后端**: FastAPI (Python) + MySQL
- **前端**: 原生HTML + JavaScript + ECharts
- **AI**: 增强版AI智能体 (多角色LLM集成)

### 目录结构
```
biyeshixi/
├── backend/                 # FastAPI后端
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置
│   ├── src/
│   │   ├── routes/         # API路由 (api.py, websocket.py)
│   │   ├── services/       # 业务服务 (ai_agent.py, enhanced_ai_agent.py)
│   │   └── models/         # 数据模型
│   └── requirements.txt
├── frontend/                # 前端页面
│   └── emohealer2.html    # 主页面
├── database/               # 数据库脚本
│   ├── init.sql           # 建表脚本
│   └── test_data.sql      # 测试数据
└── README.md
```

### 核心API路由 (backend/src/routes/api.py)
- `/api/auth/*` - 用户认证 (登录/注册)
- `/api/chat/send` - 发送消息获取AI回复
- `/api/emotion/*` - 情绪分析、报告、趋势
- `/api/plans/*` - 疗愈方案
- `/api/websocket/chat` - WebSocket实时通信

### 前端关键页面 (emohealer2.html)
- 情绪疗愈页面 (`page-chat`) - AI对话
- 情绪报告页面 (`page-report`) - 情绪数据分析
- 疗愈方案页面 (`page-plan`) - 个性化方案生成与执行
- 呼吸练习页面 (`page-breathing`)
- 心理测评页面 (`page-assessment`)

### 前端关键函数 (emohealer2.html)
- `showPage(pageId)` - 页面切换
- `sendMessage()` - 发送聊天消息
- `generateAIPersonalPlan()` - 生成AI个性化方案
- `startPlanExecution()` / `startQuickPlan()` - 开始执行疗愈任务
- `renderPlanExecutionView()` - 显示任务执行界面 (含AI引导)

## 数据库表 (database/init.sql)
- `user` - 用户表
- `user_token` - Token表
- `chat_record` - 对话记录
- `emotion_log` - 情绪日志
- `healing_plan` - 疗愈方案
- `crisis_alert` - 危机预警
- `psychological_assessment` - 心理测评
- `consultation_appointment` - 咨询预约

## 开发注意事项

1. **前端调用后端**: 使用 `API_BASE = 'http://localhost:8092'`
2. **认证**: Token存储在localStorage，发送请求需带Authorization头
3. **情绪历史**: 保存在localStorage (`emohealer_emotion_history`)
4. **疗愈方案执行**: 在page-plan内完成，不跳转页面
5. **WebSocket**: 用于实时通信，URL `ws://localhost:8092/ws/chat`

## 部署

当前使用Python HTTP服务器开发预览，生产环境建议使用Nginx反向代理。
