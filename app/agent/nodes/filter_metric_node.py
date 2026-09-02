from app.prompt.prompt_loader import load_prompt
import yaml
from langchain_core.output_parsers import JsonOutputParser
from app.agent.llm import llm
from langchain_core.prompts.prompt import PromptTemplate
from app.agent.state import MetricInfoState
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def filter_metric_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """
    过滤指标节点
    """
    # 1.获取流写入器对象
    write = runtime.stream_writer
    write({"type": "progress", "step": "过滤指标", "status": "running"})
    # 2.具体逻辑
    try:
        # 1. 先拿到已召回合并节点的信息
        metric_infos: list[MetricInfoState] = state["metric_infos"]
        query: str = state["query"]

        # 2. 调用llm获取回答用户问题需要指标
        prompt = PromptTemplate(template=load_prompt("filter_metric_info"), input_variables=["query", "metric_infos"])
        out_put = JsonOutputParser()
        chain = prompt | llm | out_put
        result = await chain.ainvoke(
            {
                "query": query,
                "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            }
        )
        logger.info(f"过滤指标结果：{result}")

        # 3. 遍历指标信息列表，将不需要的指标信息移除
        filtered_metric_names = set(result)
        metric_infos = [
            metric_info
            for metric_info in metric_infos
            if metric_info["name"] in filtered_metric_names
        ]
        # 4. 更新state中指标信息列表 “metric_infos”
        write({"type": "progress", "step": "过滤指标", "status": "success"})
        return {"metric_infos": metric_infos}
    except Exception as e:
        logger.error(f"过滤指标发生异常：{e}")
        write({"type": "progress", "step": "过滤指标", "status": "error"})
        raise

if __name__ == "__main__":
    metric_state = MetricInfoState(
        name="AOV",
        description="平均订单价值",
        relevant_columns=["order_value"],
        alias=["平均订单价值"],
    )
    print(metric_state)
