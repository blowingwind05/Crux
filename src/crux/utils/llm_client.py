"""
LLM 客户端

封装 LLM 调用逻辑，支持多种模型和配置。
支持批量并行调用和自动重试。
"""

import json
import logging
from typing import Dict, Any, List, Optional, Type
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel

from src.crux.config import CruxConfig

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

# 内部状态标记，用于 batch_call_json 重试逻辑
_SUCCESS = 'S'
_FAILURE = 'F'


class LLMClient:
    """
    LLM 客户端
    
    支持:
    - OpenAI 兼容 API
    - Mock 响应（用于测试）
    - JSON 格式输出
    - 批量并行调用与自动重试
    """
    
    def __init__(self, config: Optional[CruxConfig] = None):
        self.config = config or CruxConfig()
        self._client = None
    
    @property
    def client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url
            )
        return self._client
    
    def call_json(self, prompt: str) -> Dict[str, Any]:
        """
        调用 LLM，返回原始 dict（json_object 模式）。

        Args:
            prompt: 提示词

        Returns:
            json.loads 解析后的 dict
        """
        if self.config.mock_llm:
            mock_response = self._mock_response(prompt)
            if response_object is not None and isinstance(mock_response, dict):
                return response_object.model_validate(mock_response)
            return mock_response
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.info(f"[LLM] 调用失败: {e}")
            mock_response = self._mock_response(prompt)
            if response_object is not None and isinstance(mock_response, dict):
                return response_object.model_validate(mock_response)
            return mock_response

    def call_response(self, prompt: str) -> str:
        """
        调用 LLM，返回纯文本 content（无格式约束）。

        Args:
            prompt: 提示词

        Returns:
            模型返回的原始文本字符串
        """
        if self.config.mock_llm:
            return "[mock response]"

        try:
            response = self.client.chat.completions.create(
                model=self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.info(f"[LLM] call_response 失败: {e}")
            return ""

    def batch_call_json(
        self,
        prompts: List[str],
        max_retry: int = 5,
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        并行批量调用 LLM（json_object 模式），支持自动重试。

        Args:
            prompts: 提示词列表
            max_retry: 最大重试次数
            max_workers: 并发线程数

        Returns:
            dict 列表，顺序与输入 prompts 一致。
        """
        if self.config.mock_llm:
            return [self._mock_response(p) for p in prompts]

        results_with_status: List[Optional[tuple]] = [None] * len(prompts)
        idxs_to_retry = list(range(len(prompts)))
        current_prompts = list(prompts)
        retry_count = 0

        while idxs_to_retry and retry_count < max_retry:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.call_json, current_prompts[i]): i
                    for i in range(len(current_prompts))
                }
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc=f"Batch JSON (retry {retry_count})",
                ):
                    sub_idx = futures[future]
                    idx = idxs_to_retry[sub_idx]
                    result = future.result()
                    status = _FAILURE if result is None else _SUCCESS
                    results_with_status[idx] = (result, status)

            idxs_to_retry = [
                i for i, x in enumerate(results_with_status)
                if x is None or x[1] == _FAILURE
            ]
            current_prompts = [prompts[i] for i in idxs_to_retry]
            retry_count += 1

        return [r[0] if r else None for r in results_with_status]

    def batch_call_response(
        self,
        prompts: List[str],
        max_retry: int = 5,
        max_workers: int = 4,
    ) -> List[str]:
        """
        并行批量调用 LLM（纯文本模式），支持自动重试。

        Args:
            prompts: 提示词列表
            max_retry: 最大重试次数
            max_workers: 并发线程数

        Returns:
            文本字符串列表，顺序与输入 prompts 一致。
        """
        if self.config.mock_llm:
            return ["[mock response]" for _ in prompts]

        results_with_status: List[Optional[tuple]] = [None] * len(prompts)
        idxs_to_retry = list(range(len(prompts)))
        current_prompts = list(prompts)
        retry_count = 0

        while idxs_to_retry and retry_count < max_retry:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.call_response, current_prompts[i]): i
                    for i in range(len(current_prompts))
                }
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc=f"Batch response (retry {retry_count})",
                ):
                    sub_idx = futures[future]
                    idx = idxs_to_retry[sub_idx]
                    result = future.result()
                    status = _FAILURE if not result else _SUCCESS
                    results_with_status[idx] = (result, status)

            idxs_to_retry = [
                i for i, x in enumerate(results_with_status)
                if x is None or x[1] == _FAILURE
            ]
            current_prompts = [prompts[i] for i in idxs_to_retry]
            retry_count += 1

        return [r[0] if r else "" for r in results_with_status]

    def call_object(
        self,
        prompt: str,
        response_object: Type[BaseModel],
    ) -> BaseModel:
        """
        调用 LLM，返回 Pydantic 对象（Structured Outputs 模式）。

        Args:
            prompt: 提示词
            response_object: 必须提供的 Pydantic 模型类

        Returns:
            response_object 的实例
        """
        if self.config.mock_llm:
            return response_object.model_validate(self._mock_response(prompt, response_object))

        try:
            response = self.client.chat.completions.parse(
                model=self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                response_format=response_object,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            logging.info(f"[LLM] call_object 失败: {e}")
            return response_object.model_validate(self._mock_response(prompt, response_object))

    def batch_call_object(
        self,
        prompts: List[str],
        response_object: Type[BaseModel],
        max_retry: int = 5,
        max_workers: int = 4,
    ) -> List[BaseModel]:
        """
        并行批量调用 LLM（Structured Outputs 模式），支持自动重试。

        Args:
            prompts: 提示词列表
            response_object: 必须提供的 Pydantic 模型类
            max_retry: 最大重试次数
            max_workers: 并发线程数

        Returns:
            BaseModel 实例列表，顺序与输入 prompts 一致。
        """
        if self.config.mock_llm:
            return [response_object.model_validate(self._mock_response(p, response_object)) for p in prompts]

        results_with_status: List[tuple | None] = [None] * len(prompts)
        idxs_to_retry = list(range(len(prompts)))
        current_prompts = list(prompts)
        retry_count = 0

        while idxs_to_retry and retry_count < max_retry:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.call_object, current_prompts[i], response_object): i
                    for i in range(len(current_prompts))
                }
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc=f"Batch call (retry {retry_count})",
                ):
                    sub_idx = futures[future]
                    idx = idxs_to_retry[sub_idx]
                    result = future.result()
                    status = _FAILURE if result is None else _SUCCESS
                    results_with_status[idx] = (result, status)

            idxs_to_retry = [
                i for i, x in enumerate(results_with_status)
                if x is None or x[1] == _FAILURE
            ]
            current_prompts = [prompts[i] for i in idxs_to_retry]
            retry_count += 1

        return [r[0] if r else None for r in results_with_status]

    def _mock_response(self, prompt: str, response_object: Optional[Type[BaseModel]] = None) -> Dict[str, Any]:
        """
        根据 response_object 类型返回对应的 mock 数据 dict。
        调用方会用 response_object.model_validate() 将其转为 Pydantic 实例。
        """
        if response_object is None:
            return {}

        name = response_object.__name__

        # ── Stage 1a: CognitiveState ───────────────────────────────────
        if name == "CognitiveState":
            return {
                "cognitive_mode": "exploratory",
                "logical_dependency": "independent_parallel",
            }

        # ── Stage 1b: Constraints ──────────────────────────────────────
        if name == "Constraints":
            return {
                "structured_metadata": [],
                "unstructured_content_patterns": [],
            }

        # ── Stage 2: AgentPlan ─────────────────────────────────────────
        if name == "AgentPlan":
            return {
                "facets": [
                    {
                        "facet_id": "F1",
                        "description": "Overview and background of the topic",
                        "dependency": None,
                        "rubric": {
                            "tolerance_level": "high",
                            "quality_preference": ["survey papers", "review articles"],
                            "content_requirements": ["provides general overview"],
                        },
                    },
                    {
                        "facet_id": "F2",
                        "description": "Key methods and techniques",
                        "dependency": None,
                        "rubric": {
                            "tolerance_level": "medium",
                            "quality_preference": ["research papers", "technical reports"],
                            "content_requirements": ["describes specific methods or algorithms"],
                        },
                    },
                ],
                "criteria": {
                    "metric_type": "coverage",
                    "threshold_description": "All facets have at least one high or medium relevance document",
                    "specific_conditions": [
                        "F1 has at least one overview document",
                        "F2 has at least one method-focused document",
                    ],
                },
            }

        # ── Stage 3: FacetExpansion ────────────────────────────────────
        if name == "FacetExpansion":
            # Extract facet_id from prompt if possible
            facet_id = "F1"
            for line in prompt.splitlines():
                if "Facet ID:" in line:
                    facet_id = line.split("Facet ID:")[-1].strip()
                    break
            return {
                "facet_id": facet_id,
                "facet_query": f"overview and introduction to the topic for {facet_id}",
                "sparse_keywords": ["information retrieval", "RAG", "agentic search"],
                "hypothetical_document": (
                    "This paper provides a comprehensive survey of retrieval-augmented generation methods, "
                    "covering key architectures, datasets, and benchmarks in the field."
                ),
            }

        # ── Judge: FacetJudgments ──────────────────────────────────────
        if name == "FacetJudgments":
            # Extract doc_ids from prompt
            import re
            doc_ids = re.findall(r"doc_id:\s*(\S+)", prompt)
            if not doc_ids:
                doc_ids = ["doc_mock_1"]
            return {
                "judgments": [
                    {
                        "doc_id": did,
                        "summary": "A relevant paper discussing information retrieval techniques.",
                        "relevance_level": "medium",
                        "reason": "The document covers the facet topic at a general level.",
                    }
                    for did in doc_ids
                ]
            }

        # ── Strategy: FacetSufficiencyResult ──────────────────────────
        if name == "FacetSufficiencyResult":
            # Extract facet_ids from the facets_evidence_block section
            import re
            facet_ids = re.findall(r"###\s*Facet\s+(\w+):", prompt)
            if not facet_ids:
                facet_ids = ["F1"]
            return {
                "overall_sufficient": True,
                "facets": [
                    {
                        "facet_id": fid,
                        "satisfied": True,
                        "reason": "Sufficient evidence collected for this facet.",
                    }
                    for fid in facet_ids
                ],
            }

        # ── Default fallback ───────────────────────────────────────────
        return {}


class APIEmbeddingModel:
    """API 嵌入模型

    通过 OpenAI 兼容接口调用远程 Embedding 服务。
    """

    def __init__(self, model_name: str, api_key: str, base_url: str, max_retries: int = 3):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.max_retries = max_retries

    def encode(self, sentences, batch_size=32, convert_to_tensor=False, normalize_embeddings=True, show_progress_bar=False):
        import numpy as np

        if isinstance(sentences, str):
            sentences = [sentences]

        all_embeddings = []
        for i in tqdm(range(0, len(sentences), batch_size), disable=not show_progress_bar, desc="API Embeddings"):
            batch = sentences[i : i + batch_size]
            for attempt in range(self.max_retries):
                try:
                    response = self.client.embeddings.create(
                        input=batch,
                        model=self.model_name,
                        timeout=60
                    )
                    embeddings = [data.embedding for data in response.data]
                    all_embeddings.extend(embeddings)
                    break
                except Exception as e:
                    print(f"Embedding API Error (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        print("Max retries reached, using zero vectors as fallback")
                        all_embeddings.extend([[0.0] * 1536 for _ in batch])
                    else:
                        import time
                        time.sleep(1)

        all_embeddings = np.array(all_embeddings)

        if len(all_embeddings) == 0:
            return all_embeddings

        if normalize_embeddings:
            norms = np.linalg.norm(all_embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1e-10
            all_embeddings = all_embeddings / norms

        return all_embeddings


class APIReranker:
    """API 重排序模型

    通过 HTTP 接口调用远程 Rerank 服务。
    """

    def __init__(self, model_name: str, api_key: str, base_url: str, max_retries: int = 3):
        import requests as _requests  # noqa: F811
        self.model_name = model_name
        self.api_key = api_key
        self.url = base_url.rstrip("/") + "/rerank" if "rerank" not in base_url else base_url
        self.url = self.url.replace("//rerank", "/rerank")
        self.max_retries = max_retries

    def predict(self, sentences, batch_size=8, show_progress_bar=False):
        import json as _json
        import numpy as np
        import requests

        all_scores = []

        for i in tqdm(range(0, len(sentences), batch_size), disable=not show_progress_bar, desc="API Rerank"):
            batch = sentences[i : i + batch_size]

            if not batch:
                continue

            current_query = batch[0][0]
            current_documents = [pair[1] for pair in batch]

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

            for attempt in range(self.max_retries):
                try:
                    response = requests.post(self.url, headers=headers, data=_json.dumps(payload), timeout=60, verify=False)
                    response.raise_for_status()
                    result = response.json()

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
                    break
                except Exception as e:
                    print(f"API Rerank Request Failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        print("Max retries reached, using zero scores as fallback")
                        all_scores.extend([0.0] * len(batch))
                    else:
                        import time
                        time.sleep(1)

        return np.array(all_scores)
