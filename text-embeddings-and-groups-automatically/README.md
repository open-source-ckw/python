# Requirement

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
 
# What we are building
A small FastAPI app that:
1. stores incoming text embeddings temporarily,
2. runs K-Means on them using cosine similarity,
3. auto-picks k using silhouette score,
4. enforces a minimum cluster size (merges tiny clusters),
5. returns each term with its cluster_id, plus the chosen k and silhouette score.

# How it works end-to-end
1. Client calls POST /start with a run_id. You create/clear an in-memory buffer keyed by that run_id.
2. Client repeatedly calls POST /append with { term, vec } objects (batched list allowed). You just store them for that run, nothing else.
3. Client calls POST /finalize for that run. Now you:
    - stack vectors into a NumPy array,
    - L2-normalize rows (so Euclidean K-Means ≈ cosine K-Means),
    - sweep k over a small range (e.g., K_MIN..K_MAX), fit K-Means for each, compute silhouette with metric="cosine", pick the best k,
    - enforce MIN_SIZE: any cluster smaller than MIN_SIZE gets merged to its nearest centroid among the big clusters,
    - optionally split clusters larger than MAX_SIZE via a quick 2-means on that cluster (only if that env var is set),
    - return { term, cluster_id } for every term, plus chosen_k and overall silhouette.
4. GET /healthz returns {"status": "ok"}.
