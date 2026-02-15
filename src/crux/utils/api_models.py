"""
API 模型工具模块

提供嵌入模型和重排序模型的 API 调用功能。
"""

import json
import numpy as np
import requests
from openai import OpenAI
from tqdm import tqdm
import torch
import yaml
from src.crux.utils.retriever_config import RetrieverConfig

CONFIG = RetrieverConfig(r"src\crux\utils\config.yaml").config_dict

class APIEmbeddingModel:
    def __init__(self, model_name, api_key, base_url):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def encode(self, sentences, batch_size=32, convert_to_tensor=False, normalize_embeddings=True, show_progress_bar=False):
        if isinstance(sentences, str):
            sentences = [sentences]

        all_embeddings = []
        for i in tqdm(range(0, len(sentences), batch_size), disable=not show_progress_bar, desc="API Embeddings"):
            batch = sentences[i : i + batch_size]
            # 注意：OpenAI Embedding 接口有 token 限制，如果 batch 过大或文本过长可能会报错
            max_retries = CONFIG["max_retries"]
            for attempt in range(max_retries):
                try:
                    # 添加超时设置，避免默认超时太短
                    response = self.client.embeddings.create(
                        input=batch,
                        model=self.model_name,
                        timeout=60 # 设置60秒超时
                    )
                    embeddings = [data.embedding for data in response.data]
                    all_embeddings.extend(embeddings)
                    break  # 成功则跳出重试循环
                except Exception as e:
                    print(f"Embedding API Error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        # 最后一次重试失败，填充零向量作为 fallback
                        print("Max retries reached, using zero vectors as fallback")
                        all_embeddings.extend([[0.0] * 1536 for _ in batch])  # 使用列表而不是numpy数组
                    else:
                        # 等待一秒后重试
                        import time
                        time.sleep(1)

        all_embeddings = np.array(all_embeddings)

        if len(all_embeddings) == 0:
            if convert_to_tensor:
                return torch.empty(0)
            return all_embeddings

        if normalize_embeddings:
            norms = np.linalg.norm(all_embeddings, axis=1, keepdims=True)
            # 避免除以 0
            norms[norms == 0] = 1e-10
            all_embeddings = all_embeddings / norms

        if convert_to_tensor:
            return torch.tensor(all_embeddings)
        return all_embeddings


class APIReranker:
    def __init__(self, model_name, api_key, base_url):
        self.model_name = model_name
        self.api_key = api_key
        # 构造 rerank url: .../v1/ -> .../v1/rerank
        self.url = base_url.rstrip("/") + "/rerank" if "rerank" not in base_url else base_url
        # 修正可能出现的双 slash 问题
        self.url = self.url.replace("//rerank", "/rerank")

    def predict(self, sentences, batch_size=8, show_progress_bar=False):
        # sentences 是 [ [query, doc], [query, doc], ... ]
        all_scores = []

        # 按 batch_size 切分
        for i in tqdm(range(0, len(sentences), batch_size), disable=not show_progress_bar, desc="API Rerank"):
            batch = sentences[i : i + batch_size]

            if not batch:
                continue

            # 提取 query 和 documents
            current_query = batch[0][0]
            current_documents = [pair[1] for pair in batch]

            # 构造 Payload
            payload = {
                "model": self.model_name,
                "query": current_query,
                "documents": current_documents,
                "top_n": len(batch),
                "return_documents": False
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}" if not self.api_key.startswith("Bearer") else self.api_key,
                "Content-Type": "application/json"
            }

            max_retries = CONFIG["max_retries"]
            for attempt in range(max_retries):
                try:
                    # ！！！添加 verify=False 以解决 SSLEOFError！！！
                    # SSLEOFError 通常是因为本地网络环境与服务器的 SSL 握手异常导致的
                    response = requests.post(self.url, headers=headers, data=json.dumps(payload), timeout=60, verify=False)
                    response.raise_for_status()
                    result = response.json()

                    # 解析 scores
                    # 期望格式: "results": [ { "index": 0, "relevance_score": 0.97 }, ... ]
                    if "results" in result:
                        batch_scores = [0.0] * len(batch)
                        for item in result["results"]:
                            idx = item["index"]
                            if idx < len(batch_scores):
                                batch_scores[idx] = item["relevance_score"]
                        all_scores.extend(batch_scores)
                    else:
                        print(f"Warning: 'results' key not found. Raw: {str(result)[:100]}")
                        all_scores.extend([0.0] * len(batch))
                    break  # 成功则跳出重试循环
                except Exception as e:
                    print(f"API Rerank Request Failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        # 最后一次重试失败，Fallback: 全0分
                        print("Max retries reached, using zero scores as fallback")
                        all_scores.extend([0.0] * len(batch))
                    else:
                        # 等待一秒后重试
                        import time
                        time.sleep(1)

        return np.array(all_scores)