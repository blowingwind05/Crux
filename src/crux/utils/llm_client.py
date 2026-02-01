"""
LLM 客户端

封装 LLM 调用逻辑，支持多种模型和配置。
支持批量并行调用和自动重试。
"""

import json
import logging
from typing import Optional, Dict, Any, List
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    def call_json(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        调用 LLM 并返回 JSON 结果
        
        Args:
            prompt: 提示词
            model: 可选的模型名称
            
        Returns:
            解析后的 JSON 对象
        """
        if self.config.mock_llm:
            return self._mock_response(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=model or self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logging.info(f"[LLM] 调用失败: {e}")
            return self._mock_response(prompt)

    def _call_json_with_status(self, prompt: str, model: Optional[str] = None) -> tuple:
        """
        内部方法：调用 LLM 并返回 (结果, 状态) 元组
        
        用于 batch_call_json 的重试逻辑
        """
        if self.config.mock_llm:
            return (self._mock_response(prompt), _SUCCESS)

        try:
            response = self.client.chat.completions.create(
                model=model or self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return (json.loads(content), _SUCCESS)
        except Exception as e:
            logging.info(f"[LLM] 调用失败: {e}")
            return (self._mock_response(prompt), _FAILURE)

    def batch_call_json(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        max_retry: int = 5,
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """
        批量调用 LLM 并返回 JSON 结果

        支持并行调用和自动重试失败的请求。

        Args:
            prompts: 提示词列表
            model: 可选的模型名称
            max_retry: 最大重试次数
            max_workers: 并发线程数

        Returns:
            结果列表，顺序与输入 prompts 一致。
            每个元素为解析后的 JSON 对象。
        """
        if self.config.mock_llm:
            return [self._mock_response(prompt) for prompt in prompts]

        # 内部使用带状态的结果进行重试跟踪
        results_with_status = [None] * len(prompts)
        idxs_to_retry = list(range(len(prompts)))
        current_prompts = prompts
        retry_count = 0

        while idxs_to_retry and retry_count < max_retry:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._call_json_with_status, current_prompts[i], model): i
                    for i in range(len(current_prompts))
                }
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc=f'Processing (retry {retry_count})'
                ):
                    sub_idx = futures[future]
                    idx = idxs_to_retry[sub_idx]
                    results_with_status[idx] = future.result()

            # 收集失败的请求索引，准备重试
            idxs_to_retry = [i for i, x in enumerate(results_with_status) if x and x[1] == _FAILURE]
            current_prompts = [prompts[i] for i in idxs_to_retry]
            retry_count += 1

        # 提取结果（去除状态标记）
        return [r[0] for r in results_with_status]
    
    def _mock_response(self, prompt: str) -> Dict[str, Any]:
        """
        Mock 响应 - 用于测试
        
        根据 prompt 内容返回不同的 mock 数据
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
                "relevance": "Perfectly Relevant",
                "evidence": ["这是一篇关于信息检索的重要论文。", "提出了新颖的检索增强方法。"],
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
