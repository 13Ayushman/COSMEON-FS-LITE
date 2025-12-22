🚀 COSMEON FS-LITE
A Distributed Cloud Shredding & Retrieval System

🌐 Live Demo: https://cosme-8fg.pages.dev/

⚙️ Backend API: FastAPI (Render)
☁️ Cloud Storage: Supabase Object Storage

🧩 Abstract

COSMEON FS-LITE is a prototype distributed file system designed to demonstrate secure, resilient, and decentralized cloud storage.
Instead of storing files as a single object, the system cryptographically fragments data, distributes it across independent cloud nodes, and reconstructs the original file with bit-level accuracy on demand.

The project focuses on data integrity, fault awareness, and cloud-native deployment, making it suitable for hackathon evaluation, academic demos, and distributed systems experimentation.

❓ Problem Statement

Traditional cloud storage systems rely on centralized file storage, which introduces:

Single points of failure

Increased blast radius during breaches

Limited transparency into data integrity

Weak resilience to partial outages

Modern systems require fragmentation, decentralization, and verifiable recovery.

💡 Solution Overview

COSMEON FS-LITE implements a distributed shredding protocol:

Files are split into fixed-size fragments

Each fragment is cryptographically hashed

Fragments are distributed across multiple cloud nodes

Metadata tracks fragment order and integrity

Files are reconstructed exactly as uploaded

At no point does any single node contain the complete file.

🏗️ System Architecture
┌────────────────────┐
│  Frontend Dashboard│
│  (Cloudflare Pages)│
└──────────┬─────────┘
           │ HTTPS
           ▼
┌────────────────────┐
│ FastAPI Backend    │
│ (Render Cloud)     │
└──────────┬─────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Supabase Object Storage           │
│ Distributed Shard Containers     │
└──────────────────────────────────┘

🔐 Core Features
✅ Distributed Shredding

Files are split into multiple independent fragments

No fragment contains meaningful standalone data

✅ Cryptographic Integrity

SHA-256 hashing applied to fragments

Ensures tamper detection and data correctness

✅ Cloud-Backed Decentralization

Fragments stored across independent cloud objects

Demonstrates decentralized storage logic

✅ Exact Reconstruction

Fragments are reassembled in order

Output file matches original byte-for-byte

✅ Real-Time Ground Control UI

Upload & shred files

View active fragments

Reassemble and download files

Detect backend availability in real time

🖥️ Frontend

Pure HTML + TailwindCSS

Zero framework overhead

Hosted on Cloudflare Pages

Stateless and fully decoupled from backend

🔗 Live UI:
👉 https://cosme-8fg.pages.dev/

⚙️ Backend

FastAPI (Python)

Stateless REST architecture

Handles:

File ingestion

Fragment metadata

Integrity validation

Recovery orchestration

Deployed on Render

Key API Endpoints
GET    /api/status
GET    /api/files
POST   /api/upload
GET    /api/download/{file_id}
DELETE /api/delete/{file_id}

☁️ Storage Layer

Fragments are stored using Supabase Object Storage.

Each uploaded file is stored as a directory:

filename_timestamp/
├── part_0.bin
├── part_1.bin
├── part_2.bin
└── part_3.bin


This layout enables:

Fragment isolation

Independent deletion

Ordered reconstruction

🧪 Resilience Model (Prototype)

Node availability is monitored logically

Missing fragments are detected during recovery

System fails safely if reconstruction is impossible

This simulates real distributed system behavior under partial failure.

🚀 Local Development (Optional)
Backend
cd backend
pip install -r requirements.txt
python main.py

Frontend

Open index.html directly
or

Deploy using Cloudflare Pages / Netlify

🧑‍💻 Technology Stack

Frontend: HTML, TailwindCSS, JavaScript

Backend: Python, FastAPI

Cloud: Render, Supabase, Cloudflare Pages

Security: SHA-256 hashing

📌 Use Cases

Secure cloud storage prototypes

Distributed systems demonstrations

Fault-tolerant storage research

Hackathon & academic evaluations

🏁 Project Status

✔ Fully functional prototype
✔ Cloud-deployed frontend & backend
✔ End-to-end file recovery verified

📄 License

MIT License — free to use, modify, and extend.
