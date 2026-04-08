"""
Judge 节点 (Judge Node)

Per-Facet 研判流程：
  1. 按 facet_id 对 candidate_docs 分组
  2. 从 intent["agent_plan"]["facets"] 取每个 Facet 的 RelevanceRubric
  3. 为每个 Facet 构建研判 Prompt，并行 batch_call_object → FacetJudgments
  4. 将研判结果展开写入 verified_evidence 和 rejected_docs
"""

from typing import Dict, Any, List

from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient
from src.crux.modules.judge.prompts import build_facet_judge_prompt
from src.crux.state import FacetJudgments


class JudgeNode(BaseNode):
    """
    Per-Facet 研判节点

    对每个 Facet 的候选文档列表，根据该 Facet 的 RelevanceRubric，
    并行批量调用 LLM，输出每篇文档的摘要、相关性等级和判断理由。
    """

    name = "judge"
    name_cn = "相关性研判"
    description = "Per-Facet 研判候选文档，输出相关性等级和理由"

    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = LLMClient(config)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.reset_logger()

        intent = state["intent"]
        user_query: str = state.get("user_query", "")
        all_candidates: List[Dict] = state.get("candidate_docs", [])

        # ── 过滤已研判文档（seen_doc_ids 跨迭代累积）───────────────────
        seen: set = state.get("seen_doc_ids", set())
        candidate_docs = [
            d for d in all_candidates
            if (d.get("id") or d.get("arxiv_id", "")) not in seen
        ]
        skipped = len(all_candidates) - len(candidate_docs)
        if skipped:
            self.log(f"跳过已研判文档: {skipped} 篇")

        # ── 1. 按 facet_id 分组 ──────────────────────────────────────────
        facet_doc_map: Dict[str, List[Dict]] = {}
        for doc in candidate_docs:
            fid = doc.get("facet_id", "unknown")
            facet_doc_map.setdefault(fid, []).append(doc)

        self.log(f"共 {len(facet_doc_map)} 个 Facet，{len(candidate_docs)} 篇候选文档")

        # ── 2. 取每个 Facet 的 Rubric ────────────────────────────────────
        facets_raw: List[Dict] = intent.get("agent_plan", {}).get("facets", [])
        facet_meta: Dict[str, Dict] = {f["facet_id"]: f for f in facets_raw}

        # ── 3. 构建研判 Prompts（按 Facet 顺序） ─────────────────────────
        ordered_facet_ids = list(facet_doc_map.keys())
        prompts: List[str] = []

        for fid in ordered_facet_ids:
            docs = facet_doc_map[fid]
            meta = facet_meta.get(fid, {})
            rubric = meta.get("rubric", {})

            documents_text = self._format_documents(docs)

            prompt = build_facet_judge_prompt(
                user_query=user_query,
                facet_id=fid,
                facet_description=meta.get("description", ""),
                tolerance_level=rubric.get("tolerance_level", "medium"),
                quality_preference=rubric.get("quality_preference", []),
                content_requirements=rubric.get("content_requirements", []),
                documents=documents_text,
            )
            prompts.append(prompt)

        # ── 4. 并行批量研判 ──────────────────────────────────────────────
        judgments_list: List[FacetJudgments] = self.llm_client.batch_call_object(
            prompts=prompts,
            response_object=FacetJudgments,
            max_workers=max(len(prompts), 1),
        )

        # ── 5. 展开结果 ──────────────────────────────────────────────────
        verified_evidence: List[Dict] = []
        rejected_docs: List[Dict] = []

        for fid, facet_judgments in zip(ordered_facet_ids, judgments_list):
            if facet_judgments is None:
                self.log(f"Facet {fid} 研判失败，跳过", level="WARN")
                continue

            docs = facet_doc_map[fid]
            doc_by_id = {
                (d.get("id") or d.get("arxiv_id", f"doc_{i}")): d
                for i, d in enumerate(docs)
            }

            for jdg in facet_judgments.judgments:
                doc = doc_by_id.get(jdg.doc_id, {})
                if jdg.relevance_level in ("high", "medium"):
                    verified_evidence.append({
                        "doc_id": jdg.doc_id,
                        "facet_id": fid,
                        "summary": jdg.summary,
                        "relevance_level": jdg.relevance_level,
                        "reason": jdg.reason,
                        "title": doc.get("title", ""),
                        "abstract": doc.get("abstract", ""),
                        "metadata": {
                            "year": doc.get("year") or doc.get("metadata", {}).get("date", ""),
                            "authors": doc.get("authors", []),
                            "url": doc.get("arxiv_url", ""),
                        },
                    })
                else:
                    rejected_docs.append({
                        "doc_id": jdg.doc_id,
                        "facet_id": fid,
                        "relevance_level": jdg.relevance_level,
                        "reason": jdg.reason,
                        "title": doc.get("title", ""),
                    })

        self.log(
            f"研判完成: 采纳 {len(verified_evidence)} 篇，拒绝 {len(rejected_docs)} 篇",
            level="INFO",
        )

        # 记录本轮所有已研判文档 ID（无论接受/拒绝）→ 下次迭代跳过
        current_ids = {d.get("id") or d.get("arxiv_id", "") for d in candidate_docs}

        return self.build_result({
            "verified_evidence": verified_evidence,
            "rejected_docs": rejected_docs,
            "seen_doc_ids": current_ids,
        })

    def _format_documents(self, docs: List[Dict]) -> str:
        """将文档列表格式化为 Prompt 中的编号文档块"""
        lines = []
        for i, doc in enumerate(docs):
            doc_id = doc.get("id") or doc.get("arxiv_id", f"doc_{i}")
            title = doc.get("title", "（无标题）")
            abstract = doc.get("abstract", "（无摘要）")
            lines.append(f"[{i + 1}] doc_id: {doc_id}\n    Title: {title}\n    Abstract: {abstract}")
        return "\n\n".join(lines)
