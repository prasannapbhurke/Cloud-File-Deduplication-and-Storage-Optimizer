---
title: Cloud File Deduplication & Storage Optimizer
emoji: ☁️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
---

<div align="center">

# ☁️ Cloud File Deduplication & Storage Optimizer
### Enterprise Block-Level Content-Addressable Storage (CAS) & Redundancy Elimination Engine

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)
[![Cloudflare](https://img.shields.io/badge/Tunnel-Cloudflare-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://www.cloudflare.com/)

<p align="center">
  A high-efficiency cloud storage optimizer that slices incoming files into <b>64 KB blocks</b>, computes cryptographic <b>SHA-256 fingerprints</b>, and eliminates redundant block writes across multi-user environments in real-time.
</p>

</div>

---

## 📌 Academic Information

- **Institution:** D. Y. Patil College of Engineering & Technology, Kolhapur
- **Department:** Department of Computer Science & Engineering
- **Course:** Cloud Computing (CC) Laboratory
- **Batch / Academic Year:** Batch T6 | 2026 – 2027
- **Project Guide:** Mrs. Aditee A. Salokhe
- **Head of Department:** Dr. R. J. Dhanal

### 👥 Project Team (T.Y. CSE - Div C)
| Roll No. | Student Name | Responsibility |
|:---:|:---|:---|
| **155** | **Prasanna Pradeep Bhurke** | Cloud Backend Architecture, Supabase DB & Storage Integration, Live Tunnels |
| **144** | **Sarthak Sanjay Salokhe** | Block Hashing Engine (SHA-256), Deduplication Algorithms |
| **149** | **Vyanktesh Harishchandra Madhyapgol** | Frontend Glassmorphic UI & Visual Block Distribution Map |
| **151** | **Manjunath Rajkumar Gavandi** | Storage Analytics, Space Savings Calculator & Reporting |
| **152** | **Balaji Ramraje Gaikwad** | Testing Suite, File Reconstruction Pipeline & Validation |

---

## 🌟 Key Highlights & Innovations

- ✂️ **Variable & Fixed Block Chunking (64 KB)**: Files are streamed and split into uniform 64 KB content-addressable blocks to detect partial and exact duplicate content across multiple uploads.
- 🔐 **Cryptographic SHA-256 Content-Addressable Storage (CAS)**: Every block is indexed by its immutable cryptographic hash digest, preventing hash collisions and ensuring data integrity.
- 📉 **Massive Cloud Storage Savings**: Reuses existing chunk payloads and increments reference counters (`ref_count`) instead of storing duplicate bytes on cloud disk.
- 🧩 **Interactive Block Inspector**: Visualizes virtual file decomposition into constituent 64 KB blocks with color-coded status badges (`STORED` vs `DEDUPLICATED`).
- ⚡ **Zero-Loss Streaming Reconstruction**: On-demand generator stream fetches, decrypts, and concatenates blocks in sequential order for byte-perfect client downloads.
- ☁️ **Hybrid Cloud Architecture**:
  - **Database:** Supabase Managed PostgreSQL (with automated fallback to local SQLite for offline resilience).
  - **Object Storage:** Supabase Cloud Storage S3 Bucket (with local storage adapter support).
  - **Compute:** Render Linux Cloud Containers / Local Flask WSGI.
  - **Public Access:** One-click Cloudflare & LocalTunnel direct HTTPS tunnels.

---

## 🏗️ System Architecture & Workflow

```mermaid
flowchart TD
    A[Client File Upload] --> B[SHA-256 Whole-File Stream Hasher]
    B --> C{Exact Match in Catalog?}
    C -- Yes (100% Duplicate) --> D[Increment Existing Chunk Ref Counters]
    D --> E[Register Virtual File Link in user_files]
    E --> F[Instant 100% Space Savings Reported]

    C -- No (New / Modified) --> G[Slice Stream into 64 KB Blocks]
    G --> H[Compute SHA-256 Digest for Each Block]
    H --> I{Block Exists in CAS?}
    I -- Yes --> J[Increment Block ref_count]
    I -- No --> K[Store Block in Supabase /chunks Object Bucket]
    K --> L[Insert Record into chunks Catalog]
    J --> M[Map Chunk Index in file_chunks Table]
    L --> M
    M --> N[Register Logical File in user_files]
    N --> O[Recalculate Storage Analytics & Efficiency]
```

---

## 🗄️ Database Schema Design

The engine utilizes a normalized 3-tier relational schema designed for high-concurrency deduplication:

```mermaid
erDiagram
    CHUNKS ||--o{ FILE_CHUNKS : "referenced by"
    USER_FILES ||--o{ FILE_CHUNKS : "composed of"

    CHUNKS {
        varchar(64) chunk_hash PK "SHA-256 Digest"
        bigint size_bytes "Block Size in Bytes"
        int ref_count "Active References"
        timestamp first_uploaded_at "Creation Timestamp"
    }

    USER_FILES {
        bigint id PK "Auto-increment ID"
        text filename "Logical File Name"
        text user_name "Uploader Identity"
        bigint file_size "Total File Size (Bytes)"
        varchar(64) file_hash "Whole-File SHA-256"
        int total_chunks "Total Blocks"
        int dedup_chunks "Reused Blocks"
        int new_chunks "Newly Written Blocks"
        boolean is_deduplicated "Deduplication Flag"
        timestamp upload_timestamp "Upload Time"
    }

    FILE_CHUNKS {
        bigint id PK
        bigint file_id FK "user_files.id"
        int chunk_index "Sequential Block Order"
        varchar(64) chunk_hash FK "chunks.chunk_hash"
    }
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 1. Clone & Setup
```bash
git clone https://github.com/prasannapbhurke/Cloud-File-Deduplication-and-Storage-Optimizer.git
cd Cloud-File-Deduplication-and-Storage-Optimizer
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux / macOS
pip install -r requirements.txt
```

### 2. Configure Environment (.env)
Create a `.env` file in the project root:
```env
# Supabase Cloud Credentials
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-anon-or-service-role-key"
DATABASE_URL="postgresql://postgres.your-project:your-password@aws-0-region.pooler.supabase.com:6543/postgres"

# Optional Port Override (Default: 5000)
PORT=5000
```
*(If `.env` is omitted, the application automatically runs in offline mode using local SQLite and local folder storage).*

---

## 💻 Running the Application

### Option A: One-Click Windows Launchers
- **`run_app.bat`**: Starts the local Flask server on `http://127.0.0.1:5000`.
- **`run_all_live.bat`**: Launches the Flask server **and** starts a free Cloudflare Quick Tunnel, outputting an instant worldwide HTTPS link without port forwarding.
- **`run_cloudflare_tunnel.bat`**: Creates a direct Cloudflare HTTPS tunnel for port 5000.

### Option B: Terminal Command
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

### Option C: Docker & Container Deployment
```bash
docker build -t cloud-file-dedup .
docker run -p 5000:5000 --env-file .env cloud-file-dedup
```

---

## 🧪 Automated Verification Suite

Run the comprehensive test suite to validate all 5 deduplication guarantees:

```bash
python test_dedup.py
```

### What the test validates:
1. **TEST 1**: Uploads File 1 (150 KB multi-block payload) ➔ Verifies `STORED` status and unique chunk allocation.
2. **TEST 2**: Uploads identical File 2 ➔ Verifies **100% duplicate detection, 0 bytes written to disk, and exact hash match**.
3. **TEST 3**: Uploads partially modified File 3 (2 matching chunks + 1 modified chunk) ➔ Verifies **block-level deduplication (reusing 2 blocks, writing only 1)**.
4. **TEST 4**: Reconstructs and streams back all 3 files ➔ Verifies **byte-for-byte SHA-256 cryptographic parity**.
5. **TEST 5**: Verifies live storage analytics, deduplication ratios, and space reduction calculations.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|:---:|:---|:---|
| `POST` | `/api/upload` | Multipart file upload; triggers chunking, hashing, deduplication, and CAS storage. |
| `GET` | `/api/stats` | Returns real-time metrics: physical stored, logical volume, saved bytes, dedup ratio. |
| `GET` | `/api/files` | Lists all registered virtual files with block reuse counts and timestamps. |
| `GET` | `/api/file/<id>/chunks` | Returns the ordered block map, individual chunk digests, sizes, and reference counts. |
| `GET` | `/api/download/<id>` | Reconstructs the file on-demand and streams the binary payload to the client. |
| `POST` | `/api/delete/<id>` | Deletes the virtual file reference and purges chunks with `ref_count == 0`. |
| `POST` | `/api/reset` | Resets the storage catalog and clears chunk repositories. |

---

## 📊 Deliverables & Academic Assets

- 📄 **Print-Ready Academic Project Report (PDF)**: [`Cloud_File_Deduplication_Documentation.pdf`](./Cloud_File_Deduplication_Documentation.pdf)
- 📊 **Project Seminar Presentation (PPTX)**: [`Cloud_File_Deduplication_Presentation.pptx`](./Cloud_File_Deduplication_Presentation.pptx)
- 📝 **Report Generator Scripts**:
  - `python generate_pdf_report.py` (builds formal IEEE formatted report with diagrams and tables)
  - `python generate_ppt_presentation.py` (builds 20-slide widescreen presentation deck)

---

## 🛡️ License

This project was developed for academic research and educational evaluation under the **Department of Computer Science & Engineering, D. Y. Patil College of Engineering and Technology, Kolhapur**.
Distributed under the MIT License.
