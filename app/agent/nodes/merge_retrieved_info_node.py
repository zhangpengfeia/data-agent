from app.entities.table_info import TableInfo
from app.agent.state import ColumnInfoState, TableInfoState
from app.entities.value_info import ValueInfo
from app.entities.column_info import ColumnInfo
from app.agent.state import MetricInfoState
from app.entities.metric_info import MetricInfo
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def merge_retrieved_info_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    write = runtime.stream_writer
    write({"type": "progress", "step": "合并召回信息", "status": "running"})
    # 2.具体逻辑
    try:
        # 1.1 从state获取已召回信息
        retrieved_metrics: list[MetricInfo] = state["retrieved_metrics"]
        retrieved_columns: list[ColumnInfo] = state["retrieved_columns"]
        retrieved_values: list[ValueInfo] = state["retrieved_values"]
        # 获取持久层数据对象
        meta_mysql_repository = runtime.context['meta_mysql_repository']

        # 2 封装已找回信息中包含所有字段
        column_id_column_info_dict = {column_info.id: column_info for column_info in retrieved_columns}

        for retrieved_metric in retrieved_metrics:
            for column_id in retrieved_metric.relevant_columns:
                if column_id not in column_id_column_info_dict:
                    column_info = await meta_mysql_repository.get_column_info_by_id(column_id)
                    column_id_column_info_dict[column_id] = column_info
        # 从召回自动取值列表中，得到自动取值对应字段id，将字段信息加入到字段字典中
        for value_info in retrieved_values:
            column_id = value_info.column_id
            if column_id not in column_id_column_info_dict:
                column_info = await meta_mysql_repository.get_column_info_by_id(column_id)
                column_id_column_info_dict[column_id] = column_info
            value = value_info.value
            if value not in column_id_column_info_dict[column_id].examples:
                column_id_column_info_dict[column_id].examples.append(value)

        # 将所有字段信息转为 表-字段列表 字典
        table_id_column_info_dict = {}
        for column_info in column_id_column_info_dict.values():
            table_id = column_info.table_id
            if table_id not in table_id_column_info_dict:
                table_id_column_info_dict[table_id] = []
            table_id_column_info_dict[table_id].append(column_info)

        #3. 补齐主外键字段信息，遍历字段列表中key，得到每张表id，获取所有字段id，根据表id查询主外键字段
        for table_id in table_id_column_info_dict.keys():
            # 获取当前表已召回所有字段id
            column_ids = [column.id for column in table_id_column_info_dict[table_id]]
            # 根据id查询meta库中column_info表
            key_columns: list[ColumnInfo] = await meta_mysql_repository.get_key_columns_by_table_id(table_id)
            # 获取主外键列表
            for key_column in key_columns:
                if key_column.id not in column_ids:
                    table_id_column_info_dict[table_id].append(key_column)
        
        # 4. 处理表信息，封装table_infos
        table_infos: list[TableInfoState] = []
        for table_id, columns in table_id_column_info_dict.items():
            table_info: TableInfo = await meta_mysql_repository.get_table_info_by_id(table_id)
            table_info_state = TableInfoState(
                name=table_info.name,
                role=table_info.role,
                description=table_info.description,
                columns=[
                    ColumnInfoState(
                        name=column_info.name,
                        type=column_info.type,
                        role=column_info.role,
                        examples=list(column_info.examples),
                        description=column_info.description,
                        alias=list(column_info.alias),
                    )
                    for column_info in columns
                ]
            )
            table_infos.append(table_info_state)


        # 5 初始化存放指标信息列表
        metric_infos: list[MetricInfoState] = []

        # 3.1 处理指标信息，从已召回指标获取封装
        if retrieved_metrics:
            for metric in retrieved_metrics:
                metric_info_state=MetricInfoState(
                    name=metric.name,
                    description=metric.description,
                    relevant_columns=metric.relevant_columns,
                    alias=metric.alias,
                )
                metric_infos.append(metric_info_state)
        write({"type": "progress", "step": "合并召回信息", "status": "success"})
        logger.info(f"合并召回信息成功，表：{table_id_column_info_dict.keys()}")
        logger.info(f"合并召回信息成功，字段：{[column['name'] for ti in table_infos for column in ti['columns']]}")
        logger.info(f"合并召回信息成功，指标：{[metric_info["name"] for metric_info in metric_infos]}")
        return {"metric_infos": metric_infos, "table_infos": table_infos}
    except Exception as e:
        logger.error(f"合并召回信息发生异常：{e}")
        write({"type": "progress", "step": "合并召回信息", "status": "error"})
        raise
