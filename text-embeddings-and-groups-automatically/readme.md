# REQUIREMENT

Build a Small FastAPI Service for K-Means Clustering 
Cosine + Auto-k Build a Small FastAPI Service for K-Means Clustering (Cosine + Auto-k by Silhouette)
 
Need a lightweight Python (FastAPI) service that accepts text embeddings, clusters them with K-Means using cosine similarity, auto-selects k via silhouette score, enforces a minimum cluster size, and returns (term, cluster_id). Must support batching (append chunks, then cluster once), and be easy to deploy on a VPS.
 
# What to build
FastAPI app that clusters text embeddings with K-Means (cosine).
Auto-select k via silhouette (metric=cosine) with a small k sweep.
Enforce min cluster size (merge tiny clusters), optional max size split.
 
# Endpoints
POST /start (create/clear run buffer by run_id)
POST /append (append {term, vec})
POST /finalize (run clustering, return {term, cluster_id}, chosen k, silhouette)
GET /healthz (simple ok)

Ship with requirements.txt + README (env vars + run commands) and a few curl tests.

Stack: Python, FastAPI, NumPy, scikit-learn, Uvicorn. (Docker bonus.)
 
# Acceptance (must pass)
Works locally; handles ~1,500 items × 1,536-dim vectors in seconds.
Returns chosen k + silhouette score.
No cluster smaller than configured MIN_SIZE after finalize.
Clean error handling and basic input validation.
  
# To be considered
A 3–6 line outline of how you’ll do cosine K-Means + silhouette k-sweep.
 