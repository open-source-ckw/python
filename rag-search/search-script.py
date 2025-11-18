import psycopg2
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import openai

# -----------------------------
# CONFIGURATION
# -----------------------------
DB_CONFIG = {
    "dbname": "ai_memory",
    "user": "admin",
    "password": "xxx",
    "host": "0.0.0.0",
    "port": 5434
}



# Sentence-transformers model for neural search
model = SentenceTransformer('all-MiniLM-L6-v2')


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


# -----------------------------
# 1️⃣ Keyword-based search
# -----------------------------
def keyword_search(keyword):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT msg_id, msg_content_text FROM te_ai_message WHERE msg_content_text ILIKE %s"
    cur.execute(query, (f"%{keyword}%",))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


# -----------------------------
# 2️⃣ TF-IDF / BM25 search
# -----------------------------
def tfidf_search(query_text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT msg_content_text FROM te_ai_message")
    docs = [r[0] for r in cur.fetchall()]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(docs)
    query_vec = vectorizer.transform([query_text])
    scores = cosine_similarity(query_vec, tfidf_matrix)[0]
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    cur.close()
    conn.close()
    return ranked[:5]


# -----------------------------
# 3️⃣ Semantic search (OpenAI embeddings)
# -----------------------------
def semantic_search(query_text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT cantxt_id, cantxt_content_text FROM te_ai_canonical_data")
    results = cur.fetchall()
    cur.close()
    conn.close()

    docs = [r[1] for r in results]
    embeddings = model.encode(docs, convert_to_tensor=True)
    query_emb = model.encode(query_text, convert_to_tensor=True)
    scores = util.cos_sim(query_emb, embeddings)[0]
    ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [(r[0], r[1], float(score)) for r, score in ranked[:5]]


# -----------------------------
# 4️⃣ Vector / ANN search (pgvector)
# -----------------------------
def vector_search(query_embedding):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT cantxt_id, cantxt_content_text FROM te_ai_canonical_data ORDER BY embedding <-> %s LIMIT 5;", (query_embedding,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


# -----------------------------
# 5️⃣ Learning-to-rank (TF-IDF + ML features)
# -----------------------------
def ltr_search(query_text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT msg_content_text FROM te_ai_message")
    docs = [r[0] for r in cur.fetchall()]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(docs)
    query_vec = vectorizer.transform([query_text])
    scores = cosine_similarity(query_vec, tfidf_matrix)[0]
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    cur.close()
    conn.close()
    return ranked[:5]


# -----------------------------
# 6️⃣ Neural search (SentenceTransformer)
# -----------------------------
def neural_search(query_text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT cantxt_id, cantxt_content_text FROM te_ai_canonical_data")
    results = cur.fetchall()
    cur.close()
    conn.close()

    docs = [r[1] for r in results]
    embeddings = model.encode(docs, convert_to_tensor=True)
    query_emb = model.encode(query_text, convert_to_tensor=True)
    scores = util.cos_sim(query_emb, embeddings)[0]
    ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [(r[0], r[1], float(score)) for r, score in ranked[:5]]


# -----------------------------
# 7️⃣ Domain-specific search (example: language filter)
# -----------------------------
def domain_search(keyword, lang="en"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT cantxt_content_text 
        FROM te_ai_canonical_data 
        WHERE cantxt_content_text ILIKE %s AND cantxt_lang=%s
    """, (f"%{keyword}%", lang))
    results = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return results


# -----------------------------
# 8️⃣ Hybrid search (vector + keyword filter)
# -----------------------------
def hybrid_search(query_text, lang="en"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT cantxt_id, cantxt_content_text FROM te_ai_canonical_data WHERE cantxt_lang=%s", (lang,))
    results = cur.fetchall()
    cur.close()
    conn.close()

    docs = [r[1] for r in results]
    embeddings = model.encode(docs, convert_to_tensor=True)
    query_emb = model.encode(query_text, convert_to_tensor=True)
    scores = util.cos_sim(query_emb, embeddings)[0]
    ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [(r[0], r[1], float(score)) for r, score in ranked[:5]]


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    print("Keyword search:", keyword_search("tooth pain"))
    print("TF-IDF search:", tfidf_search("tooth pain"))
    print("Neural search:", neural_search("tooth pain"))
    print("Domain search (English):", domain_search("tooth pain"))
    print("Hybrid search:", hybrid_search("tooth pain"))
