"""
EmoHealer AI服务配置
用于配置AI智能体的各种参数和LLM连接
"""

# AI智能体配置
AI_CONFIG = {
    # 是否启用LLM（设为True使用真实LLM，False使用规则引擎）
    "use_llm": True,

    # LLM提供商选项: mock, baidu, openai, anthropic, chatglm
    "llm_provider": "openai",
    
    # LLM配置（根据provider填写相应配置）
    "llm": {
        # 百度文心一言
        "baidu": {
            "api_key": "",      # 百度API Key
            "api_secret": "",   # 百度API Secret
            "model": "ernie-lite-8k"
        },
        # OpenAI (支持ChatGPT、硅基流动等兼容API)
        "openai": {
            "api_key": "sk-yvrlkvsdjcocuqaflmemkcevtgacjzclofysaetmztwhulcm",      # API Key
            "api_base": "https://api.siliconflow.cn/v1",  # 硅基流动API地址
            "model": "Qwen/Qwen2.5-7B-Instruct"  # 推荐模型（免费额度可用）
        },
        # Anthropic Claude
        "anthropic": {
            "api_key": "",
            "model": "claude-3-sonnet-20240229"
        },
        # ChatGLM 本地/云端
        "chatglm": {
            "api_base": "http://localhost:8000",
            "model": "chatglm3-6b"
        }
    },
    
    # 对话配置
    "conversation": {
        # 最大历史消息数
        "max_history": 20,
        # 回复最大token数
        "max_tokens": 500,
        # 温度参数（创造性程度）
        "temperature": 0.8
    },
    
    # 情绪检测配置
    "emotion_detection": {
        # 置信度阈值
        "confidence_threshold": 0.5,
        # 是否启用高级情绪分析
        "enable_advanced": True
    },
    
    # 危机检测配置
    "crisis_detection": {
        # 是否启用
        "enabled": True,
        # 高危机关键词列表（可自定义添加）
        "high_risk_keywords": [
            '自杀', '自伤', '想死', '不想活', '结束一切', '抹脖子', '上吊',
            '跳楼', '割腕', '安眠药', '氰化物', '活着没意义', '不想活了'
        ],
        # 危机干预热线
        "hotline": "400-161-9995"
    }
}


def get_ai_config():
    """获取AI配置"""
    return AI_CONFIG


def update_llm_provider(provider: str, **kwargs):
    """更新LLM提供商配置"""
    AI_CONFIG["llm_provider"] = provider
    AI_CONFIG["use_llm"] = (provider != "mock")
    
    if provider in kwargs:
        AI_CONFIG["llm"][provider].update(kwargs[provider])
    
    return AI_CONFIG


# API密钥配置说明：
# 
# 1. 百度文心一言：
#    - 访问 https://console.bce.baidu.com/ 创建应用
#    - 获取 API Key 和 Secret Key
#
# 2. OpenAI:
#    - 访问 https://platform.openai.com 获取API Key
#    - 或者使用硅基流动等国内兼容API
#
# 3. Anthropic Claude:
#    - 访问 https://console.anthropic.com 获取API Key
#
# 4. ChatGLM:
#    - 本地部署：使用 https://github.com/THUDM/ChatGLM3
#    - 云端API：使用硅基流动等平台
