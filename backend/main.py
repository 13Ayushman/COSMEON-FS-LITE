import os
import math
import hashlib
import requests
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ----------------------------
# Cloudinary Configuration
# ----------------------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="COSMEON Cloud Shredder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# In-memory metadata store
# (OK for hackathon demo)
# ----------------------------
FILES = {}  
# structure:
# FILES[file_id] = {
#   "filename": str,
#   "shards": [
#       { "index": int, "url": str, "hash": str }
#   ]
# }

# ----------------------------
# Helpers
# ----------------------------
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def generate_file_id(filename: str) -> str:
    raw = f"{filename}_{os.urandom(8)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]

# ----------------------------
# API Endpoints
# ----------------------------

@app.get("/api/status")
def status():
    return {
        "mesh_health": 100,
        "node_status": {
            "node_1": True,
            "node_2": True,
            "node_3": True,
            "node_4": True,
            "node_5": True
        }
    }

@app.get("/api/files")
def list_files():
    response = []
    for fid, meta in FILES.items():
        response.append({
            "id": fid,
            "filename": meta["filename"],
            "size": len(meta["shards"])
        })
    return response

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    shard_count = 5
    chunk_size = math.ceil(len(content) / shard_count)

    file_id = generate_file_id(file.filename)
    shards_meta = []

    for i in range(shard_count):
        start = i * chunk_size
        end = min(start + chunk_size, len(content))
        chunk = content[start:end]

        if not chunk:
            continue

        shard_hash = sha256(chunk)

        upload_result = cloudinary.uploader.upload(
            chunk,
            resource_type="raw",
            folder=f"cosmeon/{file_id}",
            public_id=f"part_{i}",
            overwrite=True
        )

        shards_meta.append({
            "index": i,
            "url": upload_result["secure_url"],
            "hash": shard_hash
        })

    FILES[file_id] = {
        "filename": file.filename,
        "shards": shards_meta
    }

    return {
        "status": "success",
        "file_id": file_id,
        "shards": len(shards_meta)
    }

@app.get("/api/download/{file_id}")
def download(file_id: str):
    if file_id not in FILES:
        raise HTTPException(status_code=404, detail="File not found")

    shards = sorted(FILES[file_id]["shards"], key=lambda x: x["index"])

    def stream():
        for shard in shards:
            r = requests.get(shard["url"])
            if r.status_code != 200:
                raise HTTPException(status_code=500, detail="Shard retrieval failed")

            if sha256(r.content) != shard["hash"]:
                raise HTTPException(status_code=500, detail="Integrity check failed")

            yield r.content

    filename = FILES[file_id]["filename"]
    return StreamingResponse(
        stream(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.delete("/api/delete/{file_id}")
def delete(file_id: str):
    if file_id not in FILES:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        cloudinary.api.delete_resources_by_prefix(f"cosmeon/{file_id}", resource_type="raw")
        cloudinary.api.delete_folder(f"cosmeon/{file_id}")
    except Exception:
        pass

    del FILES[file_id]
    return {"status": "deleted"}
