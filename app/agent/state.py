from typing import TypedDict

class DataAgentState(TypedDict):
    """数据智能体的状态"""
    query: str
    keywords: list[str]
