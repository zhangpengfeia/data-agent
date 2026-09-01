
from app.agent.nodes.add_extra_context_node import add_extra_context_node
from app.agent.nodes.correct_sql_node import correct_sql_node
from app.agent.nodes.execute_sql_node import execute_sql_node
from app.agent.nodes.validate_sql_node import validate_sql_node
from app.agent.nodes.generate_sql_node import generate_sql_node
from app.agent.nodes.filter_metric_node import filter_metric_node
from app.agent.nodes.filter_table_node import filter_table_node
from app.agent.nodes.merge_retrieved_info_node import merge_retrieved_info_node
from app.agent.nodes.recall_value_node import recall_value_node
from app.agent.nodes.recall_metric_node import recall_metric_node
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.clients.es_client_manager import es_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager
from app.agent.context import DataAgentContext
from app.agent.nodes.recall_column_node import recall_column_node
from langgraph.constants import START
from app.agent.state import DataAgentState
from app.agent.nodes.extract_keywords_node import extract_keywords_node
from langgraph.graph import StateGraph, END

def route_after_validate_sql(state: DataAgentState) -> str:
    """校验 SQL 后的路由：校验通过 -> 执行 SQL；校验失败 -> 校正 SQL"""
    if state["error"] is None:
        return "execute_sql_node"
    return "correct_sql_node"


# 1. 创建 graph 对象
graph_builder = StateGraph(DataAgentState)

# 2. 添加节点
graph_builder.add_node("extract_keywords_node", extract_keywords_node)
graph_builder.add_node("recall_column_node", recall_column_node)
graph_builder.add_node("recall_metric_node", recall_metric_node)
graph_builder.add_node("recall_value_node", recall_value_node)
graph_builder.add_node("merge_retrieved_info_node", merge_retrieved_info_node)
graph_builder.add_node("filter_table_node", filter_table_node)
graph_builder.add_node("filter_metric_node", filter_metric_node)
graph_builder.add_node("add_extra_context_node", add_extra_context_node)
graph_builder.add_node("generate_sql_node", generate_sql_node)
graph_builder.add_node("validate_sql_node", validate_sql_node)
graph_builder.add_node("correct_sql_node", correct_sql_node)
graph_builder.add_node("execute_sql_node", execute_sql_node)


# 3.添加边
graph_builder.add_edge(START, "extract_keywords_node")
graph_builder.add_edge("extract_keywords_node", "recall_column_node")
graph_builder.add_edge("extract_keywords_node", "recall_metric_node")
graph_builder.add_edge("extract_keywords_node", "recall_value_node")

graph_builder.add_edge("recall_column_node", "merge_retrieved_info_node")
graph_builder.add_edge("recall_metric_node", "merge_retrieved_info_node")
graph_builder.add_edge("recall_value_node", "merge_retrieved_info_node")

graph_builder.add_edge("merge_retrieved_info_node", "filter_table_node")
graph_builder.add_edge("merge_retrieved_info_node", "filter_metric_node")

graph_builder.add_edge("filter_table_node", "add_extra_context_node")
graph_builder.add_edge("filter_metric_node", "add_extra_context_node")

graph_builder.add_edge("add_extra_context_node", "generate_sql_node")
graph_builder.add_edge("generate_sql_node", "validate_sql_node")

# 条件边：如果校验 SQL 节点 error 为 None 则执行 SQL，否则先校正 SQL
graph_builder.add_conditional_edges(
    "validate_sql_node",
    route_after_validate_sql,
    {
        "execute_sql_node": "execute_sql_node",
        "correct_sql_node": "correct_sql_node",
    },
)

graph_builder.add_edge("correct_sql_node", "execute_sql_node")
graph_builder.add_edge("execute_sql_node", END)

# 4. 编译得到 graph
graph = graph_builder.compile()

# 5. 测试
if __name__ == "__main__":
    print(graph.get_graph().draw_mermaid())
    async def test():
        dw_mysql_client_manager.init()
        meta_mysql_client_manager.init()
        embedding_client_manager.init()
        qdrant_client_manager.init()
        es_client_manager.init()

        # 2.创建不同持久对象
        async with (meta_mysql_client_manager.session_factory() as meta_session, dw_mysql_client_manager.session_factory() as dw_session):
            context = DataAgentContext(
                meta_mysql_repository=MetaMySQLRepository(meta_session),
                dw_mysql_repository=DWMySQLRepository(dw_session),
                embedding_client=embedding_client_manager.client,
                column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manager.client),
                metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client),
                value_es_repository=ValueESRepository(es_client_manager.client)

            )
            state = DataAgentState(query="你好，我是张三，我想知道北京的天气", context=context)
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                print(chunk)
 
            # 3.关闭连接
            await dw_mysql_client_manager.close()
            await meta_mysql_client_manager.close()
            await es_client_manager.close()
            await qdrant_client_manager.close()
        
    import asyncio
    asyncio.run(test())