import json
from urllib.request import Request, urlopen

from langchain_core.embeddings import Embeddings


class QwenVLEmbeddings(Embeddings):
    def __init__(self, model: str, api_key: str):
        if model != "qwen3-vl-embedding":
            raise ValueError("请将 embedding_model_name 配置为 qwen3-vl-embedding")
        self.model = model
        self.api_key = api_key

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        batch_size = 10
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            payload = {
                "model": self.model,
                "input": {"contents": [{"text": text} for text in batch]},
                "parameters": {"enable_fusion": False},
            }
            request = Request(
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/"
                "multimodal-embedding/multimodal-embedding",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urlopen(request, timeout=30) as response:
                result = json.load(response)

            items = sorted(result["output"]["embeddings"], key=lambda item: item["index"])
            if [item["index"] for item in items] != list(range(len(batch))):
                raise RuntimeError("百炼返回的向量与输入文本不匹配")
            vectors.extend(item["embedding"] for item in items)

        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
