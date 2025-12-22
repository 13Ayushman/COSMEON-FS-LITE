import os
import hashlib
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

# ================= CONFIG =================
CHUNK_SIZE = 1024 * 1024  # 1 MB

BASE_DIR = os.path.dirname(__file__)
NODES_DIR = os.path.join(BASE_DIR, "simulated_nodes")
RESTORE_DIR = os.path.join(BASE_DIR, "restored")

NODES = [f"node_{i}" for i in range(1, 6)]

# Create directories
for node in NODES:
    os.makedirs(os.path.join(NODES_DIR, node), exist_ok=True)
os.makedirs(RESTORE_DIR, exist_ok=True)

# ================= APP =================
app = FastAPI(title="COSMEON FS-LITE Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # OK for hackathon/demo
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= IN-MEMORY REGISTRY =================
# NOTE: In production this would be Supabase / DB
FILE_INDEX = {}

# ================= HELPERS =================
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# ================= API =================

@app.get("/status")
def status():
    node_status = {}
    for node in NODES:
        node_status[node] = os.path.exists(os.path.join(NODES_DIR, node))

    mesh_health = int((sum(node_status.values()) / len(NODES)) * 100)

    return {
        "mesh_health": mesh_health,
        "node_status": node_status
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()

    if not content:
        raise HTTPException(400, "Empty file")

    file_id = hashlib.md5(file.filename.encode()).hexdigest()[:8]

    FILE_INDEX[file_id] = {
        "filename": file.filename,
        "chunks": []
    }

    chunk_index = 0

    for i in range(0, len(content), CHUNK_SIZE):
        chunk = content[i:i + CHUNK_SIZE]
        checksum = sha256(chunk)

        node = NODES[chunk_index % len(NODES)]
        node_path = os.path.join(NODES_DIR, node)

        chunk_name = f"{file_id}.part{chunk_index}"
        chunk_path = os.path.join(node_path, chunk_name)

        with open(chunk_path, "wb") as f:
            f.write(chunk)

        FILE_INDEX[file_id]["chunks"].append({
            "index": chunk_index,
            "node": node,
            "name": chunk_name,
            "hash": checksum,
            "size": len(chunk)
        })

        chunk_index += 1

    return {
        "status": "stored",
        "file_id": file_id,
        "chunks": chunk_index
    }


@app.get("/files")
def list_files():
    return [
        {
            "id": fid,
            "filename": meta["filename"],
            "size": sum(c["size"] for c in meta["chunks"])
        }
        for fid, meta in FILE_INDEX.items()
    ]


@app.get("/download/{file_id}")
def download(file_id: str):
    if file_id not in FILE_INDEX:
        raise HTTPException(404, "File not found")

    output_path = os.path.join(RESTORE_DIR, FILE_INDEX[file_id]["filename"])

    with open(output_path, "wb") as out:
        for chunk in FILE_INDEX[file_id]["chunks"]:
            chunk_path = os.path.join(
                NODES_DIR,
                chunk["node"],
                chunk["name"]
            )

            if not os.path.exists(chunk_path):
                raise HTTPException(
                    500,
                    f"Missing chunk {chunk['name']} on {chunk['node']}"
                )

            with open(chunk_path, "rb") as f:
                data = f.read()
                if sha256(data) != chunk["hash"]:
                    raise HTTPException(500, "Checksum mismatch detected")
                out.write(data)

    return FileResponse(
        output_path,
        filename=FILE_INDEX[file_id]["filename"],
        media_type="application/octet-stream"
    )


@app.delete("/delete/{file_id}")
def delete(file_id: str):
    if file_id not in FILE_INDEX:
        raise HTTPException(404, "File not found")

    for chunk in FILE_INDEX[file_id]["chunks"]:
        path = os.path.join(
            NODES_DIR,
            chunk["node"],
            chunk["name"]
        )
        if os.path.exists(path):
            os.remove(path)

    del FILE_INDEX[file_id]

    return {"status": "deleted"}


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
