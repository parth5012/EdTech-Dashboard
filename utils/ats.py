# # In your_scorer_logic.py (add these imports)
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# # ... (add extract_text function from above) ...

# def calculate_ats_score(resume_text, job_description):
#     if resume_text is None:
#         return {'error': 'Unsupported file type.'}

#     # Create a list of the two texts
#     text_documents = [resume_text, job_description]

#     # Initialize the TF-IDF Vectorizer
#     vectorizer = TfidfVectorizer(stop_words='english')

#     # Fit and transform the documents
#     tfidf_matrix = vectorizer.fit_transform(text_documents)

#     # Calculate the Cosine Similarity
#     # This will return a 2x2 matrix. We want the similarity between doc 0 and doc 1
#     similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    
#     # The score is a value between 0 and 1. Multiply by 100 for a percentage.
#     match_score = similarity_matrix[0][0] * 100

#     # --- Bonus: Find Missing Keywords ---
#     jd_keywords = set(vectorizer.get_feature_names_out())
    
#     # We need to vectorize the resume text ALONE to see its keywords
#     resume_vectorizer = TfidfVectorizer(stop_words='english')
#     resume_vectorizer.fit_transform([resume_text])
#     resume_keywords = set(resume_vectorizer.get_feature_names_out())

#     missing_keywords = list(jd_keywords - resume_keywords)
#     # Sort by importance (highest TF-IDF score in the JD) and take top 10
    
#     jd_feature_index = tfidf_matrix[1].nonzero()[1]
#     jd_scores = zip([vectorizer.get_feature_names_out()[i] for i in jd_feature_index], tfidf_matrix[1, jd_feature_index].data)
    
#     # Filter this list to only include keywords missing from the resume
#     top_missing = sorted(
#         [item for item in jd_scores if item[0] in missing_keywords], 
#         key=lambda x: x[1], 
#         reverse=True
#     )

#     return {
#         'score': round(match_score, 2),
#         'missing_keywords': [kw[0] for kw in top_missing[:10]] # Get top 10
#     }