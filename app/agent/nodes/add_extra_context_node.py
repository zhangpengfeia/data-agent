from app.agent.state import DBInfoState
from app.agent.state import DateInfoState
from datetime import datetime
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def add_extra_context_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """
    添加额外上下文节点
    """
    # 1.获取流写入器对象
    write = runtime.stream_writer
    write({"type": "progress", "step": "添加上下文", "status": "running"})

    # 2.具体逻辑
    try:
        # 1.获取当天对象
        today = datetime.today()
        # 2.获取日期，星期数
        date_str = today.strftime("%Y-%m-%d")
        week_str = today.strftime("%A %Y-%m-%d")
        # 3. 获取季度
        quarter = (today.month - 1) // 3 + 1
        quarter_str = f"第{quarter}季度"
        # 4. 封装日期state
        date_state = DateInfoState(
            date=date_str,
            week=week_str,
            quarter=quarter_str,
        )
        # 5. 封装数据库信息
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        db_info = await dw_mysql_repository.get_db_info()
        db_info_state = DBInfoState(
            version=db_info["version"],
            dialect=db_info["dialect"],
        )
        write({"type": "progress", "step": "添加上下文", "status": "success"})
        logger.info(f"添加上下文成功：{date_state} {db_info_state}")
        return {"date_info": date_state, "db_info": db_info_state}
    except Exception as e:
        logger.error(f"添加上下文发生异常：{e}")
        write({"type": "progress", "step": "添加上下文", "status": "error"})
        raise
