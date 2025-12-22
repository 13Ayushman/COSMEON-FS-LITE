import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

# --- CONFIGURATION ---
UPLOAD_DIR = "shards"
RECONSTRUCT_DIR = "reconstructed"

# Ensure directories exist
for d in [UPLOAD_DIR, RECONSTRUCT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# --- LIFESPAN (Replaces deprecated on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic
    print("\n==============================")
    print("   COSMEON SECURE SERVER")
    print("==============================")
    print(f"Target: http://127.0.0.1:8000")
    yield
    # Shutdown Logic (Optional)
    print("Server shutting down...")

app = FastAPI(lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE (In-Memory for Lite version) ---
# In a full version, this would be a JSON file or SQLite
file_registry = {}

# --- ROUTES ---

@app.get("/")
async def root():
    return {"status": "online", "system": "COSMEON FS-LITE"}

@app.get("/files")
async def list_files():
    """Returns the list of fragmented files for the dashboard."""
    return list(file_registry.values())

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Fragments a file and stores it."""
    try:
        file_id = str(uuid.uuid4())
        file_content = await file.read()
        
        # Logic: Split file into 4 shards (Simulation)
        shard_size = len(file_content) // 4
        shards_created = 0
        
        for i in range(4):
            start = i * shard_size
            # Last shard takes the remainder
            end = (i + 1) * shard_size if i < 3 else len(file_content)
            
            shard_path = os.path.join(UPLOAD_DIR, f"{file_id}_part_{i}.shard")
            with open(shard_path, "wb") as f:
                f.write(file_content[start:end])
            shards_created += 1

        # Register file
        entry = {
            "id": file_id,
            "filename": file.filename,
            "shard_count": shards_created,
            "size": len(file_content)
        }
        file_registry[file_id] = entry
        
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reconstruct/{file_id}")
async def reconstruct_file(file_id: str):
    """Reassembles shards and serves the file."""
    if file_id not in file_registry:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    metadata = file_registry[file_id]
    output_path = os.path.join(RECONSTRUCT_DIR, metadata["filename"])
    
    try:
        with open(output_path, "wb") as outfile:
            for i in range(metadata["shard_count"]):
                shard_path = os.path.join(UPLOAD_DIR, f"{file_id}_part_{i}.shard")
                with open(shard_path, "rb") as infile:
                    outfile.write(infile.read())
        
        return FileResponse(output_path, filename=metadata["filename"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconstruction failed: {str(e)}")

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Purges shards from storage."""
    if file_id in file_registry:
        # Delete shard files
        for i in range(file_registry[file_id]["shard_count"]):
            shard_path = os.path.join(UPLOAD_DIR, f"{file_id}_part_{i}.shard")
            if os.path.exists(shard_path):
                os.remove(shard_path)
        
        del file_registry[file_id]
        return {"message": "Shards purged successfully"}
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
