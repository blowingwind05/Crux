from sentence_transformers import CrossEncoder

# Download from the 🤗 Hub
model = CrossEncoder("/workspace/bge-reranker-v2-m3")

# Get scores for pairs of texts
pairs = [
    ["how to obtain a teacher's certificate in texas?", 'Some aspiring educators may be confused about the difference between teaching certification and teaching certificates. Teacher certification is another term for the licensure required to teach in public schools, while a teaching certificate is awarded upon completion of an academic program.'],
    ["how to obtain a teacher's certificate in texas?", '["Step 1: Obtain a Bachelor\'s Degree. One of the most important Texas teacher qualifications is a bachelor\'s degree. ... ", \'Step 2: Complete an Educator Preparation Program (EPP) ... \', \'Step 3: Pass Texas Teacher Certification Exams. ... \', \'Step 4: Complete a Final Application and Background Check.\']'],
    ["how to obtain a teacher's certificate in texas?", "Washington Teachers Licensing Application Process Official transcripts showing proof of bachelor's degree. Proof of teacher program completion at an approved teacher preparation school. Passing scores on the required examinations. Completed application for teacher certification in Washington."],
    ["how to obtain a teacher's certificate in texas?", 'Teacher education programs may take 4 years to complete after which certification plans are prepared for a three year period. During this plan period, the teacher must obtain a Standard Certification within 1-2 years. Learn how to get certified to teach in Texas.'],
    ["how to obtain a teacher's certificate in texas?", 'In Texas, the minimum age to work is 14. Unlike some states, Texas does not require juvenile workers to obtain a child employment certificate or an age certificate to work. A prospective employer that wants one can request a certificate of age for any minors it employs, obtainable from the Texas Workforce Commission.'],
]
scores = model.predict(pairs)
print(scores)
# [0.00121048 0.97105724 0.00536712 0.8632406  0.00168043]

# Or rank different texts based on similarity to a single text
ranks = model.rank(
    "how to obtain a teacher's certificate in texas?",
    [
        "[\"Step 1: Obtain a Bachelor's Degree. One of the most important Texas teacher qualifications is a bachelor's degree. ... \", 'Step 2: Complete an Educator Preparation Program (EPP) ... ', 'Step 3: Pass Texas Teacher Certification Exams. ... ', 'Step 4: Complete a Final Application and Background Check.']",
        "Teacher education programs may take 4 years to complete after which certification plans are prepared for a three year period. During this plan period, the teacher must obtain a Standard Certification within 1-2 years. Learn how to get certified to teach in Texas.",
        "Washington Teachers Licensing Application Process Official transcripts showing proof of bachelor's degree. Proof of teacher program completion at an approved teacher preparation school. Passing scores on the required examinations. Completed application for teacher certification in Washington.",
        "Some aspiring educators may be confused about the difference between teaching certification and teaching certificates. Teacher certification is another term for the licensure required to teach in public schools, while a teaching certificate is awarded upon completion of an academic program.",
        "In Texas, the minimum age to work is 14. Unlike some states, Texas does not require juvenile workers to obtain a child employment certificate or an age certificate to work. A prospective employer that wants one can request a certificate of age for any minors it employs, obtainable from the Texas Workforce Commission.",
    ],
)
print(ranks)
# [
#     {'corpus_id': 0, 'score': 0.97105724},
#     {'corpus_id': 1, 'score': 0.8632406},
#     {'corpus_id': 2, 'score': 0.0053671156},
#     {'corpus_id': 4, 'score': 0.0016804343},
#     {'corpus_id': 3, 'score': 0.0012104829},
# ]