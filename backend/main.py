import os
import hashlib
import math
import time
import threading
import logging
from io import BytesIO
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from supabase import create_client, Client
from dotenv import load_dotenv

# --- FORCE LOAD .ENV ---
# This looks for .env in the backend folder AND the parent folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(current_dir, '.env'))
load_dotenv(os.path.join(parent_dir, '.env'))

app = Flask(__name__)
CORS(app)

# ... (rest of your imports and config)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION & SECURITY ---
SUPABASE_URL = os.getenv("your supabase url")
SUPABASE_KEY = os.getenv("your supabase key..secret key")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Cloud Credentials Missing! Set SUPABASE_URL and SUPABASE_KEY environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# --- THREAD-SAFE STATE ---
TOTAL_NODES = 5
NODE_LOCATIONS = {
    f"node_{i+1}": loc for i, loc in enumerate([
        "Orbit Alpha (AWS US-East)", 
        "Orbit Beta (AWS Mumbai)", 
        "Orbit Gamma (GCP London)", 
        "Orbit Delta (Azure Singapore)", 
        "Orbit Epsilon (Supabase Frankfurt)"
    ])
}

# Use a lock for thread-safe state modifications
state_lock = threading.Lock()
node_status = {f"node_{i+1}": True for i in range(TOTAL_NODES)}

def get_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

@app.route('/')
def index():
    # Fixed case-sensitivity: Matches the exact filename "Dashboard.html"
    try:
        return send_file(os.path.join(os.path.dirname(app.root_path), 'Dashboard.html'))
    except FileNotFoundError:
        return "Dashboard.html not found. Ensure the filename matches case exactly.", 404

@app.route('/api/status', methods=['GET'])
def get_status():
    with state_lock:
        current_status = node_status.copy()
    
    return jsonify({
        "node_status": current_status,
        "node_locations": NODE_LOCATIONS,
        "mesh_health": (sum(current_status.values()) / TOTAL_NODES) * 100,
        "storage_mode": "SECURE-CLOUD-DISTRIBUTED",
        "timestamp": time.time()
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No data stream"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400

    # Validation: Secure filename and size check
    filename = secure_filename(file.filename)
    raw_data = file.read()
    
    if len(raw_data) > MAX_CONTENT_LENGTH:
        return jsonify({"success": False, "error": "File exceeds 16MB limit"}), 413
    
    if len(raw_data) < TOTAL_NODES:
        return jsonify({"success": False, "error": "File too small for distribution"}), 400

    original_hash = get_checksum(raw_data)
    
    # Check if all nodes are "online" before starting
    with state_lock:
        if not all(node_status.values()):
            return jsonify({"success": False, "error": "Upload blocked: Some orbital nodes are offline"}), 503

    chunk_size = math.ceil(len(raw_data) / TOTAL_NODES)
    
    try:
        for i in range(TOTAL_NODES):
            chunk = raw_data[i * chunk_size : (i + 1) * chunk_size]
            if not chunk: continue # Safety for tiny files
            
            chunk_filename = f"{filename}.p{i}"
            bucket_name = f"node-{i+1}"
            
            # Direct Cloud Upload
            supabase.storage.from_(bucket_name).upload(
                path=chunk_filename,
                file=chunk,
                file_options={"upsert": "true", "content-type": "application/octet-stream"}
            )

        return jsonify({
            "success": True, 
            "integrity_hash": original_hash, 
            "nodes_engaged": TOTAL_NODES
        })
    except Exception as e:
        logger.error(f"Cloud Upload Error: {str(e)}")
        return jsonify({"success": False, "error": "Cloud connection failed during distribution"}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    filename = secure_filename(filename)
    
    with state_lock:
        if not all(node_status.values()):
            return jsonify({"error": "Satellite Mesh offline. Cannot retrieve data."}), 503

    reassembled = bytearray()
    try:
        for i in range(TOTAL_NODES):
            part_name = f"{filename}.p{i}"
            # Attempt retrieval
            cloud_part = supabase.storage.from_(f"node-{i+1}").download(part_name)
            if not cloud_part:
                raise ValueError(f"Missing fragment p{i} on cloud node {i+1}")
            reassembled.extend(cloud_part)
        
        # INTEGRITY CHECK: Compare reassembled hash with original stored hash 
        # (In production, you'd fetch the expected hash from a DB here)
        final_data = bytes(reassembled)
        
        return send_file(
            BytesIO(final_data), 
            as_attachment=True, 
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Retrieval error: {str(e)}")
        return jsonify({"error": "Data corruption or missing fragments on cloud nodes"}), 404

@app.route('/api/toggle_node/<node_id>', methods=['POST'])
def toggle(node_id):
    if node_id in node_status:
        with state_lock:
            node_status[node_id] = not node_status[node_id]
            new_state = node_status[node_id]
        return jsonify({"success": True, "node": node_id, "active": new_state})
    return jsonify({"error": "Node ID not found"}), 404

if __name__ == '__main__':
    # debug=False for production readiness
    app.run(host='0.0.0.0', port=5000, debug=False)
