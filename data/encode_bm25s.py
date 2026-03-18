import bm25s
import os
import pandas as pd
from tqdm import tqdm
def tokenize_corpus(texts):
    return bm25s.tokenize([str(t).lower() for t in tqdm(texts)], stopwords="en")
path="paper_bm25s_index"
os.makedirs(path, exist_ok=True)

df_papers=pd.read_parquet("arxiv-metadata-oai-snapshot.parquet")
print(df_papers.shape)
df_papers["combined_text"]=df_papers["title"]+" "+df_papers["abstract"]
print(df_papers.shape)
papers_tokens = tokenize_corpus(df_papers["combined_text"])
papers_bm25 = bm25s.BM25(method="bm25+")
papers_bm25.index(papers_tokens)
papers_bm25.save(path)
print("保存成功")
del papers_tokens
# Query the corpus
query = "does the fish purr like a cat?"

# Tokenize the query
query_tokens = bm25s.tokenize(query)

# Get top-k results as a tuple of (doc ids, scores). Both are arrays of shape (n_queries, k)
results, scores = papers_bm25.retrieve(query_tokens, k=2)
print(results, scores,type(results))


# ---- 检索 ----
def search(query, k=5):
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    print('=' * 60)

    query_tokens = bm25s.tokenize(query.lower(), stopwords="en")
    results, scores = papers_bm25.retrieve(query_tokens, k=k)

    # results[0] 是第一个 query 的索引数组
    for rank, (idx, score) in enumerate(zip(results[0], scores[0]), 1):
        row = df_papers.iloc[idx]
        print(f"\n[Rank {rank}] Score: {score:.4f}")
        print(f"  Title   : {row['title']}")
        print(f"  Abstract: {row['abstract'][:200]}...")
        # 如果有其他字段也可以打印，比如 authors、categories
        if 'categories' in df_papers.columns:
            print(f"  Category: {row['categories']}")


# 测试几个 query 看效果
queries = [
    "larged language model reasoning",
    "graph neural network node classification",
    "retrieval augmented generation",
]

for q in queries:
    search(q, k=3)