from langgraph.config import get_stream_writer
from app.agent.state import DataAgentState


async def extract_keywords_node(state: DataAgentState) -> dict[str, list[str]]:
    """入口节点，将用户问题提取关键词"""

    # 1. 获取流写入器对象
    writer = get_stream_writer()
    writer.write("开始提取关键词\n")


    # 2. 从状态中获取用户问题
    query = state["query"]


    # 3. 自定义数据 处理成功
    writer.write("处理成功\n")

    # 实现关键词提取逻辑
    keywords = [
        "你好",
        "查询",
        "数据",
        "列",
        "表",
    ]


    return {"keywords": keywords}
