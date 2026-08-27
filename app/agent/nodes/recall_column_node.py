from langgraph.config import get_stream_writer
from app.agent.state import DataAgentState
async def recall_column_node(state: DataAgentState) -> DataAgentState:
    """召回列节点"""
    writer = get_stream_writer()
    writer.write("开始召回列\n")
    try:
        # 1. 从状态中获取关键词
        writer.write({"type": "progress", "step":"召回字段"})
        keywords = state["keywords"]
        return {"retrieved_columns": ["列1", "列2", "列3"]}


    except Exception as e:
        writer.write("关键词不存在\n")
        return {"retrieved_columns": []}

