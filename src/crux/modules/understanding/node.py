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
    name_cn = "意图理解"
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
        self.reset_logger()
        
        query = state["user_query"]
        current_time = datetime.datetime.now().strftime("%Y-%m-%d")

        self.log("正在解析用户意图...")
        self.log(f"用户查询: {query}", details={"query": query})

        # 使用 ContextBuilder 构建 prompt (schema 从 config 加载)
        self.log("构建意图解析 Prompt...")
        prompt = self.context_builder.build_intent_prompt(
            query=query,
            current_date=current_time
        )

        # 调用 LLM 生成结构化意图
        self.log("调用 LLM 进行意图解析...", details={"model": self.config.llm.model})
        intent_json = self.llm_client.call_json(prompt)

        # 使用 Pydantic 校验和转换
        try:
            intent_obj = IntentObject(**intent_json)
            
            # 记录解析结果
            cognitive = intent_obj.cognitive_strategy
            self.log(f"识别用户目标: {cognitive.user_goal}")
            self.log(f"推理拓扑: {cognitive.reasoning_topology}")
            
            # 记录约束条件
            constraints = intent_obj.constraints
            structured_count = len(constraints.get("structured_metadata", []))
            pattern_count = len(constraints.get("unstructured_content_patterns", []))
            self.log(f"提取约束条件: {structured_count} 个结构化约束, {pattern_count} 个内容模式")
            
            # 记录信息面
            facets = intent_obj.information_facets
            if facets:
                self.log(f"识别信息面: {len(facets)} 个", details={
                    "facets": [f.facet_id for f in facets]
                })
            
            # 记录检索策略
            retrieval = intent_obj.retrieval_execution
            sparse_count = len(retrieval.sparse_keywords)
            dense_count = len(retrieval.dense_queries)
            self.log(f"生成检索策略: {sparse_count} 个关键词, {dense_count} 个语义查询")
            
            self.log("意图解析完成", level="INFO")
            
            return self.build_result({
                "intent": intent_obj.model_dump(),
                "intent_object": intent_obj.model_dump(),  # 兼容前端
                "search_iteration": 0,
                "verified_evidence": []  # 初始化证据列表
            })
            
        except Exception as e:
            self.log(f"解析失败，使用默认意图: {e}", level="WARN")
            # 返回一个默认的意图结构
            default_intent = IntentObject()
            return self.build_result({
                "intent": default_intent.model_dump(),
                "intent_object": default_intent.model_dump(),
                "search_iteration": 0,
                "verified_evidence": []
            })
