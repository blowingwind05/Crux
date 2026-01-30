import pandas as pd

df=pd.read_parquet("legacy/ir_papers.parquet")
print(df.columns)
# Index(['alphaxiv_overview', 'arxiv_id', 'abstract', 'affiliation_detail',
#        'title', 'metadata', 'alphaxiv_detail', 'full_text', 'id', 'hits',
#        'score_detail', 'category_detail'],
#       dtype='object')
print(df["metadata"][0])
# {'all_categories': array(['cs.CL', 'cs.AI', 'cs.IR', 'cs.MA'], dtype=object), 'arxiv_url': 'http://arxiv.org/abs/2512.23647v1', 'authors': array(['Baixuan Li', 'Jialong Wu', 'Wenbiao Yin', 'et al.'], dtype=object), 'category': 'CL', 'date': '2025-12-29', 'doi': None, 'journal_ref': None, 'pdf_url': 'https://arxiv.org/pdf/2512.23647v1', 'primary_category': 'cs.CL', 'timestamp': 1767031154}

# 想要字段：arxiv_id，title，abstract,arxiv_url,authors,date

df["arxiv_url"]=df["metadata"].apply(lambda x:x['arxiv_url'])
df["authors"]=df["metadata"].apply(lambda x:x['authors'])
df["date"]=df["metadata"].apply(lambda x:x['date'])
print(df[['arxiv_id','title','abstract','arxiv_url','authors','date']])
df[['arxiv_id','title','abstract','arxiv_url','authors','date']].to_json("ir_papers.json", orient="records", force_ascii=False, indent=4)