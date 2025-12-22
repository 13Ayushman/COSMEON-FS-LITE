import os
import math
import hashlib
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil

app = FastAPI(title="Cosmeon Cloud Shredder API")

# Enable CORS so your React dashboard can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
VAULT_DIR = "vault"
OUTPUT_DIR = "restored"

for folder in [VAULT_DIR, OUTPUT_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

class CloudShredder:
    def generate_shard_id(self, filename, index):
        """Creates a unique hash-based identity for a fragment."""
        hash_input = f"{filename}_{index}_{os.urandom(8)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    def shred_content(self, content: bytes, filename: str, shard_count: int):
        file_size = len(content)
        chunk_size = math.ceil(file_size / shard_count)
        shards_info = []

        for i in range(shard_count):
            start = i * chunk_size
            end = min(start + chunk_size, file_size)
            chunk_data = content[start:end]
            
            if not chunk_data:
                break
                
            shard_id = self.generate_shard_id(filename, i)
            shard_name = f"{filename}.shard_{i}.{shard_id}.bin"
            shard_path = os.path.join(VAULT_DIR, shard_name)
            
            with open(shard_path, 'wb') as shard_file:
                shard_file.write(chunk_data)
            
            shards_info.append({
                "index": i,
                "shard_id": shard_id,
                "name": shard_name,
                "size": len(chunk_data)
            })
        
        return shards_info

engine = CloudShredder()

@app.get("/")
async def root():
    return {"message": "Cosmeon Shredder API is Online", "vault_status": "Active"}

@app.post("/shred")
async def api_shred(file: UploadFile = File(...), shards: int = Form(4)):
    try:
        content = await file.read()
        shard_data = engine.shred_content(content, file.filename, shards)
        
        return {
            "status": "success",
            "filename": file.filename,
            "original_size": len(content),
            "shards_created": len(shard_data),
            "shards": shard_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reassemble/{filename}")
async def api_reassemble(filename: str):
    shards = [f for f in os.listdir(VAULT_DIR) if f.startswith(filename + ".shard_")]
    shards.sort(key=lambda x: int(x.split('.shard_')[1].split('.')[0]))

    if not shards:
        raise HTTPException(status_code=404, detail="No fragments found for this file.")

    output_path = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(output_path, 'wb') as output_f:
            for shard_name in shards:
                with open(os.path.join(VAULT_DIR, shard_name), 'rb') as s_file:
                    output_f.write(s_file.read())
        
        return {"status": "restored", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Render provides the PORT environment variable automatically
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
