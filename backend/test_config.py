"""测试配置加载"""
import sys
sys.path.insert(0, '.')

from src.config.ai_config import AI_CONFIG

print("=== AI_CONFIG ===")
print(f"use_llm: {AI_CONFIG.get('use_llm')}")
print(f"llm_provider: {AI_CONFIG.get('llm_provider')}")

llm = AI_CONFIG.get('llm', {})
openai_config = llm.get('openai', {})
print(f"\nOpenAI配置:")
print(f"  api_key: {openai_config.get('api_key')[:10]}..." if openai_config.get('api_key') else "  api_key: None")
print(f"  api_base: {openai_config.get('api_base')}")
print(f"  model: {openai_config.get('model')}")

# 测试enhanced_ai_agent
print("\n=== EnhancedAIAgent ===")
from src.services.enhanced_ai_agent import enhanced_ai_agent
print(f"use_llm: {enhanced_ai_agent.use_llm}")
print(f"llm provider: {enhanced_ai_agent.llm.provider}")
print(f"llm api_key: {enhanced_ai_agent.llm.api_key[:10]}..." if enhanced_ai_agent.llm.api_key else "None")
print(f"llm api_base: {enhanced_ai_agent.llm.api_base}")
print(f"llm model: {enhanced_ai_agent.llm.model}")
