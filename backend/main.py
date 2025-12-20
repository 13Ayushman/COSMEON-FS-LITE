import os
import hashlib
import math
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

# --- SYSTEM CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_PATH = os.path.join(BASE_DIR, 'orbital_mesh_storage')
TOTAL_NODES = 5
node_status = {f"node_{i+1}": True for i in range(TOTAL_NODES)}

# Ensure directory structure
for i in range(1, TOTAL_NODES + 1):
    os.makedirs(os.path.join(STORAGE_PATH, f"node_{i}"), exist_ok=True)

def calculate_hash(data):
    return hashlib.sha256(data).hexdigest()

@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'dashboard.html'))

@app.route('/api/status', methods=['GET'])
def get_status():
    node_contents = {}
    for node_id in node_status.keys():
        path = os.path.join(STORAGE_PATH, node_id)
        node_contents[node_id] = os.listdir(path) if os.path.exists(path) else []
    
    return jsonify({
        "node_status": node_status,
        "node_contents": node_contents,
        "mesh_health": sum(node_status.values()) / TOTAL_NODES * 100,
        "timestamp": time.time()
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No data stream"}), 400
    
    file = request.files['file']
    raw_data = file.read()
    original_hash = calculate_hash(raw_data)
    
    # Fragment the binary data
    chunk_size = math.ceil(len(raw_data) / TOTAL_NODES)
    
    for i in range(TOTAL_NODES):
        node_id = f"node_{i+1}"
        start, end = i * chunk_size, (i + 1) * chunk_size
        chunk = raw_data[start:end]
        
        # Metadata is attached to filename to simulate a database record
        chunk_filename = f"{file.filename}.part_{i}"
        with open(os.path.join(STORAGE_PATH, node_id, chunk_filename), 'wb') as f:
            f.write(chunk)

    return jsonify({
        "success": True,
        "filename": file.filename,
        "hash": original_hash,
        "size": len(raw_data),
        "nodes_utilized": TOTAL_NODES
    })

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    # Security Guard: Check if critical fragments are reachable
    offline = [id for id, online in node_status.items() if not online]
    if offline:
        return jsonify({"error": "Data Incomplete", "missing_nodes": offline}), 503

    reassembled = bytearray()
    try:
        for i in range(TOTAL_NODES):
            with open(os.path.join(STORAGE_PATH, f"node_{i+1}", f"{filename}.part_{i}"), 'rb') as f:
                reassembled.extend(f.read())
        
        return send_file(BytesIO(reassembled), as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/toggle_node/<node_id>', methods=['POST'])
def toggle(node_id):
    if node_id in node_status:
        node_status[node_id] = not node_status[node_id]
        return jsonify({"success": True, "state": node_status[node_id]})
    return jsonify({"error": "Node ID invalid"}), 404

if __name__ == '__main__':
    print("\n[V2.0] COSMEON DISTRIBUTED ENGINE LOADED")
    app.run(debug=True, port=5000)