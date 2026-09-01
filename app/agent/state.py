from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from typing import TypedDict

class DataAgentState(TypedDict):
    """数据智能体的状态"""
    query: str
    keywords: list[str]
    error: str
    retrieved_columns: list[ColumnInfo]
    retrieved_metrics: dict[str, MetricInfo]
