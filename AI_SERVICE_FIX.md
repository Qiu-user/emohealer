# AI服务连接问题诊断和解决方案

## 问题描述
前端提示"无法连接到AI服务，请确保后端服务已启动"

## 诊断结果

### ✅ AI API连接测试 - 通过
```
状态码: 200
AI回复: 你好！我是Qwen，由阿里云开发的大型语言模型...
Token使用: 105
```

### ✅ AI智能体配置 - 正确
```
use_llm: True
provider: openai
api_key: sk-yvrlkvsdjcocuqafl...
api_base: https://api.siliconflow.cn/v1
model: Qwen/Qwen2.5-7B-Instruct
```

### ✅ AI智能体chat方法 - 正常工作
```
reply: 听到你今天工作顺利，感觉很开心...
emotion: happy
confidence: 0.6
is_crisis: False
agent_role: listener
```

### ❌ 后端API - 返回500错误
```
状态码: 500
响应: Internal Server Error
```

## 问题分析

AI服务本身是正常工作的，问题出在后端API处理流程中。可能的原因：

1. **数据库会话问题** - FastAPI依赖注入的db会话可能有问题
2. **异步调用问题** - 可能在await某个操作时出错
3. **模型序列化问题** - 返回数据格式可能有问题
4. **后端实例冲突** - 多个后端实例导致的状态不一致

## 解决方案

### 方案1: 重启后端服务（推荐）

```batch
# 停止所有后端进程
taskkill /F /IM python.exe

# 重新启动后端
cd c:\Users\18746\Desktop\biyeshixi\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8092 --reload
```

### 方案2: 检查后端日志

查看后端控制台输出的错误日志，定位具体是哪行代码出错。

### 方案3: 使用前端直接测试

1. 打开浏览器访问: http://localhost:5000/emohealer2.html
2. 登录账号
3. 在聊天框输入消息
4. 查看浏览器控制台(F12)的错误信息

### 方案4: 检查数据库连接

```bash
mysql -h localhost -u root -p emohealer
```

确认以下表存在且可访问：
- user
- user_token
- chat_record

## 快速验证步骤

### 1. 验证后端服务状态
```bash
netstat -ano | findstr :8092
```

### 2. 测试API端点
```bash
# 健康检查
curl http://localhost:8092/docs

# 登录
curl -X POST http://localhost:8092/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'
```

### 3. 查看后端日志
如果后端是前台运行，查看控制台输出的错误信息。

## 临时替代方案

如果AI服务持续出现问题，可以临时使用Mock模式：

修改 `backend/src/config/ai_config.py`:
```python
AI_CONFIG = {
    "use_llm": False,  # 改为False使用Mock模式
    "llm_provider": "mock",
    ...
}
```

然后重启后端服务。

## 预期结果

重启后端服务后，应该能够：
1. ✅ 后端服务正常启动
2. ✅ 用户可以注册/登录
3. ✅ 发送消息获得AI回复
4. ✅ 前端显示AI回复内容

## 需要的信息

如果问题仍然存在，请提供：
1. 后端控制台的完整错误日志
2. 浏览器的开发者工具(F12) Console中的错误信息
3. 网络(Network)标签中 `/api/chat/send` 请求的响应

## 参考文档

- 后端API文档: http://localhost:8092/docs
- 前端页面: http://localhost:5000/emohealer2.html
- 硅基流动API: https://www.siliconflow.cn/
