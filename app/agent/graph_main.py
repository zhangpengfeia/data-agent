from langgraph.constants import START
from app.agent.state import DataAgentState
from app.agent.nodes.extract_keywords_node import extract_keywords_node
from langgraph.graph import StateGraph, END

# 1. 创建graph 对象
graph_builder = StateGraph(DataAgentState)

# 2. 添加节点
graph_builder.add_node(extract_keywords_node)

# 3. 添加边
graph_builder.add_edge(START, "extract_keywords_node")
graph_builder.add_edge("extract_keywords_node", END)

# 4. 编译得到graph
graph = graph_builder.compile()

# 5. 测试
if __name__ == "__main__":
    print(graph.get_graph().draw_mermaid())