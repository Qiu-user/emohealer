# EmoHealer 情绪疗愈平台

基于AI的情绪疗愈系统

## 功能特点

- 🤖 AI对话陪伴 - 智能情绪识别与回复
- 📈 情绪趋势分析 - 可视化情绪变化
- 📝 心理测评 - 专业心理评估
- 💡 疗愈方案 - 个性化情绪管理
- 📅 预约咨询 - 心理咨询服务

## 技术栈

- 后端: FastAPI + Python
- 前端: HTML + JavaScript + ECharts
- 数据库: MySQL
- AI: 增强版AI智能体

## 快速开始

### 1. 启动后端

```bash
cd backend
python main.py
# 或
python -m uvicorn main:app --host 0.0.0.0 --port 8088
```

### 2. 访问系统

打开浏览器: http://localhost:8088/emohealer

## 项目结构

```
biyeshixi/
├── backend/           # 后端代码
│   ├── src/
│   │   ├── routes/   # API路由
│   │   ├── services/ # 业务服务
│   │   └── models/   # 数据模型
│   ├── main.py       # 主入口
│   └── config.py     # 配置文件
├── frontend/          # 前端页面
├── database/         # 数据库脚本
└── README.md
```

## License

MIT
