import os
import math
import hashlib
from concurrent.futures import ThreadPoolExecutor

class CloudShredder:
    """
    Core engine for fragmenting files into encrypted shards.
    This simulates the logic used to split and distribute data.
    """
    
    def __init__(self, output_dir="vault"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_shard_id(self, filename, index):
        """Creates a unique hash-based identity for a fragment."""
        hash_input = f"{filename}_{index}_{os.urandom(8)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    def shred_file(self, file_path, shard_count=4):
        """
        Splits a file into N fragments.
        In a production environment, these would be encrypted and 
        uploaded to different storage providers.
        """
        if not os.path.isfile(file_path):
            print(f"[-] Error: {file_path} not found.")
            return False

        file_size = os.path.getsize(file_path)
        chunk_size = math.ceil(file_size / shard_count)
        base_name = os.path.basename(file_path)
        
        print(f"[+] Initiating shredding for: {base_name} ({file_size} bytes)")
        
        try:
            with open(file_path, 'rb') as f:
                for i in range(shard_count):
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break
                        
                    shard_id = self.generate_shard_id(base_name, i)
                    shard_name = f"{base_name}.shard_{i}.{shard_id}.bin"
                    shard_path = os.path.join(self.output_dir, shard_name)
                    
                    with open(shard_path, 'wb') as shard_file:
                        shard_file.write(chunk_data)
                    
                    print(f"    -> Fragment {i+1} distributed: {shard_name}")
            
            print(f"[+] Successfully shredded into {shard_count} shards.")
            return True
        except Exception as e:
            print(f"[-] Critical failure: {str(e)}")
            return False

    def reassemble_file(self, original_filename, output_name):
        """
        Locates shards in the vault and reassembles them into the original file.
        """
        print(f"[+] Reassembling: {original_filename}")
        
        # Gather all shards for this specific file
        shards = [f for f in os.listdir(self.output_dir) if f.startswith(original_filename + ".shard_")]
        # Sort by the shard index (the number after '.shard_')
        shards.sort(key=lambda x: int(x.split('.shard_')[1].split('.')[0]))

        if not shards:
            print("[-] No fragments found for this identity.")
            return

        try:
            with open(output_name, 'wb') as output_f:
                for shard_name in shards:
                    shard_path = os.path.join(self.output_dir, shard_name)
                    with open(shard_path, 'rb') as s_file:
                        output_f.write(s_file.read())
            print(f"[+] Restoration complete: {output_name}")
        except Exception as e:
            print(f"[-] Restoration failed: {str(e)}")

def main():
    """Entry point for local CLI testing of the shredder logic."""
    engine = CloudShredder()
    
    print("--- COSMEON SHREDDER CLI ---")
    print("1. Shred File")
    print("2. Reassemble File")
    choice = input("Select operation [1/2]: ")

    if choice == "1":
        path = input("Enter path to file: ")
        shards = input("Number of shards (default 4): ") or "4"
        engine.shred_file(path, int(shards))
    elif choice == "2":
        identity = input("Enter original filename identity: ")
        out = input("Enter output filename: ")
        engine.reassemble_file(identity, out)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
