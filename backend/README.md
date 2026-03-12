# EmoHealer 后端服务

基于 Python FastAPI 的情绪疗愈平台后端服务。

## 技术栈

- **框架**: FastAPI
- **数据库**: MySQL 8.0
- **ORM**: SQLAlchemy
- **验证**: Pydantic

## 项目结构

```
backend/
├── main.py                 # 应用入口
├── config.py               # 配置文件
├── database.py             # 数据库连接
├── requirements.txt       # Python依赖
├── README.md              # 本文件
└── src/
    ├── models/
    │   └── models.py       # 数据模型
    ├── routes/
    │   └── api.py          # API路由
    └── services/
        └── ai_service.py   # AI服务
```

## API 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/chat/send` | POST | 发送消息获取AI回复 |
| `/api/chat/history/{user_id}` | GET | 获取对话历史 |
| `/api/emotion/trend` | POST | 获取情绪趋势数据 |
| `/api/users` | GET | 获取用户列表 |
| `/api/user/{user_id}` | GET | 获取用户信息 |
| `/api/healing-plan/{user_id}` | GET | 获取疗愈方案 |
| `/api/plans/{user_id}` | GET | 获取疗愈方案列表 |
| `/api/assessment/submit` | POST | 提交心理测评 |
| `/api/assessment/{user_id}` | GET | 获取测评历史 |
| `/api/appointment/submit` | POST | 提交预约咨询 |
| `/api/appointment/{user_id}` | GET | 获取预约列表 |
| `/api/stats/{user_id}` | GET | 获取用户统计 |

## 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8088 --reload
```

## 配置

在 `config.py` 中修改数据库连接配置：

```python
DATABASE_URL = "mysql+pymysql://root:19891213@localhost:3306/emohealer"
HOST = "0.0.0.0"
PORT = 8088
```

## 运行要求

- Python 3.8+
- MySQL 8.0+
