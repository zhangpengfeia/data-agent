
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

# 1. 创建 graph 对象
graph_builder = StateGraph(DataAgentState)

# 2. 添加节点
graph_builder.add_node(extract_keywords_node)
graph_builder.add_node(recall_column_node)

# 3. 添加边
graph_builder.add_edge(START, "extract_keywords_node")
graph_builder.add_edge("extract_keywords_node", "recall_column_node")
graph_builder.add_edge("recall_column_node", END)

# 4. 编译得到 graph
graph = graph_builder.compile()

# 5. 测试
if __name__ == "__main__":
    async def test():
        state = DataAgentState(query="你好", context=context)
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
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                print(chunk)
 
            # 3.关闭连接
            await dw_mysql_client_manager.close()
            await meta_mysql_client_manager.close()
            await es_client_manager.close()
            await qdrant_client_manager.close()
        
    import asyncio
    asyncio.run(test())