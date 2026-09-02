from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """验证SQL语句是否符合语法规范"""
    # 1.获取流写入器对象
    write = runtime.stream_writer
    write({"type": "progress", "step": "验证SQL", "status": "running"})

    # 2.具体逻辑
    try:
        # 1.从state中获取sql语句
        sql = state["sql"]
        
        # 2.调用数仓持久层通过执行计划关键词验证sql
        dw_mysql_repository = runtime.context['dw_mysql_repository']
        await dw_mysql_repository.validate_sql(sql)

        # 3.返回验证结果
        write({"type": "progress", "step": "验证SQL", "status": "success"})
    except Exception as e:
        logger.error(f"验证SQL发生异常：{e}")
        write({"type": "progress", "step": "验证SQL", "status": "error"})
        return {"error": f"{e}"}
