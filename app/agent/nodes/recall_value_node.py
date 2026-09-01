from app.entities.value_info import ValueInfo
from app.agent import llm
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.prompt.prompt_loader import load_prompt
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def recall_value_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """召回字段取值节点， 获取真实有效字段取值，解决llm生成sql where部分字段取值"""
   
    # 1.获取流写入器对象
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段取值", "status": "running"})

    try:
        # 2.具体逻辑
        # 2.1 获取state中用户问题，抽取关键词节点，关键词列表
        query = state["query"]
        keywords = state["keywords"]

        # 2.2 对原问题通过llm扩展关键词
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_value_recall"), input_variables=["query"])
        json_output = JsonOutputParser()
        chain = prompt | llm | json_output
        result = await chain.ainvoke({"query": query})

        # 2.3 最终关键词列表 = llm扩容后 + state中关键词列表
        keywords = list(set(keywords + result))
        
        # 2.4 初始化自动取值字典，字典key = 字段取值id value=字段取值对象
        retrieved_values_dict: dict[str, ValueInfo] = {}
        
        # 2.5 runtime中获取操作es持久层对象
        value_es_repository = runtime.context.get("value_es_repository")

        # 2.6 遍历关键词列表，执行全文检索，处理结果
        for keyword in keywords:
            results: list[ValueInfo] = await value_es_repository.search(keyword)
            for result in results:
                value_id = result.id
                if value_id not in retrieved_values_dict:
                    retrieved_values_dict[value_id] = result
        writer({"type": "progress", "step": "召回字段取值", "status": "success", "message": "召回字段取值完成"})
        retrieved_values = list(retrieved_values_dict.keys())
        logger.info(f"召回字段取值完成，共召回{len(retrieved_values)}个字段取值")
        # 2.7 更新 state 中的 retrieved_values
        return {"retrieved_values": retrieved_values}
        # 2.8 返回state
    except Exception as e:
        writer({"type": "progress", "step": "召回指标", "status": "error", "error": str(e)})
        logger.error(e)
        raise e
