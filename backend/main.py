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

app = Flask(__name__)
CORS(app)

# --- MANUAL ENV PARSER (If load_dotenv fails) ---
def load_env_manual(filepath):
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if they exist
                os.environ[key.strip()] = value.strip().strip('"').strip("'")
    return True

# --- PATHS ---
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
env_path = os.path.join(backend_dir, '.env')

print("\n" + "="*40)
print("SATELLITE MESH DIAGNOSTICS")
if load_env_manual(env_path):
    print(f"✅ FOUND .ENV AT: {env_path}")
else:
    print(f"❌ NO .ENV FOUND AT: {env_path}")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    print(f"🚀 CLOUD LINK ESTABLISHED: {SUPABASE_URL[:20]}...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("⚠️  SYSTEM OFFLINE: SUPABASE_URL or KEY missing inside .env")
print("="*40 + "\n")

# --- MESH STATE ---
TOTAL_NODES = 5
NODE_LOCATIONS = {
    "node_1": "Orbit Alpha (AWS US-East)", 
    "node_2": "Orbit Beta (AWS Mumbai)", 
    "node_3": "Orbit Gamma (GCP London)", 
    "node_4": "Orbit Delta (Azure Singapore)", 
    "node_5": "Orbit Epsilon (Supabase Frankfurt)"
}
state_lock = threading.Lock()
node_status = {f"node_{i+1}": True for i in range(TOTAL_NODES)}

@app.route('/')
def index():
    # Force find Dashboard.html (Case Insensitive Check)
    for f in os.listdir(root_dir):
        if f.lower() == 'dashboard.html':
            return send_file(os.path.join(root_dir, f))
    return "Error: Dashboard.html not found in root folder.", 404

@app.route('/api/status', methods=['GET'])
def get_status():
    with state_lock:
        return jsonify({
            "node_status": node_status,
            "node_locations": NODE_LOCATIONS,
            "mesh_health": (sum(node_status.values()) / TOTAL_NODES) * 100
        })

# --- UPLOAD ROUTE ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({"success": False, "error": "No file"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    raw_data = file.read()
    
    if len(raw_data) < TOTAL_NODES: return jsonify({"success": False, "error": "File too small"}), 400
    
    original_hash = hashlib.sha256(raw_data).hexdigest()
    chunk_size = math.ceil(len(raw_data) / TOTAL_NODES)
    
    try:
        for i in range(TOTAL_NODES):
            chunk = raw_data[i * chunk_size : (i + 1) * chunk_size]
            if not chunk: continue
            supabase.storage.from_(f"node-{i+1}").upload(
                path=f"{filename}.p{i}",
                file=chunk,
                file_options={"upsert": "true", "content-type": "application/octet-stream"}
            )
        return jsonify({"success": True, "integrity_hash": original_hash})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/toggle_node/<node_id>', methods=['POST'])
def toggle(node_id):
    if node_id in node_status:
        with state_lock:
            node_status[node_id] = not node_status[node_id]
        return jsonify({"success": True})
    return jsonify({"error": "Invalid node"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)False)
