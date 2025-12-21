import os
import io
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# --- PATH DISCOVERY ---
# Look for .env in current folder AND parent folder
load_dotenv() # Default look
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env')) # Look one level up

app = Flask(__name__, static_folder='../')
CORS(app)

# --- CONFIG & SUPABASE CHECK ---
SUPABASE_URL = os.getenv("https://seqykgsrppbfrzjaqcxu.supabase.co")
SUPABASE_KEY = os.getenv("sb_secret_PIULBuhTh0-FDezUzJNTDw_FzvwbB2z")

# Simulated Satellite Node Registry
NODES = {
    "node_alpha": "Low Earth Orbit (LEO-1)",
    "node_beta": "Polar Orbit (POL-2)",
    "node_gamma": "Geostationary (GEO-3)",
    "node_delta": "Mid-Earth Orbit (MEO-4)"
}

# State management
node_status = {name: True for name in NODES.keys()}

def get_mesh_health():
    active = sum(1 for status in node_status.values() if status)
    return (active / len(NODES)) * 100

def run_diagnostics():
    print("\n" + "="*40)
    print("SATELLITE MESH DIAGNOSTICS")
    
    # Precise file checking for the user
    env_path = os.path.abspath(".env")
    parent_env = os.path.abspath("../.env")
    
    found = False
    if os.path.exists(env_path):
        print(f"✅ .ENV FOUND AT: {env_path}")
        found = True
    elif os.path.exists(parent_env):
        print(f"✅ .ENV FOUND AT: {parent_env}")
        found = True
    else:
        print(f"❌ NO .ENV FOUND. Checked:\n   1. {env_path}\n   2. {parent_env}")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  SYSTEM OFFLINE: SUPABASE_URL or KEY missing inside .env")
    else:
        print(f"🚀 SYSTEM ONLINE: Connected to {SUPABASE_URL[:15]}...")
    print("="*40 + "\n")

# --- API ROUTES ---

@app.route('/')
def serve_index():
    # Serves Dashboard.html if it exists in the root folder
    return send_from_directory(app.static_folder, 'Dashboard.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "mesh_health": get_mesh_health(),
        "node_status": node_status,
        "node_locations": NODES,
        "supabase_connected": bool(SUPABASE_URL and SUPABASE_KEY)
    })

@app.route('/api/toggle_node/<node_id>', methods=['POST'])
def toggle_node(node_id):
    if node_id in node_status:
        node_status[node_id] = not node_status[node_id]
        return jsonify({"success": True, "new_state": node_status[node_id]})
    return jsonify({"error": "Node not found"}), 404

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"success": False, "error": "Backend credentials missing"}), 500
    
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    file_data = file.read()
    
    # Security: Only upload if at least one node is active
    active_nodes = [n for n, status in node_status.items() if status]
    if not active_nodes:
        return jsonify({"success": False, "error": "Mesh network is down. No active nodes."}), 503

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Simple fragmentation simulation (Uploading to a bucket named 'satellite-mesh')
        # In a real app, we'd split the bytes. Here we upload to the "Mesh"
        file_hash = hashlib.sha256(file_data).hexdigest()
        filename = f"fragment_{file_hash[:10]}_{file.filename}"
        
        # Note: 'satellite-mesh' bucket must exist in your Supabase storage
        res = supabase.storage.from_('satellite-mesh').upload(
            path=filename,
            file=file_data,
            file_options={"content-type": file.content_type}
        )
        
        return jsonify({
            "success": True, 
            "integrity_hash": file_hash,
            "nodes_utilized": active_nodes
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    run_diagnostics()
    app.run(host='0.0.0.0', port=5000, debug=True)
