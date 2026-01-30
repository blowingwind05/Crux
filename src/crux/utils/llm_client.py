"""
LLM 客户端

封装 LLM 调用逻辑，支持多种模型和配置。
"""

import json
from typing import Optional, Dict, Any
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.crux.config import CruxConfig

import logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

class LLMClient:
    """
    LLM 客户端
    
    支持:
    - OpenAI 兼容 API
    - Mock 响应（用于测试）
    - JSON 格式输出
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
        
        return self._single_call(prompt, model)

    def _single_call(self, prompt: str, model: Optional[str] = None) -> tuple[Dict[str, Any], str]:
        """真实 LLM 调用"""
        try:
            response = self.client.chat.completions.create(
                model=model or self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return (json.loads(content), 'S')
        except Exception as e:
            logging.info(f"[LLM] 调用失败: {e}")
            return (self._mock_response(prompt), 'F')

    def _batch_call(self, prompts: list[str], model: Optional[str] = None, max_retry: int = 5, max_workers: int = 16) -> list[tuple[Dict[str, Any], str]]:
        """真实 LLM 批量调用"""
        results = [None] * len(prompts)
        idxs_to_retry = list(range(len(prompts)))
        current_prompts = prompts
        retry_count = 0

        while idxs_to_retry and retry_count < max_retry:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._single_call, current_prompts[i], model): i
                    for i in range(len(current_prompts))
                }
                for future in tqdm(as_completed(futures), total=len(futures), desc=f'Processing (retry {retry_count})'):
                    sub_idx = futures[future]
                    idx = idxs_to_retry[sub_idx]
                    results[idx] = future.result()

            idxs_to_retry = [i for i, x in enumerate(results) if x[1] == 'F']
            current_prompts = [prompts[i] for i in idxs_to_retry]
            retry_count += 1

        return results

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
