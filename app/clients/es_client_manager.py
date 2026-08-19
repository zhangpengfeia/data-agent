import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    def __init__(self, config: ESConfig):
        self.config = config
        self.client: Optional[AsyncElasticsearch] = None

    def _get_url(self):
        return f"{self.config.scheme}://{self.config.host}:{self.config.port}"

    def init(self):
        # 腾讯云 ES：HTTPS + Basic Auth + 自签名证书处理
        kwargs = {
            "hosts": self._get_url(),
        }
        # 用户名/密码鉴权（不填则跳过，兼容本地裸跑的 ES）
        if self.config.user:
            kwargs["basic_auth"] = (self.config.user, self.config.password)
        # HTTPS 证书校验
        if self.config.scheme == "https":
            kwargs["verify_certs"] = self.config.verify_certs
            # 配置了 CA 证书则按证书校验
            if self.config.ca_certs:
                kwargs["ca_certs"] = self.config.ca_certs
                kwargs["verify_certs"] = True
            # 关闭校验时一并关闭告警，避免刷屏
            if not kwargs["verify_certs"]:
                kwargs["ssl_show_warn"] = False
        self.client = AsyncElasticsearch(**kwargs)

    async def close(self):
        if self.client:
            await self.client.close()


es_client_manager = ESClientManager(app_config.es)

if __name__ == '__main__':
    es_client_manager.init()
    client = es_client_manager.client

    idx_name = "test"


    async def test_index():
        """采用显示映射创建索引库"""
        if not await client.indices.exists(index=idx_name):
            resp = await client.indices.create(
                index=idx_name,
                mappings={
                    "dynamic": False,
                    "properties": {
                        "id": {
                            "type": "long"
                        },
                        "name": {
                            "type": "text",
                            "analyzer": "ik_max_word"
                        },
                        "brand": {
                            "type": "keyword"
                        },
                        "image": {
                            "type": "keyword",
                            "index": False
                        },
                        "price": {
                            "type": "float"
                        }
                    }
                }
            )
            print(resp)
        await es_client_manager.close()


    # asyncio.run(test_index())

    async def test_doc():
        await client.index(
            index=idx_name,
            document={
                "id": 3,
                "name": "小米su7 ultra长续航版本",
                "brand": "小米汽车",
                "image": "www.xxx.xxx/xm.png",
                "price": 406000
            }
        )

        await client.bulk(operations=[
            {
                "index": {
                    "_index": idx_name
                }
            },
            {
                "id": 1,
                "name": "小米17ProMax 1T 雪花白 8GB+16GB",
                "brand": "小米",
                "image": "www.xxx.xxx/xm.png",
                "price": 5000
            },
            {
                "index": {
                    "_index": idx_name
                }
            },
            {
                "id": 2,
                "name": "小米17ProMax 1T 冰晶蓝 8GB+16GB",
                "brand": "小米",
                "image": "www.xxx.xxx/xm.png",
                "price": 6000
            }
        ])
        await es_client_manager.close()
    asyncio.run(test_doc())

