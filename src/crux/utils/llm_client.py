"""
LLM 客户端

封装 OpenAI 兼容 API 的调用逻辑，支持 JSON 格式输出和 Mock 模式。
"""

import json
from typing import Optional, Dict, Any
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.crux.utils.constant import SUCCESS, FAILURE
from src.crux.config import CruxConfig

import logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

class LLMClient:
    """LLM 客户端，支持 OpenAI 兼容 API 和 Mock 测试模式"""

    def __init__(self, config: Optional[CruxConfig] = None):
        """初始化客户端，支持传入自定义配置"""
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

    def call_json(self, prompt: str, model: Optional[str] = None) -> tuple[Dict[str, Any], str]:
        """
        调用 LLM 并返回 JSON 结果

        Args:
            prompt: 提示词
            model: 可选的模型名称，默认使用配置中的模型

        Returns:
            (解析后的 JSON 对象, 状态码)
            - 状态码 SUCCESS: 调用成功
            - 状态码 FAILURE: 调用失败（返回 mock 数据作为 fallback）
        """
        if self.config.mock_llm:
            return (self._mock_response(prompt), SUCCESS)

        try:
            response = self.client.chat.completions.create(
                model=model or self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return (json.loads(content), SUCCESS)
        except Exception as e:
            logging.info(f"[LLM] 调用失败: {e}")
            return (self._mock_response(prompt), FAILURE)

    def batch_call_json(
        self,
        prompts: list[str],
        model: Optional[str] = None,
        max_retry: int = 5,
        max_workers: int = 4
    ) -> list[tuple[Dict[str, Any], str]]:
        """
        批量调用 LLM 并返回 JSON 结果

        Args:
            prompts: 提示词列表
            model: 可选的模型名称
            max_retry: 最大重试次数
            max_workers: 并发线程数

        Returns:
            结果列表，顺序与输入 prompts 一致。
            每个元素为 (解析后的 JSON 对象, 状态码) 元组。
        """
        if self.config.mock_llm:
            return [(self._mock_response(prompt), SUCCESS) for prompt in prompts]

        results = [None] * len(prompts)
        idxs_to_retry = list(range(len(prompts)))
        current_prompts = prompts
        retry_count = 0

        while idxs_to_retry and retry_count < max_retry:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.call_json, current_prompts[i], model): i
                    for i in range(len(current_prompts))
                }
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc=f'Processing (retry {retry_count})'
                ):
                    sub_idx = futures[future]
                    idx = idxs_to_retry[sub_idx]
                    results[idx] = future.result()

            # 收集失败的请求索引，准备重试
            idxs_to_retry = [i for i, x in enumerate(results) if x and x[1] == FAILURE]
            current_prompts = [prompts[i] for i in idxs_to_retry]
            retry_count += 1

        return results

    def _mock_response(self, prompt: str) -> Dict[str, Any]:
        """
        Mock 响应，用于测试环境

        根据 prompt 中的关键字返回对应的 mock 数据。

        匹配规则:
        - "Strategy Planner" 或 "信息覆盖" -> Gap analysis 响应
        - "Critical Judge" 或 "研判" -> Adjudication 响应
        - "Intent Parsing" 或 "意图解析" -> Intent parsing 响应
        - 其他 -> 默认响应
        """
        # Gap analysis
        if "Strategy Planner" in prompt or "信息覆盖" in prompt:
            return {
                "status": "sufficient",
                "missing_info": None
            }

        # Adjudication
        if "Critical Judge" in prompt or "研判" in prompt:
            return {
                "is_relevant": True,
                "evidence": "这是一篇关于信息检索的重要论文。",
                "reason": "内容与查询直接相关"
            }

        # Intent parsing
        if "Intent Parsing" in prompt or "意图解析" in prompt:
            return {
                "user_goal": "FACTUAL",
                "constraints": {
                    "structured_metadata": [
                        {"field": "category", "operator": "in", "value": ["cs.IR", "cs.CL", "cs.AI"]}
                    ]
                },
                "keywords_bm25": ["信息检索", "RAG", "检索增强"],
                "queries_vector": ["检索增强生成技术研究", "信息检索智能体"],
                "rubric": "文档必须与信息检索或 RAG 技术相关",
                "missing_info_gap": None
            }

        # Default
        return {
            "user_goal": "FACTUAL",
            "constraints": {"structured_metadata": []},
            "keywords_bm25": [],
            "queries_vector": [],
            "rubric": "相关内容",
            "missing_info_gap": None
        }
