"""
意图理解节点 (Understanding Node)

负责人: [待分配]

功能:
- 解析用户自然语言查询
- 生成结构化 IntentObject
- 识别认知策略、约束条件、信息面
"""

import json
import datetime
from typing import Dict, Any

from src.crux.nodes.base import BaseNode
from src.crux.core.state import AgentState, IntentObject
from src.crux.llm.client import LLMClient
from src.crux.prompts.templates import get_intent_parsing_prompt
from src.crux.context.builder import ContextBuilder


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
    
    def process(self, state: AgentState) -> Dict[str, Any]:
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
        schema_type = state.get("schema_type", self.config.schema_type)
        
        # 使用 ContextBuilder 构建 prompt
        prompt = self.context_builder.build_intent_prompt(
            query=query,
            current_date=current_time,
            schema_type=schema_type
        )
        
        # 调用 LLM 生成结构化意图
        intent_json = self.llm_client.call_json(prompt)
        
        # 使用 Pydantic 校验和转换
        try:
            intent_obj = IntentObject(**intent_json)
            self.log(f"解析结果: {json.dumps(intent_json, ensure_ascii=False, indent=2)}")
            return {
                "intent": intent_obj.model_dump(),
                "search_iteration": 0,
                "verified_evidence": []  # 初始化证据列表
            }
        except Exception as e:
            self.log(f"解析失败，使用默认意图: {e}", level="WARN")
            # 返回一个默认的意图结构
            default_intent = IntentObject(
                user_goal="FACTUAL",
                constraints={"structured_metadata": []},
                keywords_bm25=[],
                queries_vector=[],
                rubric="文档内容相关即可",
                missing_info_gap=None
            )
            return {
                "intent": default_intent.model_dump(),
                "search_iteration": 0,
                "verified_evidence": []
            }
