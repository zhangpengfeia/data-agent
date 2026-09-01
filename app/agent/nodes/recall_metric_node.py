
from app.entities.metric_info import MetricInfo
from app.agent.llm import llm
from langchain_core.output_parsers.json import JsonOutputParser
from app.prompt.prompt_loader import load_prompt
from langchain_core.prompts.prompt import PromptTemplate
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
        # 2.1 从state获取用户问题，关键词列表
        query = state["query"]
        keywords = state["keywords"]

        # 2.2 先对原query问题通过llm进行扩展
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_metric_recall"), input_variables=["query"])
        json_output = JsonOutputParser()
        chain = prompt | llm | json_output
        result = await chain.ainvoke({"query": query})

        # 2.3 得到最终关键词列表 = llm扩展后关键词+state中jieba分词后关键词
        keywords = list(set(keywords + result))
        # 2.4 声明指标信息字典，方便去重，字典key=指标id, value = 指标信息
        retrieved_metrics = {}

        # 2.5 从runtime总获取Embedding客户端，指标向量持久层
        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repository = runtime.context["metric_qdrant_repository"]

        # 2.6 遍历关键词列表，执行向量检索
        for keyword in keywords:
            # 2.6.1 将关键词转为向量
            keyword_embedding = await embedding_client.aembed_query(keyword)
            # 2.6.2 执行向量检索
            metric_infos: list[MetricInfo] = await metric_qdrant_repository.search(keyword_embedding)
            # 2.6.3 去重合并指标信息
            for metric_info in metric_infos:
                metric_id = metric_info.id
                if metric_id not in retrieved_metrics:
                    retrieved_metrics[metric_id] = metric_info
        # 2.7
        writer({"type": "progress", "step": "召回指标", "status": "success"})
        logger.info(f"指标召回信息成功: {list(retrieved_metrics.keys())}")
        return {"retrieved_metrics": retrieved_metrics}


    except Exception as e:
        writer({"type": "progress", "step": "召回指标", "status": "error", "error": str(e)})
        logger.error(e)
        raise e
