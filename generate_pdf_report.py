import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Draw header on pages > 1
        if self._pageNumber > 1:
            self.drawString(54, 750, "Cloud File Deduplication & Storage Optimizer — Project Documentation")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, letter[0] - 54, 742)
            
        # Draw footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 36, footer_text)
        self.drawString(54, 36, "D. Y. Patil College of Engineering & Technology, Kolhapur | Batch T6")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, letter[0] - 54, 48)
        self.restoreState()

def build_pdf(filename="Cloud_File_Deduplication_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1E293B")
    accent_color = colors.HexColor("#2563EB")
    emerald_color = colors.HexColor("#059669")
    text_dark = colors.HexColor("#0F172A")
    text_muted = colors.HexColor("#475569")
    card_bg = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=primary_color,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E3A8A")
    )

    story = []

    # Title & Header
    story.append(Paragraph("Cloud File Deduplication & Storage Optimizer", title_style))
    story.append(Paragraph("D. Y. Patil College of Engineering & Technology, Kolhapur | Department of CSE | Batch T6 (2026-27)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=0, spaceAfter=14))

    # Meta Info Card
    meta_data = [
        [
            Paragraph("<b>Institution:</b> D. Y. Patil College of Engg. & Tech., Kolhapur", body_style),
            Paragraph("<b>Course:</b> Cloud Computing (CC) Laboratory", body_style)
        ],
        [
            Paragraph("<b>Department:</b> Computer Science & Engineering", body_style),
            Paragraph("<b>Batch / Academic Year:</b> Batch T6 (2026 – 2027)", body_style)
        ],
        [
            Paragraph("<b>Project Guide:</b> Mrs. Aditee A. Salokhe", body_style),
            Paragraph("<b>Head of Department:</b> Dr. R. J. Dhanal", body_style)
        ],
        [
            Paragraph("<b>Live Stack:</b> Netlify (Frontend) | Render (Backend)", body_style),
            Paragraph("<b>Database & Storage:</b> Supabase PostgreSQL + S3 Storage", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), card_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Team Members Table
    team_data = [
        [
            Paragraph("<b>Roll No.</b>", body_style),
            Paragraph("<b>Student Name (T.Y. CSE - Div C)</b>", body_style),
            Paragraph("<b>Project Module & Responsibility</b>", body_style)
        ],
        [
            Paragraph("<b>155</b>", body_style),
            Paragraph("Prasanna Pradeep Bhurke", body_style),
            Paragraph("Cloud Backend Architecture, Supabase DB & Storage Integration, Live Tunnels", body_style)
        ],
        [
            Paragraph("<b>144</b>", body_style),
            Paragraph("Sarthak Sanjay Salokhe", body_style),
            Paragraph("Block Hashing Engine (SHA-256), Deduplication Algorithms", body_style)
        ],
        [
            Paragraph("<b>149</b>", body_style),
            Paragraph("Vyanktesh Harishchandra Madhyapgol", body_style),
            Paragraph("Frontend Glassmorphic UI & Visual Block Distribution Map", body_style)
        ],
        [
            Paragraph("<b>151</b>", body_style),
            Paragraph("Manjunath Rajkumar Gavandi", body_style),
            Paragraph("Storage Analytics, Space Savings Calculator & Reporting", body_style)
        ],
        [
            Paragraph("<b>152</b>", body_style),
            Paragraph("Balaji Ramraje Gaikwad", body_style),
            Paragraph("Testing Suite, File Reconstruction Pipeline & Validation", body_style)
        ]
    ]
    team_table = Table(team_data, colWidths=[60, 180, 264])
    team_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(team_table)
    story.append(Spacer(1, 14))

    # Section 1: Executive Overview
    story.append(Paragraph("1. Executive Overview & Problem Statement", h1_style))
    story.append(Paragraph(
        "Modern cloud storage systems face severe data redundancy. Studies indicate that <b>40% to 70%</b> of data stored in organizational clouds (Google Drive, Dropbox, AWS S3) consists of duplicate files, minor revisions, and identical shared attachments. Storing duplicate bytes wastes cloud budgets, network bandwidth, and backup infrastructure.",
        body_style
    ))
    story.append(Paragraph(
        "The <b>Cloud File Deduplication & Storage Optimizer</b> is an enterprise-grade cloud system that eliminates redundant file storage. By slicing files into uniform <b>64 KB chunk blocks</b>, generating cryptographically collision-resistant <b>SHA-256 fingerprints</b>, and managing reference counts within a central metadata catalog, the system guarantees that <b>any identical chunk is stored physically only once</b> across the entire cloud.",
        body_style
    ))

    # Section 2: Complete Technology Stack
    story.append(Spacer(1, 6))
    story.append(Paragraph("2. Full Technology Stack: Frontend, Backend & Database", h1_style))
    
    tech_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technology / Service</b>", body_style), Paragraph("<b>Role & Technical Responsibilities</b>", body_style)],
        [
            Paragraph("<b>Frontend (UI/UX)</b>", body_style),
            Paragraph("<b>HTML5, Modern CSS3, JavaScript (Vanilla ES6+), Netlify CDN</b>", body_style),
            Paragraph("• Responsive Glassmorphism dashboard with dark mode palette.<br/>• Drag-and-drop file upload zone with real-time chunk visualization.<br/>• Live analytics cards: deduplication ratio, percentage reduction, logical vs. physical space.<br/>• Visual chunk map showing shared vs. unique blocks.<br/>• Hosted globally on Netlify CDN with automated API proxy rewrites.", body_style)
        ],
        [
            Paragraph("<b>Backend (Engine)</b>", body_style),
            Paragraph("<b>Python 3, Flask, Gunicorn, REST API, Render Web Service</b>", body_style),
            Paragraph("• Slices file streams into uniform 64 KB binary blocks dynamically.<br/>• Calculates SHA-256 digests in linear O(N) streaming time.<br/>• Cross-Origin Resource Sharing (CORS) enabled for microservice communication.<br/>• Asynchronous chunk verification & reference counting.<br/>• On-demand file reconstruction and chunk streaming for byte-perfect downloads.<br/>• Deployed 24/7 on Render cloud with automated auto-scaling.", body_style)
        ],
        [
            Paragraph("<b>Database (Metadata)</b>", body_style),
            Paragraph("<b>Supabase Cloud PostgreSQL + IPv4 Connection Pooler</b>", body_style),
            Paragraph("• Relational schema with ACID compliance.<br/>• Foreign key cascades linking logical files to physical chunk hashes.<br/>• Indexed lookups on 64-character SHA-256 fingerprints for O(1) duplicate checks.<br/>• Resilient database adapter with automatic fallback to local SQLite if offline.", body_style)
        ],
        [
            Paragraph("<b>Storage (Object Layer)</b>", body_style),
            Paragraph("<b>Supabase Cloud Storage (S3-Compatible Bucket)</b>", body_style),
            Paragraph("• Stores unique raw binary chunks in the 'cloud-chunks' bucket.<br/>• Local LRU binary caching to accelerate read throughput and reconstruction.<br/>• Seamless dual-adapter mode: Cloud Object Storage vs. Local directory bucket.", body_style)
        ]
    ]

    tech_table = Table(tech_data, colWidths=[90, 130, 284])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, card_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tech_table)

    story.append(PageBreak())

    # Section 3: Architecture & Deduplication Algorithm
    story.append(Paragraph("3. Chunk-Level Deduplication Algorithm & Lifecycle", h1_style))
    story.append(Paragraph(
        "Deduplication occurs at the <b>chunk level</b> (sub-file level) rather than whole-file level. This ensures that when a user uploads an edited version of a 100 MB file where only 1 paragraph was changed, 99.9% of the unchanged chunks are reused, saving massive cloud storage.",
        body_style
    ))
    
    algo_steps = [
        "<b>Step 1 — Stream Ingestion:</b> The uploaded file is read as an in-memory binary stream without saving unverified temporary files to disk.",
        "<b>Step 2 — Fixed-Size Chunking:</b> The stream is partitioned into discrete 64 KB (65,536 bytes) binary blocks.",
        "<b>Step 3 — Cryptographic Hashing:</b> For each chunk, a SHA-256 cryptographic fingerprint (a 64-character hexadecimal digest) is generated.",
        "<b>Step 4 — Catalog Hash Lookup:</b> The engine queries PostgreSQL: <i>SELECT ref_count FROM chunks WHERE chunk_hash = %s</i>.",
        "<b>Step 5 — Conditional Action:</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• <b>If Hash Exists (Duplicate):</b> Skip physical upload! Increment chunk <i>ref_count = ref_count + 1</i> in database.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• <b>If Hash is New:</b> Upload 64 KB payload to Supabase Object Storage, insert new record in <i>chunks</i> with <i>ref_count = 1</i>.",
        "<b>Step 6 — Virtual File Registration:</b> Insert the logical file record into <i>user_files</i> and map each chunk position into <i>file_chunks(file_id, chunk_index, chunk_hash)</i>."
    ]
    for step in algo_steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    story.append(Spacer(1, 8))

    # Section 4: Database Schema
    story.append(Paragraph("4. Relational Database Schema & Data Models", h1_style))
    story.append(Paragraph(
        "The relational schema is engineered to decouple physical cloud chunks from virtual user files:",
        body_style
    ))

    schema_data = [
        [Paragraph("<b>Table</b>", body_style), Paragraph("<b>Key Columns & Types</b>", body_style), Paragraph("<b>Purpose</b>", body_style)],
        [
            Paragraph("<b>chunks</b><br/>(Physical Catalog)", body_style),
            Paragraph("• chunk_hash (VARCHAR 64, PK)<br/>• size_bytes (BIGINT)<br/>• ref_count (INTEGER)<br/>• first_uploaded_at (TIMESTAMPTZ)", body_style),
            Paragraph("Stores the catalog of unique physical binary chunks in cloud storage and tracks active references across all files.", body_style)
        ],
        [
            Paragraph("<b>user_files</b><br/>(Virtual Metadata)", body_style),
            Paragraph("• id (BIGSERIAL, PK)<br/>• filename (TEXT)<br/>• user_name (TEXT)<br/>• file_size (BIGINT)<br/>• file_hash (VARCHAR 64)<br/>• total_chunks, dedup_chunks, new_chunks<br/>• upload_timestamp (TIMESTAMPTZ)<br/>• is_deduplicated (BOOLEAN)", body_style),
            Paragraph("Represents the logical files visible to users on the dashboard, tracking deduplication efficiency metrics per file.", body_style)
        ],
        [
            Paragraph("<b>file_chunks</b><br/>(Reassembly Map)", body_style),
            Paragraph("• id (BIGSERIAL, PK)<br/>• file_id (BIGINT, FK -> user_files.id)<br/>• chunk_index (INTEGER)<br/>• chunk_hash (VARCHAR 64, FK -> chunks)", body_style),
            Paragraph("The reassembly recipe! Maintains the exact sequential order of chunk hashes required to reconstruct any file.", body_style)
        ]
    ]

    schema_table = Table(schema_data, colWidths=[110, 200, 194])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, card_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(schema_table)

    story.append(Spacer(1, 10))

    # Section 5: Reconstruction & Streaming
    story.append(Paragraph("5. File Reconstruction & Byte-Perfect Streaming Pipeline", h1_style))
    story.append(Paragraph(
        "When a user clicks <b>Download</b> for file ID <i>k</i>, the system dynamically reconstructs the original file on-the-fly without keeping pre-built duplicates on disk:",
        body_style
    ))
    recon_steps = [
        "<b>Ordered Chunk Query:</b> The engine queries <i>file_chunks</i> ordered by <i>chunk_index ASC</i> to obtain the exact sequential list of hashes.",
        "<b>Chunk Retrieval:</b> For each hash, the storage adapter checks its local cache first (hit time < 1ms); if missing, it fetches the chunk binary from Supabase Object Storage.",
        "<b>Generator Stream Pipeline:</b> Chunks are yielded sequentially through Python's WSGI generator protocol, piped directly into Flask's HTTP <i>Response(stream, mimetype='application/octet-stream')</i>.",
        "<b>Zero Memory Bloat:</b> Large multi-gigabyte files can be streamed to the client with fixed, constant RAM consumption (64 KB working memory)."
    ]
    for step in recon_steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    story.append(PageBreak())

    # Section 6: Cloud Deployment
    story.append(Paragraph("6. Production Cloud Deployment Architecture", h1_style))
    story.append(Paragraph(
        "The project is engineered as a decoupled, multi-cloud microservices architecture:",
        body_style
    ))

    cloud_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Provider</b>", body_style), Paragraph("<b>Configuration & Routing</b>", body_style)],
        [
            Paragraph("<b>Frontend SPA</b>", body_style),
            Paragraph("<b>Netlify</b>", body_style),
            Paragraph("Static site hosting on high-speed global edge CDN.<br/>Proxy redirect in <code>netlify.toml</code> forwards <code>/api/*</code> to backend seamlessly with zero CORS friction.", body_style)
        ],
        [
            Paragraph("<b>Backend API</b>", body_style),
            Paragraph("<b>Render</b>", body_style),
            Paragraph("Continuous delivery from GitHub repository.<br/>Runs production Gunicorn WSGI workers on Linux container with Python 3.14.", body_style)
        ],
        [
            Paragraph("<b>Relational DB</b>", body_style),
            Paragraph("<b>Supabase (PostgreSQL)</b>", body_style),
            Paragraph("Managed PostgreSQL with Supavisor connection pooler on port 6543 (IPv4 compatible for Render environments).", body_style)
        ],
        [
            Paragraph("<b>Object Storage</b>", body_style),
            Paragraph("<b>Supabase Storage</b>", body_style),
            Paragraph("S3-compatible bucket <code>cloud-chunks</code> storing deduplicated binary payload blocks with cryptographic naming.", body_style)
        ],
        [
            Paragraph("<b>Local Dev Tunnel</b>", body_style),
            Paragraph("<b>Cloudflare Tunnel</b>", body_style),
            Paragraph("Instant public SSL URL for offline demonstrations via <code>run_all_live.bat</code>.", body_style)
        ]
    ]

    cloud_table = Table(cloud_data, colWidths=[100, 110, 294])
    cloud_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, card_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(cloud_table)

    story.append(Spacer(1, 12))

    # Section 7: Analytics & Formulae
    story.append(Paragraph("7. Storage Analytics & Space Optimization Formulas", h1_style))
    story.append(Paragraph(
        "The analytics module continuously computes live metrics across all cloud storage operations:",
        body_style
    ))
    
    analytics_formulas = [
        "<b>Total Logical Size:</b> <i>L = &Sigma; file_size<sub>i</sub></i> (Total data size users believe is stored).",
        "<b>Total Physical Size:</b> <i>P = &Sigma; size_bytes<sub>j</sub></i> (Actual unique chunks stored in Supabase).",
        "<b>Space Saved:</b> <i>S = L - P</i> (Bytes eliminated from physical cloud disk).",
        "<b>Deduplication Ratio:</b> <i>R = L / P : 1</i> (e.g., 5.4 : 1 means 5.4x storage efficiency).",
        "<b>Savings Percentage:</b> <i>% = ((L - P) / L) &times; 100%</i> (e.g., 81.5% storage cost reduction)."
    ]
    for formula in analytics_formulas:
        story.append(Paragraph(f"• {formula}", bullet_style))

    story.append(Spacer(1, 10))

    # Section 8: Reliability & Summary
    story.append(Paragraph("8. Security, Data Integrity & Crash-Resilient Architecture", h1_style))
    story.append(Paragraph(
        "• <b>Collision Resistance:</b> SHA-256 probability of hash collision is less than 1 in 10<sup>77</sup>, statistically impossible in practical cloud systems.<br/>"
        "• <b>Graceful DB Fallback:</b> In [core/db.py], if cloud PostgreSQL experiences network latency or connection pooling delays, the system automatically falls back to SQLite so the web service never crashes.<br/>"
        "• <b>Safe Deletion (Reference Counting):</b> Deleting a file decrements chunk reference counts. A physical chunk is only purged from cloud storage when its <i>ref_count == 0</i>, preventing accidental data loss.",
        body_style
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ PDF Generated successfully: {filename}")

if __name__ == "__main__":
    build_pdf()
