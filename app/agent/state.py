from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo

class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

class DBInfoState(TypedDict):
    """数据库信息"""
    version: str
    dialect: str


class DateInfoState(TypedDict):
    """日期信息"""
    date: str
    week: str
    quarter: str


class DataAgentState(TypedDict):
    # 提问问题
    query: str
    # 抽取关键字节点结果
    keywords: list[str]
    # 召回字段节点结果
    retrieved_columns: list[ColumnInfo]
    # 召回指标节点结果
    retrieved_metrics: list[MetricInfo]
    # 召回字段取值结果
    retrieved_values: list[ValueInfo]
    # 数据库信息
    db_info: DBInfoState
    # 日期信息
    date_info: DateInfoState
    # 生成SQL节点结果
    sql: str

    # 合并节点结果
    table_infos: list[TableInfoState]  # 表信息
    metric_infos: list[MetricInfoState]  # 指标信息

    # 校验SQL节点 SQL错误信息
    error: str | None
