import asyncio

from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

llm = init_chat_model(
    model=app_config.llm.model_name,
    model_provider="openai",
    api_key=app_config.llm.api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0
)

if __name__ == "__main__":
    result = asyncio.run(llm.ainvoke("你好"))
    print(result.content)
