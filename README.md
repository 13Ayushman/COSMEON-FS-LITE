# 🚀 COSMEON FS-LITE  
### Distributed Cloud Shredding & Retrieval System

🌐 **Live Demo (Frontend):** https://cosme-8fg.pages.dev/  
⚙️ **Backend:** FastAPI (Render)  
☁️ **Cloud Storage:** Supabase Object Storage  

---

## 🧠 Problem Statement

Centralized cloud storage creates **single points of failure**, security risks, and data exposure.  
COSMEON FS-LITE demonstrates a **distributed file system concept** where:

- No single node ever stores the complete file
- Data integrity is preserved
- Files can be reconstructed exactly as uploaded
- Node failures can be detected and handled

---

## 💡 Solution Overview

COSMEON FS-LITE implements a **distributed shredding protocol**:

1. A file is split into fixed-size chunks
2. Each chunk is cryptographically hashed
3. Chunks are distributed across multiple simulated nodes
4. Metadata enables exact reassembly
5. Files are restored byte-perfect on retrieval

---

## 🏗️ Architecture

