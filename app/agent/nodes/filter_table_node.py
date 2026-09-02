import yaml
from app.agent.llm import llm
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.prompt.prompt_loader import load_prompt
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def filter_table_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """
    过滤表格节点
    """
    # 1.获取流写入器对象
    write = runtime.stream_writer
    write({"type": "progress", "step": "过滤表格", "status": "running"})

    # 2.具体逻辑
    try:
        #1. 从state中获取表格信息列表
        table_infos = state["table_infos"]
        query = state["query"]

        # 2. 调用llm获取回答用户问题所需要表跟字段
        prompt = PromptTemplate(template=load_prompt("filter_table_info"), input_variables=["query", "table_infos"])
        out_put = JsonOutputParser()
        chain = prompt | llm | out_put
        result = await chain.ainvoke(
            {
                "query": query,
                "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            }
        )
        logger.info(f"过滤表格结果：{result}")

        # 3.遍历表信息列表，将不需要的信息以及表中字段删除
        for table_info in table_infos[:]:
            table_name = table_info['name']
            if table_name not in result:
                table_infos.remove(table_info)
            else:
                table_info["columns"] = [
                    column
                    for column in table_info["columns"]
                    if column["name"] in result[table_name]
                ]

        logger.info(f"过滤表格结果：{table_infos}")
        write({"type": "progress", "step": "过滤表格", "status": "success"})
        return {"table_infos": table_infos}
    except Exception as e:
        logger.error(f"过滤表格发生异常：{e}")
        write({"type": "progress", "step": "过滤表格", "status": "error"})
        raise
