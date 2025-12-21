import os
import io
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__, static_folder='../')
CORS(app)

# --- CREDENTIALS ---
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    SYSTEM_ONLINE = True
except:
    SYSTEM_ONLINE = False

# Mapping your actual Supabase Buckets (Updated to match Node-1...Node-5)
NODES = {
    "node_1": "Node-1",
    "node_2": "Node-2",
    "node_3": "Node-3",
    "node_4": "Node-4",
    "node_5": "Node-5"
}
node_status = {name: True for name in NODES.keys()}

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'Dashboard.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    active = sum(1 for status in node_status.values() if status)
    return jsonify({
        "mesh_health": (active / len(NODES)) * 100,
        "node_status": node_status,
        "node_locations": NODES,
        "supabase_connected": SYSTEM_ONLINE
    })

@app.route('/api/toggle_node/<node_id>', methods=['POST'])
def toggle_node(node_id):
    if node_id in node_status:
        node_status[node_id] = not node_status[node_id]
        return jsonify({"success": True})
    return jsonify({"error": "Node not found"}), 404

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not SYSTEM_ONLINE: 
        return jsonify({"success": False, "error": "Cloud Handshake Offline"}), 500
    
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file detected"}), 400

    file = request.files['file']
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()
    
    # Split into 5 fragments
    chunk_size = max(1, len(file_data) // 5)
    chunks = [file_data[i:i + chunk_size] for i in range(0, len(file_data), chunk_size)]
    
    upload_results = []
    
    try:
        for i in range(5):
            node_id = f"node_{i+1}"
            bucket_name = NODES[node_id]
            
            # Only upload if node is 'active' in UI
            if node_status[node_id]:
                frag_data = chunks[i] if i < len(chunks) else b"0"
                filename = f"fragment_{file_hash[:6]}_{file.filename}"
                
                # UPLOAD TO BUCKET
                # The .upload() method returns a response object.
                # In some versions of the library, errors are handled via exceptions.
                supabase.storage.from_(bucket_name).upload(
                    path=filename,
                    file=frag_data,
                    file_options={"content-type": "application/octet-stream", "upsert": "true"}
                )
                upload_results.append(bucket_name)

        return jsonify({
            "success": True, 
            "integrity_hash": file_hash,
            "message": f"Successfully sharded across: {', '.join(upload_results)}"
        })
    except Exception as e:
        print(f"Detailed Server Error: {str(e)}")
        # If the error contains '404', it means the bucket name is still slightly off
        return jsonify({"success": False, "error": f"Storage Error: {str(e)}"}), 500

if __name__ == '__main__':
    print("\n🛰️  SATELLITE MESH ONLINE")
    print("Targeting Buckets: Node-1, Node-2, Node-3, Node-4, Node-5")
    app.run(host='0.0.0.0', port=5000, debug=True)
