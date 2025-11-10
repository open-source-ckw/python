# app.py
app = FastAPI()

@app.post("/start")
def start(req: StartReq):
    runs.start(req.run_id)
    return {"ok": True}

@app.post("/append")
def append(req: AppendReq):
    try:
        count = runs.append(req.run_id, req.items)
        return {"ok": True, "count": count}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/finalize", response_model=FinalizeResp)
def finalize(req: FinalizeReq):
    try:
        terms, X = runs.materialize(req.run_id)
        labels, chosen_k, sil = auto_kmeans_finalize(X)
        assignments = [{"term": t, "cluster_id": int(l)} for t, l in zip(terms, labels)]
        return {"ok": True, "chosen_k": int(chosen_k), "silhouette": float(sil), "assignments": assignments}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
