import yaml
from app.agent.llm import llm
from langchain_core.output_parsers import StrOutputParser
from app.prompt.prompt_loader import load_prompt
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def generate_sql_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """根据SQL模板生成SQL语句"""
    # 1.获取流写入器对象
    write = runtime.stream_writer
    write({"type": "progress", "step": "生成SQL", "status": "running"})

    # 2.具体逻辑
    try:
        # 1.从state中获取生成sql上下文信息
        query = state["query"]
        table_infos = state["table_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]
        metric_infos = state["metric_infos"]

        # 2.调用大模型生成纯文本sql
        prompt = PromptTemplate(template=load_prompt("generate_sql"), input_variables=["query", "table_infos", "date_info", "db_info", "metric_infos"])
        str_output_parse = StrOutputParser()
        chain = prompt | llm | str_output_parse
        sql = await chain.ainvoke({"query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False)
        })
        write({"type": "progress", "step": "生成SQL", "status": "success"})
        logger.info(f"生成SQL成功：{sql}")
        return {"sql": sql}
    except Exception as e:
        logger.error(f"生成SQL发生异常：{e}")
        write({"type": "progress", "step": "生成SQL", "status": "error"})
        raise
