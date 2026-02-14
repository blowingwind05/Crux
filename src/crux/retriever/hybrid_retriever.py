import os
import bm25s
import gc
import numpy as np
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from src.crux.utils.api_models import APIEmbeddingModel, APIReranker
from src.crux.utils.retriever_config import RetrieverConfig

CONFIG = RetrieverConfig(r"src\crux\utils\config.yaml").config_dict

class HybridRetriever:
    def __init__(self,  df_papers):
        self.df_papers = df_papers
        if CONFIG.get("use_api_emb"):
            print(f"Using API for embeddings ({CONFIG['model_emb']})")
            self.model_emb = APIEmbeddingModel(
                model_name=CONFIG["model_emb"],
                api_key=CONFIG["api_key_emb"],
                base_url=CONFIG["base_url_emb"]
            )
        else:
            print(f"Using Local Model for embeddings ({CONFIG['model_emb']})")
            self.model_emb = SentenceTransformer(
            CONFIG["model_emb"],
            device=CONFIG["device"],
            model_kwargs={"torch_dtype": torch.float16 if "cuda" in str(CONFIG["device"]) else torch.float32},
            )
        if CONFIG.get("use_api_rerank"):
            print(f"Using API Reranker ({CONFIG['model_rerank']})...")
            self.reranker = APIReranker(
                model_name=CONFIG["model_rerank"],
                api_key=CONFIG["api_key_rerank"],
                base_url=CONFIG["base_url_rerank"]
            )
        else:
            print(f"Loading local Reranker ({CONFIG['model_rerank']})...")
            self.reranker = CrossEncoder(
                CONFIG["model_rerank"],
                device=CONFIG["device"],
                max_length=512,
                automodel_args={"dtype": torch.float16 if "cuda" in str(CONFIG["device"]) else torch.float32},
            )
    
    def get_papers_bm25(self):
        path = CONFIG["papers_index_save_path"]
        if os.path.exists(path):
            print("Loading existing BM25 index...")
            self.papers_bm25 = bm25s.BM25.load(path)
        else:
            def tokenize_corpus(texts):
                return bm25s.tokenize([str(t).lower()[:2000] for t in texts], stopwords="en")
            papers_tokens = tokenize_corpus(self.df_papers["combined_text"].tolist())
            papers_bm25 = bm25s.BM25()
            papers_bm25.index(papers_tokens)
            self.papers_bm25 = papers_bm25
            print("Saving BM25 index...")
            os.makedirs(path, exist_ok=True)
            self.papers_bm25.save(path)
            del papers_tokens
            gc.collect()

    def get_papers_embeddings(self):
        print("Preparing papers embeddings...")
        path = os.path.join(CONFIG["papers_embeddings_save_path"], "embeddings.npy")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            print("Loading existing papers embeddings...")
            self.papers_embeddings = np.load(path)
        else:
            truncated_papers = [str(t)[:2000] for t in self.df_papers["combined_text"].tolist()]
            papers_embeddings = self.model_emb.encode(
                truncated_papers,
                batch_size=CONFIG["batch_size"] if not CONFIG.get("use_api_emb") else 32,
                convert_to_tensor=False,
                normalize_embeddings=True,
                show_progress_bar=True,
            )
            self.papers_embeddings = papers_embeddings
            print("Saving papers embeddings...")
            np.save(path, papers_embeddings)
        print("Papers embeddings ready.")

    def hybrid_search(self, queries, query_tokens, top_k):
        self.get_papers_embeddings()
        self.get_papers_bm25()
        # CPU Search
        queries_emb = self.model_emb.encode(
            queries,convert_to_tensor=True, normalize_embeddings=True
        )
        hits_list = util.semantic_search(queries_emb, self.papers_embeddings, top_k=top_k)
        dense_res = []
        for i, hits in enumerate(hits_list):
            dense_res.append({self.df_papers.iloc[h["corpus_id"]]["arxiv_id"]: h["score"] for h in hits})
        # First fusion (if multiple queries)
        if len(dense_res) > 1:
            dense_fused = {}
            for arxiv_id in set().union(*[set(res.keys()) for res in dense_res]):
                r = {}
                for i, res in enumerate(dense_res):
                    r[i] = list(res).index(arxiv_id) if arxiv_id in res else 2 * top_k
                dense_fused[arxiv_id] = sum([1 / (CONFIG["fusion_k"] + r[i]) for i in range(len(dense_res))])
            dense_fused = sorted(dense_fused.items(), key=lambda x: x[1], reverse=True)
            dense_res = {arxiv_id: score for arxiv_id, score in dense_fused}
        else:
            # Single query, just use the results directly
            dense_res = dense_res[0] if dense_res else {}

        # Sparse Search (BM25)
        docs, scores = self.papers_bm25.retrieve(query_tokens, k=top_k)
        sparse_res = {
            self.df_papers.iloc[docs[0][i]]["arxiv_id"]: scores[0][i]
            for i in range(len(docs[0]))
        }

        # Fusion
        fused = {}
        for arxiv_id in set(dense_res) | set(sparse_res):
            r_dense = list(dense_res).index(arxiv_id) if arxiv_id in dense_res else 2 * top_k
            r_sparse = list(sparse_res).index(arxiv_id) if arxiv_id in sparse_res else 2 * top_k
            fused[arxiv_id] = (1 / (CONFIG["fusion_k"] + r_dense)) + (1 / (CONFIG["fusion_k"] + r_sparse))

        return sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]

    def rerank(self, query, candidates, top_k):
        pairs = []
        valid_ids = []
        paper_map = dict(zip(self.df_papers["arxiv_id"], self.df_papers["combined_text"]))

        for arxiv_id, _ in candidates:
            text = paper_map.get(arxiv_id, "")
            if text:
                pairs.append([query, str(text)[:2000]])
                valid_ids.append(arxiv_id)

        if not pairs:
            return []

        scores = self.reranker.predict(
            pairs, batch_size=CONFIG["batch_size"], show_progress_bar=False
        )
        scored = sorted(zip(valid_ids, scores), key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored[:top_k]]