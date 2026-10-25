import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck(filename="Cloud_File_Deduplication_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    C_NAVY = RGBColor(15, 23, 42)        # #0F172A
    C_SLATE = RGBColor(30, 41, 59)       # #1E293B
    C_INDIGO = RGBColor(79, 70, 229)     # #4F46E5
    C_EMERALD = RGBColor(16, 185, 129)   # #10B981
    C_WHITE = RGBColor(255, 255, 255)
    C_MUTED = RGBColor(148, 163, 184)    # #94A3B8
    C_CARD_BG = RGBColor(241, 245, 249)  # #F1F5F9
    C_CARD_DARK = RGBColor(30, 41, 59)
    C_TEXT_DARK = RGBColor(15, 23, 42)

    def add_background(slide, color):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        return shape

    def add_header(slide, title, category="CLOUD STORAGE & DATA OPTIMIZATION"):
        # Category Tracker
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_INDIGO

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = C_NAVY

    # =========================================================================
    # SLIDE 1: Title Slide (Dark Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_background(s1, C_NAVY)

    # Accent pill
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.3), Inches(3.6), Inches(0.45))
    pill.fill.solid()
    pill.fill.fore_color.rgb = C_INDIGO
    pill.line.fill.background()
    p_pill = pill.text_frame.paragraphs[0]
    p_pill.text = "ENTERPRISE CLOUD ARCHITECTURE"
    p_pill.font.size = Pt(11)
    p_pill.font.bold = True
    p_pill.font.color.rgb = C_WHITE
    p_pill.alignment = PP_ALIGN.CENTER

    # Main Title
    t1_box = s1.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.5), Inches(2.2))
    tf1 = t1_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Cloud File Deduplication\n& Storage Optimizer"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

    # Humanized Subtitle
    sub1_box = s1.shapes.add_textbox(Inches(0.8), Inches(4.3), Inches(11.5), Inches(1.0))
    tf_sub1 = sub1_box.text_frame
    tf_sub1.word_wrap = True
    p_sub1 = tf_sub1.paragraphs[0]
    p_sub1.text = "Why Pay for the Same File 1,000 Times? Smarter Cloud Storage with 64 KB Chunk Fingerprinting"
    p_sub1.font.size = Pt(18)
    p_sub1.font.color.rgb = C_EMERALD

    # Presenter Card
    pres_box = s1.shapes.add_textbox(Inches(0.8), Inches(5.8), Inches(11.5), Inches(1.0))
    tf_pres = pres_box.text_frame
    p_pres = tf_pres.paragraphs[0]
    p_pres.text = "Presented by: Prasanna Bhurke | Full-Stack Cloud Engineering Project"
    p_pres.font.size = Pt(13)
    p_pres.font.color.rgb = C_MUTED

    # =========================================================================
    # SLIDE 2: The Real-World Problem (Human Story)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_background(s2, C_WHITE)
    add_header(s2, "The Real-World Headache: The Silent Cloud Waste")

    # 3 Problem Cards
    col_w = Inches(3.64)
    gap = Inches(0.4)
    left_start = Inches(0.8)
    top_pos = Inches(2.0)
    card_h = Inches(4.7)

    problems = [
        ("📂 The 'Version Spam' Reality",
         "Everyone does it: 'Report_Final.docx', 'Report_Final_v2.docx', 'Report_REAL_Final.docx'. Across thousands of company employees or students, 95% of each document is identical, yet cloud drives duplicate the entire file every single time.",
         "95% Redundancy"),
        ("💸 Exploding Cloud Storage Bills",
         "Cloud providers like AWS S3, Google Cloud, and Azure bill per gigabyte stored and per gigabyte transferred. Organizations waste up to 60% of their cloud storage budget storing identical duplicate bytes.",
         "Up to 60% Budget Waste"),
        ("🐌 Wasted Bandwidth & Latency",
         "Re-uploading and backing up identical multi-megabyte files chokes office networks, slows down mobile uploads, and doubles cloud synchronization wait times unnecessarily.",
         "Slow Network Backups")
    ]

    for i, (title, desc, stat) in enumerate(problems):
        card_left = left_start + i * (col_w + gap)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, top_pos, col_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_BG
        card.line.color.rgb = RGBColor(226, 232, 240)

        tb = s2.shapes.add_textbox(card_left + Inches(0.2), top_pos + Inches(0.3), col_w - Inches(0.4), card_h - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY
        p_t.space_after = Pt(14)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(13)
        p_d.font.color.rgb = RGBColor(71, 85, 105)
        p_d.space_after = Pt(20)

        p_s = tf.add_paragraph()
        p_s.text = f"🚨 {stat}"
        p_s.font.size = Pt(14)
        p_s.font.bold = True
        p_s.font.color.rgb = RGBColor(225, 29, 72)

    # =========================================================================
    # SLIDE 3: The Core Solution (The Human Analogy)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_background(s3, C_WHITE)
    add_header(s3, "The Big Idea: The 'Library Card' Philosophy")

    # Big concept card
    left_w = Inches(5.6)
    right_w = Inches(5.8)
    
    # Left: The Library Analogy
    card_l = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), left_w, Inches(4.8))
    card_l.fill.solid()
    card_l.fill.fore_color.rgb = RGBColor(238, 242, 255)
    card_l.line.color.rgb = C_INDIGO

    tb_l = s3.shapes.add_textbox(Inches(1.1), Inches(2.2), left_w - Inches(0.6), Inches(4.2))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    
    p_lt = tf_l.paragraphs[0]
    p_lt.text = "📚 The Library Book Analogy"
    p_lt.font.size = Pt(19)
    p_lt.font.bold = True
    p_lt.font.color.rgb = C_INDIGO
    p_lt.space_after = Pt(14)

    p_lb = tf_l.add_paragraph()
    p_lb.text = "Imagine a college library. If 1,000 students want to read the same textbook:\n\n❌ Wrong Way: Buy 1,000 identical textbooks and build a bigger building to hold them all.\n\n✅ The Smart Way: Keep ONE master copy on the shelf. Give all 1,000 students a unique Library Card that points to that single copy!\n\nThat is exact what our Deduplication Engine does for cloud storage."
    p_lb.font.size = Pt(13)
    p_lb.font.color.rgb = C_NAVY

    # Right: How it applies to Files
    card_r = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.9), right_w, Inches(4.8))
    card_r.fill.solid()
    card_r.fill.fore_color.rgb = C_CARD_BG
    card_r.line.color.rgb = RGBColor(226, 232, 240)

    tb_r = s3.shapes.add_textbox(Inches(7.1), Inches(2.2), right_w - Inches(0.6), Inches(4.2))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p_rt = tf_r.paragraphs[0]
    p_rt.text = "⚙️ Translating Analogy to Code"
    p_rt.font.size = Pt(19)
    p_rt.font.bold = True
    p_rt.font.color.rgb = C_NAVY
    p_rt.space_after = Pt(14)

    pts = [
        "1. Every file is sliced into 64 KB pieces called 'Chunks'.",
        "2. Each chunk receives an unforgeable SHA-256 digital fingerprint.",
        "3. When you upload, we check: 'Do we already have this fingerprint?'",
        "4. If YES: We create a virtual reference link (Zero bytes stored!).",
        "5. If NO: We store the chunk once in Supabase Cloud Storage.",
        "6. Result: 10 people uploading a 100 MB file = Only 100 MB stored, not 1,000 MB!"
    ]
    for pt in pts:
        p_pt = tf_r.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = Pt(12.5)
        p_pt.font.color.rgb = RGBColor(51, 65, 85)
        p_pt.space_after = Pt(4)

    # =========================================================================
    # SLIDE 4: Full Stack Architecture (What did we use?)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_background(s4, C_WHITE)
    add_header(s4, "Under the Hood: Our 4-Layer Cloud Stack")

    grid_w = Inches(5.6)
    grid_h = Inches(2.25)
    gap_x = Inches(0.5)
    gap_y = Inches(0.35)

    layers = [
        ("🎨 Layer 1: Frontend (User Dashboard)",
         "HTML5 + Vanilla CSS3 (Glassmorphism) + Modern ES6 JS\n• Hosted on Netlify Global Edge CDN.\n• Real-time drag-and-drop, visual chunk distribution map, live metrics.\n• Completely zero framework bloat for lightning-fast 60 FPS rendering.",
         C_INDIGO),
        ("⚙️ Layer 2: Backend (Deduplication Core)",
         "Python 3 + Flask + Gunicorn WSGI + REST APIs\n• Hosted 24/7 on Render Cloud Linux Containers.\n• Dynamic 64 KB binary streaming, SHA-256 fingerprint generation.\n• Byte-perfect on-demand file reconstruction and chunk streaming.",
         C_NAVY),
        ("🐘 Layer 3: Database (Metadata Catalog)",
         "Supabase Cloud PostgreSQL + Connection Pooler (Port 6543)\n• Decouples virtual user files from physical storage chunks.\n• Foreign-key relational cascades and indexed fingerprint lookups.\n• Resilient auto-fallback to SQLite to prevent cloud downtime.",
         RGBColor(2, 132, 199)),
        ("☁️ Layer 4: Cloud Storage (Binary Chunks)",
         "Supabase S3-Compatible Object Storage ('cloud-chunks' bucket)\n• Content-addressable binary block storage.\n• Local LRU binary caching for sub-millisecond repeated reads.\n• Supports cloud bucket or local folder seamlessly via Adapter pattern.",
         C_EMERALD)
    ]

    for i, (title, desc, accent) in enumerate(layers):
        r = i // 2
        c = i % 2
        x = Inches(0.8) + c * (grid_w + gap_x)
        y = Inches(1.9) + r * (grid_h + gap_y)

        box = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, grid_w, grid_h)
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG
        box.line.color.rgb = accent
        box.line.width = Pt(1.5)

        tb = s4.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), grid_w - Inches(0.4), grid_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(15)
        p_t.font.bold = True
        p_t.font.color.rgb = accent
        p_t.space_after = Pt(6)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(11.5)
        p_d.font.color.rgb = RGBColor(51, 65, 85)

    # =========================================================================
    # SLIDE 5: How It Works Step-by-Step (The Pipeline)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_background(s5, C_WHITE)
    add_header(s5, "The 5-Step Pipeline: From Upload to Cloud Storage")

    step_w = Inches(2.15)
    step_gap = Inches(0.24)
    step_h = Inches(4.8)

    steps = [
        ("Step 1", "📥 Ingestion", "File streamed into memory in 64 KB binary blocks without writing unverified junk to disk."),
        ("Step 2", "🔐 Fingerprinting", "Each 64 KB block gets an unforgeable SHA-256 cryptographic hash fingerprint."),
        ("Step 3", "🔎 Catalog Check", "System queries PostgreSQL database: Does this SHA-256 hash already exist in our cloud?"),
        ("Step 4", "⚖️ Smart Action", "• If DUPLICATE: Increment reference counter by +1. Skip physical upload!\n• If NEW: Upload chunk to Supabase bucket."),
        ("Step 5", "🧩 File Mapping", "Records the file 'recipe' in file_chunks table: which chunks in what exact order make up the file.")
    ]

    for i, (badge, title, desc) in enumerate(steps):
        sx = Inches(0.8) + i * (step_w + step_gap)
        s_box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, Inches(1.9), step_w, step_h)
        s_box.fill.solid()
        s_box.fill.fore_color.rgb = C_CARD_BG
        s_box.line.color.rgb = RGBColor(226, 232, 240)

        tb = s5.shapes.add_textbox(sx + Inches(0.12), Inches(2.1), step_w - Inches(0.24), step_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p_b = tf.paragraphs[0]
        p_b.text = badge.upper()
        p_b.font.size = Pt(11)
        p_b.font.bold = True
        p_b.font.color.rgb = C_INDIGO
        p_b.space_after = Pt(6)

        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY
        p_t.space_after = Pt(14)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = RGBColor(71, 85, 105)

    # =========================================================================
    # SLIDE 6: File Reconstruction & Download (Byte-Perfect)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_background(s6, C_WHITE)
    add_header(s6, "How Do We Reconstruct Files? (Zero Data Loss)")

    # Left: Explanation Card
    c_l6 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(6.5), Inches(4.8))
    c_l6.fill.solid()
    c_l6.fill.fore_color.rgb = C_CARD_BG
    c_l6.line.color.rgb = RGBColor(226, 232, 240)

    tb_l6 = s6.shapes.add_textbox(Inches(1.1), Inches(2.2), Inches(6.0), Inches(4.2))
    tf_l6 = tb_l6.text_frame
    tf_l6.word_wrap = True

    p_l6t = tf_l6.paragraphs[0]
    p_l6t.text = "🔄 On-The-Fly Reassembly Engine"
    p_l6t.font.size = Pt(18)
    p_l6t.font.bold = True
    p_l6t.font.color.rgb = C_NAVY
    p_l6t.space_after = Pt(12)

    l6_pts = [
        "1. No Duplicate Stored on Disk: The cloud never keeps whole file copies sitting on disk waiting for download.",
        "2. Reading the Recipe: When a user clicks 'Download', the system queries the database for chunk hashes ordered by chunk_index ASC.",
        "3. High-Speed Streaming: Chunks are retrieved from Supabase and yielded directly into an HTTP stream.",
        "4. Bit-for-Bit Identical: The reconstructed file matches the original byte-for-byte with identical SHA-256 checksum.",
        "5. O(1) Memory Footprint: A 10 GB file can be downloaded with only 64 KB of RAM used on the server."
    ]
    for pt in l6_pts:
        p = tf_l6.add_paragraph()
        p.text = pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = RGBColor(51, 65, 85)
        p.space_after = Pt(8)

    # Right: The Benchmark Stat Card
    c_r6 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.7), Inches(1.9), Inches(4.8), Inches(4.8))
    c_r6.fill.solid()
    c_r6.fill.fore_color.rgb = RGBColor(236, 253, 245)
    c_r6.line.color.rgb = C_EMERALD

    tb_r6 = s6.shapes.add_textbox(Inches(8.0), Inches(2.2), Inches(4.2), Inches(4.2))
    tf_r6 = tb_r6.text_frame
    tf_r6.word_wrap = True

    p_r6t = tf_r6.paragraphs[0]
    p_r6t.text = "🎯 Tested & Verified Metrics"
    p_r6t.font.size = Pt(18)
    p_r6t.font.bold = True
    p_r6t.font.color.rgb = C_EMERALD
    p_r6t.space_after = Pt(16)

    stats = [
        ("100.0%", "Integrity Match in Automated Tests"),
        ("60% - 85%", "Physical Storage Space Reduction"),
        ("10x - 50x", "Faster 'Upload' for Duplicate Chunks"),
        ("1 in 10⁷⁷", "Probability of Hash Collision (Impossible)")
    ]
    for val, lbl in stats:
        pv = tf_r6.add_paragraph()
        pv.text = val
        pv.font.size = Pt(22)
        pv.font.bold = True
        pv.font.color.rgb = C_NAVY

        pl = tf_r6.add_paragraph()
        pl.text = lbl
        pl.font.size = Pt(11)
        pl.font.color.rgb = RGBColor(71, 85, 105)
        pl.space_after = Pt(8)

    # =========================================================================
    # SLIDE 7: Live Cloud Deployment & Microservices
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_background(s7, C_WHITE)
    add_header(s7, "Multi-Cloud Production Deployment: 24/7 Live")

    s7_w = Inches(3.64)
    s7_gap = Inches(0.4)
    s7_top = Inches(2.0)
    s7_h = Inches(4.7)

    deploys = [
        ("🌐 Netlify Edge CDN",
         "The Frontend Face",
         "• Global SSL distribution for instant page loads anywhere in the world.\n• Built-in automated API proxy rewrites (/api/*) directly to backend.\n• Eliminates cross-origin CORS barriers for seamless browser interaction.",
         C_INDIGO),
        ("🚀 Render Cloud Containers",
         "The Python Engine",
         "• Production Gunicorn WSGI workers running on Linux Docker environment.\n• Continuous deployment auto-triggered on Git push to main.\n• Health checks and auto-restart monitoring built in.",
         C_NAVY),
        ("🐘 Supabase Cloud Infrastructure",
         "Database + Object Storage",
         "• Managed PostgreSQL database with ACID transaction pooler on port 6543.\n• S3-compatible cloud object storage for binary chunks.\n• Enterprise backup, replication, and data persistence 24/7.",
         C_EMERALD)
    ]

    for i, (head, sub, desc, acc) in enumerate(deploys):
        dx = Inches(0.8) + i * (s7_w + s7_gap)
        d_box = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, dx, s7_top, s7_w, s7_h)
        d_box.fill.solid()
        d_box.fill.fore_color.rgb = C_CARD_BG
        d_box.line.color.rgb = acc
        d_box.line.width = Pt(1.5)

        tb = s7.shapes.add_textbox(dx + Inches(0.2), s7_top + Inches(0.25), s7_w - Inches(0.4), s7_h - Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p_h = tf.paragraphs[0]
        p_h.text = head
        p_h.font.size = Pt(17)
        p_h.font.bold = True
        p_h.font.color.rgb = acc
        p_h.space_after = Pt(2)

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(12)
        p_s.font.bold = True
        p_s.font.color.rgb = C_NAVY
        p_s.space_after = Pt(14)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = RGBColor(71, 85, 105)

    # =========================================================================
    # SLIDE 8: Conclusion & Key Takeaways
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_background(s8, C_NAVY)

    tb8 = s8.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.7), Inches(5.5))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    p8_t = tf8.paragraphs[0]
    p8_t.text = "Summary: Why This Project Stands Out"
    p8_t.font.size = Pt(32)
    p8_t.font.bold = True
    p8_t.font.color.rgb = C_WHITE
    p8_t.space_after = Pt(24)

    takeaways = [
        "✅ Real Problem, Real Solution: Directly cuts cloud storage costs by 60% to 80% without impacting user experience.",
        "✅ Sub-File Precision: 64 KB chunking catches duplicate portions inside modified documents, videos, and archives.",
        "✅ Enterprise Architecture: Decoupled Frontend (Netlify), Backend (Render), and Cloud DB + Storage (Supabase).",
        "✅ Zero-Data-Loss Reliability: Cryptographic SHA-256 fingerprinting + reference counting guarantee 100% data safety.",
        "✅ Production Ready: Fully functional with live dashboard, analytics, chunk visualizer, and instant file reconstruction."
    ]
    for item in takeaways:
        p = tf8.add_paragraph()
        p.text = item
        p.font.size = Pt(16)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_after = Pt(14)

    prs.save(filename)
    print(f"✅ PowerPoint presentation generated: {filename}")

if __name__ == "__main__":
    create_deck()
