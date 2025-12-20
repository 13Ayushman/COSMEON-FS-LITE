# chunker.py
import os
import hashlib
import shutil

# --- CONFIGURATION ---
# 1MB Chunks
CHUNK_SIZE = 1024 * 1024 
# Relative path for cloud compatibility (Linux/Windows safe)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NODE_DIR = os.path.join(BASE_DIR, "simulated_nodes")
NODES = ["node_1", "node_2", "node_3", "node_4", "node_5"]

def setup_nodes():
    """
    Creates the simulated satellite folders.
    Crucial for Cloud: Runs every time to ensure folders exist on ephemeral storage.
    """
    if not os.path.exists(NODE_DIR):
        os.makedirs(NODE_DIR)
    
    for node in NODES:
        path = os.path.join(NODE_DIR, node)
        if not os.path.exists(path):
            os.makedirs(path)

def calculate_checksum(data):
    """Generates SHA-256 fingerprint for integrity checks."""
    return hashlib.sha256(data).hexdigest()

def split_file(file_path):
    """
    Reads a file, splits it into 1MB chunks, calculates hashes,
    and distributes them across the 5 simulated nodes.
    """
    setup_nodes()
    
    file_name = os.path.basename(file_path)
    # Remove the 'temp_' prefix if present for clean storage names
    clean_name = file_name.replace("temp_", "")
    
    chunks_metadata = []
    
    try:
        with open(file_path, 'rb') as f:
            chunk_index = 0
            while True:
                chunk_data = f.read(CHUNK_SIZE)
                if not chunk_data:
                    break
                
                # 1. Integrity: Calculate Hash
                chunk_hash = calculate_checksum(chunk_data)
                
                # 2. Distribution: Round Robin (0->Node1, 1->Node2, etc.)
                node_name = NODES[chunk_index % len(NODES)]
                node_path = os.path.join(NODE_DIR, node_name)
                
                # Create unique chunk name: filename.part0, filename.part1
                chunk_filename = f"{clean_name}.part{chunk_index}"
                full_chunk_path = os.path.join(node_path, chunk_filename)
                
                # 3. Storage: Write to the specific node folder
                with open(full_chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)
                
                chunks_metadata.append({
                    "index": chunk_index,
                    "node": node_name,
                    "hash": chunk_hash,
                    "filename": chunk_filename
                })
                chunk_index += 1
                
        print(f"✅ [SYSTEM] Split {clean_name} into {chunk_index} chunks.")
        return chunks_metadata

    except Exception as e:
        print(f"❌ [ERROR] Chunking failed: {e}")
        return []

def reconstruct_file(chunks_metadata, output_path):
    """
    Retrieves chunks from the nodes, verifies their integrity,
    and rebuilds the original file.
    """
    try:
        with open(output_path, 'wb') as f_out:
            # sort by index to ensure correct order
            sorted_chunks = sorted(chunks_metadata, key=lambda x: x['index'])
            
            for meta in sorted_chunks:
                node_path = os.path.join(NODE_DIR, meta['node'])
                chunk_path = os.path.join(node_path, meta['filename'])
                
                # 1. Availability Check
                if not os.path.exists(chunk_path):
                    print(f"❌ [FAILURE] Node {meta['node']} is offline or chunk missing.")
                    return False
                
                with open(chunk_path, 'rb') as f_in:
                    chunk_data = f_in.read()
                    
                    # 2. Integrity Check
                    if calculate_checksum(chunk_data) != meta['hash']:
                        print(f"⚠️ [CORRUPTION] Integrity mismatch in chunk {meta['index']}")
                        return False
                    
                    f_out.write(chunk_data)
                    
        print(f"✅ [SYSTEM] {os.path.basename(output_path)} reconstructed successfully.")
        return True

    except Exception as e:
        print(f"❌ [ERROR] Reconstruction process failed: {e}")
        return False