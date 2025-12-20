import os
import shutil
from chunker import split_file, reconstruct_file, setup_nodes, NODE_DIR

def run_test_mission():
    print("🛰️  COSMEON FS-LITE: STARTING SYSTEM TEST MISSION...")
    
    # 1. Initialize Nodes
    setup_nodes()
    
    # 2. Create a Mock Mission Payload (Test File)
    test_filename = "mission_data.txt"
    test_content = "SECRET MISSION DATA: " + "A" * 1024 * 512 # 0.5 MB of data
    
    with open(test_filename, "w") as f:
        f.write(test_content)
    
    print(f"📦 Payload Created: {test_filename} ({len(test_content)} bytes)")

    # 3. Test the Splitter
    print("⚡ Initiating Orbital Distribution (Chunking)...")
    metadata = split_file(test_filename)
    
    if not metadata:
        print("❌ FAILED: Metadata is empty. Chunking engine failed.")
        return

    print(f"✅ Distribution Complete: {len(metadata)} chunks stored in nodes.")

    # 4. Verify Chunks physically exist
    print("🔍 Inspecting Satellite Nodes...")
    all_exist = True
    for meta in metadata:
        chunk_path = os.path.join(NODE_DIR, meta['node'], meta['filename'])
        if not os.path.exists(chunk_path):
            print(f"⚠️  WARNING: Chunk missing in {meta['node']}!")
            all_exist = False
    
    if all_exist:
        print("✅ All fragments verified in orbital storage.")

    # 5. Test Reconstruction
    print("🔄 Initiating Reconstruction (Retrieving from orbit)...")
    restored_filename = "restored_mission_data.txt"
    success = reconstruct_file(metadata, restored_filename)

    if success:
        # 6. Final Integrity Comparison
        with open(restored_filename, "r") as f:
            restored_content = f.read()
        
        if restored_content == test_content:
            print("💎 SUCCESS: Data integrity 100% verified. Payload is identical.")
        else:
            print("❌ FAILED: Data corruption detected in reconstructed file.")
    else:
        print("❌ FAILED: Reconstruction process errored out.")

    # 7. Cleanup (Optional - keep for demo, delete for clean testing)
    print("🧹 Cleaning up test artifacts...")
    for f in [test_filename, restored_filename]:
        if os.path.exists(f):
            os.remove(f)
    
    print("🏁 TEST MISSION COMPLETE.")

if __name__ == "__main__":
    run_test_mission()
