"""
意图理解节点 (Understanding Node)

负责人: [待分配]

功能:
- 解析用户自然语言查询
- 生成结构化 IntentObject
- 识别认知策略、约束条件、信息面
"""

import datetime
import json
from typing import Dict, Any

from src.crux.context.builder import ContextBuilder
from src.crux.state import IntentObject
from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient


class UnderstandingNode(BaseNode):
    """
    Schema 感知的意图理解节点
    
    将用户自然语言查询转化为机器可执行的结构化 IntentObject。
    """

    name = "understand"
    description = "解析用户意图，生成结构化查询对象"

    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = LLMClient(config)
        self.context_builder = ContextBuilder(config)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户查询，生成意图对象
        
        Args:
            state: 包含 user_query 的状态
            
        Returns:
            包含 intent, search_iteration, verified_evidence 的更新
        """
        self.log("正在解析意图...")

        query = state["user_query"]
        current_time = datetime.datetime.now().strftime("%Y-%m-%d")

        # 使用 ContextBuilder 构建 prompt (schema 从 config 加载)
        prompt = self.context_builder.build_intent_prompt(
            query=query,
            current_date=current_time
        )

        # 调用 LLM 生成结构化意图
        intent_json = self.llm_client.call_json(prompt)

        # 使用 Pydantic 校验和转换
        try:
            intent_obj = IntentObject(**intent_json)
            self.log(f"解析结果: {json.dumps(intent_json, ensure_ascii=False, indent=2)}")
            return {
                "intent": intent_obj.model_dump(),
                "intent_object": intent_obj.model_dump(),  # 兼容前端
                "search_iteration": 0,
                "verified_evidence": []  # 初始化证据列表
            }
        except Exception as e:
            self.log(f"解析失败，使用默认意图: {e}", level="WARN")
            # 返回一个默认的意图结构
            default_intent = IntentObject()
            return {
                "intent": default_intent.model_dump(),
                "intent_object": default_intent.model_dump(),
                "search_iteration": 0,
                "verified_evidence": []
            }
