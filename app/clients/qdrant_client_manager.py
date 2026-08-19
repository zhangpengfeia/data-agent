import asyncio
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PointStruct, UpdateResult, QueryResponse, Filter,
    FieldCondition, MatchValue
)

from app.clients.embedding_client_manager import embedding_client_manager
from app.conf.app_config import QdrantConfig, app_config


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client: Optional[AsyncQdrantClient] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncQdrantClient(
            url=self._get_url()
        )

    async def close(self):
        if self.client:
            await self.client.close()


qdrant_client_manager = QdrantClientManager(app_config.qdrant)


async def test_collection(client, coll_name: str):
    """需求：判断集合是否存在，如果不存在则创建集合"""
    flag = await client.collection_exists(collection_name=coll_name)
    print("是否存在集合：", flag)
    if not flag:
        flag = await client.create_collection(
            collection_name=coll_name,
            vectors_config=VectorParams(
                size=app_config.qdrant.embedding_size,
                distance=Distance.COSINE
            )
        )
        print("创建集合结果：", flag)


async def test_add_points(client, coll_name: str):
    """写入若干个有关或者不相关关键词 存入向量索引库集合中"""
    keywords = [
        "苹果", "香蕉", "橘子", "芒果", "开发工程师", "Java开发工程师", "C++开发工程师", "嵌入式开发工程师",
        "机器学习", "深度学习", "数据科学", "数据处理", "数据可视化", "汽车", "小米", "大米"
    ]
    points = []
    for i, keyword in enumerate(keywords):
        vec = await embedding_client_manager.client.aembed_query(keyword)
        points.append(PointStruct(
            id=i,
            vector=vec,
            payload={"keyword": keyword}
        ))

    result: UpdateResult = await client.upsert(
        collection_name=coll_name,
        points=points
    )
    print("upsert结果：", result)


async def test_search(client, coll_name: str):
    """查询出跟 西瓜 语义相近的向量点"""
    embeded_query = await embedding_client_manager.client.aembed_query("西瓜")
    result: QueryResponse = await client.query_points(
        collection_name=coll_name,
        query=embeded_query,
        limit=10,
        score_threshold=0.6,
        query_filter=Filter(
            must=[FieldCondition(key="keyword", match=MatchValue(value="橘子"))]
        ),
    )
    payload_list = [point.payload for point in result.points]
    print("搜索结果payload：", payload_list)


async def main():
    # 初始化客户端
    qdrant_client_manager.init()
    qd_client = qdrant_client_manager.client

    embedding_client_manager.init()

    coll_name = "test"

    # 1. 先确保集合存在
    await test_collection(qd_client, coll_name)
    # 2. 写入向量数据（首次运行打开；后续测试搜索可以注释）
    await test_add_points(qd_client, coll_name)
    # 3. 执行检索
    await test_search(qd_client, coll_name)

    await qdrant_client_manager.close()


if __name__ == '__main__':
    asyncio.run(main())