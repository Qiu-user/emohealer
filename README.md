# EmoHealer 情绪疗愈平台

基于AI的情绪疗愈系统

## 功能特点

- 🤖 AI对话陪伴 - 智能情绪识别与回复
- 📈 情绪趋势分析 - 可视化情绪变化
- 📝 情绪日记 - 记录心情，保护隐私
- 💡 疗愈方案 - 个性化情绪管理
- 📅 预约咨询 - 心理咨询服务

## 技术栈

- 后端: FastAPI + Python
- 前端: HTML + JavaScript + ECharts
- 数据库: MySQL 8.0
- AI: 增强版AI智能体（LLM集成）

## 快速开始

### 方式一：Docker 部署（推荐团队协作）

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 启动 MySQL 数据库
docker-compose up -d mysql

# 3. 等待数据库初始化完成
docker-compose logs -f mysql

# 4. 启动后端
cd backend
pip install -r requirements.txt
python main.py
```

### 方式二：本地开发

#### 1. 启动 MySQL 数据库

```bash
# 使用 Docker 启动
docker run -d \
  --name emohealer_mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=emohealer \
  -v mysql_data:/var/lib/mysql \
  mysql:8.0
```

#### 2. 初始化数据库

```bash
# 执行建表脚本
mysql -u root -p emohealer < database/init.sql

# 导入测试数据（可选）
mysql -u root -p emohealer < database/test_data.sql
```

#### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### 4. 启动前端

```bash
cd frontend
python -m http.server 5000
```

#### 5. 访问系统

打开浏览器: http://localhost:5000/emohealer2.html

## Docker 常用命令

```bash
# 启动数据库
docker-compose up -d mysql

# 查看日志
docker-compose logs -f mysql

# 停止服务
docker-compose down

# 完全清除数据
docker-compose down -v

# 重启数据库
docker-compose restart mysql
```

## 数据库连接信息

| 配置项 | 默认值 |
|--------|--------|
| 主机 | localhost |
| 端口 | 3306 |
| 用户名 | emohealer |
| 密码 | emohealer_pass_2026 |
| 数据库 | emohealer |

## 项目结构

```
biyeshixi/
├── backend/              # 后端代码
│   ├── src/
│   │   ├── routes/      # API路由
│   │   ├── services/    # 业务服务
│   │   └── models/      # 数据模型
│   ├── main.py          # 主入口
│   ├── config.py        # 配置文件
│   └── Dockerfile        # Docker配置
├── frontend/             # 前端页面
├── database/            # 数据库脚本
│   ├── init.sql         # 建表脚本
│   └── test_data.sql    # 测试数据
├── docker-compose.yml   # Docker编排配置
├── .env.example         # 环境变量示例
└── README.md
```

## 数据库表结构

- `user` - 用户表
- `user_token` - Token表
- `chat_record` - 对话记录
- `emotion_log` - 情绪日志
- `emotion_diary` - 情绪日记
- `healing_plan` - 疗愈方案
- `crisis_alert` - 危机预警
- `psychological_assessment` - 心理测评
- `consultation_appointment` - 咨询预约
- `token_usage` - Token消耗记录
- `operation_log` - 操作日志

## 测试账号

| 用户名 | 密码 |
|--------|------|
| testuser3 | 123456 |
| testuser2026 | 123456 |

## License

MIT
