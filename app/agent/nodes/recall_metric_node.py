
from app.core.log import logger
from app.agent.context import DataAgentContext
from langgraph.runtime import Runtime
from app.agent.state import DataAgentState


async def recall_metric_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 1.获取流写入器对象
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回指标", "status": "running"})

    # 2.逻辑
    try:
        # 计算召回指标
        recall = 0.5
        writer({"type": "progress", "step": "召回指标", "status": "success", "recall": recall})
    except Exception as e:
        writer({"type": "progress", "step": "召回指标", "status": "error", "error": str(e)})
        logger.error(e)
        raise e
    

    pass