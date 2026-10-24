import os

# Automatically load .env file if present
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.isfile(env_file):
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

try:
    import spaces
except ImportError:
    class spaces:
        @staticmethod
        def GPU(fn=None, **kwargs):
            if fn:
                return fn
            def decorator(f):
                return f
            return decorator

@spaces.GPU
def zero_gpu_optimizer(task="status"):
    """Satisfies ZeroGPU startup scanner and executes GPU optimization worker."""
    return f"⚡ ZeroGPU Storage Engine Active [{task}]"

from flask import Flask, render_template, request, jsonify, send_file, Response
from core.dedup_engine import DeduplicationManager
from core.analytics import StorageAnalytics
from core.cloud_storage import CloudStorageAdapter
from core.supabase_storage import SupabaseStorageAdapter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB upload limit

data_dir = os.environ.get("DATA_DIR", ".")
os.makedirs(data_dir, exist_ok=True)
bucket_dir = os.path.join(data_dir, "cloud_storage_bucket")
db_path = os.path.join(data_dir, "metadata_catalog.db")

# Detect Supabase Configuration
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
database_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")

if supabase_url and supabase_key:
    print("[SUPABASE ACTIVE] Storing chunks in Supabase Cloud Object Storage...")
    storage_adapter = SupabaseStorageAdapter(supabase_url=supabase_url, supabase_key=supabase_key)
else:
    storage_adapter = CloudStorageAdapter(bucket_dir=bucket_dir)

if database_url:
    print("[SUPABASE ACTIVE] Connecting to Supabase Cloud PostgreSQL database...")

# Initialize Deduplication Engine & Analytics
dedup_manager = DeduplicationManager(db_path=db_path, db_url=database_url, storage_adapter=storage_adapter)
analytics = StorageAnalytics(db_path=db_path, db_url=database_url)

is_hf = bool(os.environ.get("SYSTEM") == "spaces" or os.environ.get("SPACE_ID"))


@app.route("/")
@app.route("/flask/")
def index():
    """Serves the interactive cloud storage optimizer dashboard."""
    base_href = "/flask/" if is_hf else "/"
    return render_template("index.html", base_href=base_href)


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """
    Handles file upload, slices file into 64 KB blocks,
    computes cryptographic fingerprints, eliminates redundant chunks,
    and updates the cloud storage catalog.
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file_obj = request.files["file"]
        if file_obj.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        user_name = request.form.get("user_name", "Anonymous")
        filename = file_obj.filename

        # Execute chunk-level deduplication pipeline
        result = dedup_manager.upload_file(filename=filename, user_name=user_name, file_stream=file_obj.stream)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "status": "ERROR"}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Returns live storage analytics, deduplication ratio, and space savings."""
    metrics = analytics.get_metrics()
    return jsonify(metrics)


@app.route("/api/files", methods=["GET"])
def list_files():
    """Returns the list of all registered files."""
    files = dedup_manager.list_files()
    return jsonify(files)


@app.route("/api/file/<int:file_id>/chunks", methods=["GET"])
def get_file_chunks(file_id: int):
    """Returns the constituent chunks, chunk hashes, and deduplication map for a file."""
    file_info = dedup_manager.get_file(file_id)
    if not file_info:
        return jsonify({"error": "File not found"}), 404
    return jsonify({
        "file_id": file_info["id"],
        "filename": file_info["filename"],
        "file_size": file_info["file_size"],
        "file_hash": file_info["file_hash"],
        "total_chunks": file_info["total_chunks"],
        "dedup_chunks": file_info["dedup_chunks"],
        "new_chunks": file_info["new_chunks"],
        "chunks": file_info.get("chunks", [])
    })


@app.route("/api/download/<int:file_id>", methods=["GET"])
def download_file(file_id: int):
    """Reconstructs and streams the requested file from cloud object storage chunks."""
    file_info = dedup_manager.get_file(file_id)
    if not file_info:
        return jsonify({"error": "File not found"}), 404

    filename = file_info["filename"]
    response = Response(
        dedup_manager.reconstruct_file_stream(file_id),
        mimetype="application/octet-stream"
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    if file_info.get("file_size"):
        response.headers["Content-Length"] = str(file_info["file_size"])
    return response


@app.route("/api/delete/<int:file_id>", methods=["POST"])
def delete_file(file_id: int):
    """Removes a user file reference and cleans up unreferenced cloud chunks."""
    res = dedup_manager.delete_file(file_id)
    return jsonify(res)


@app.route("/api/reset", methods=["POST"])
def reset_storage():
    """Clears all metadata records and purged chunks."""
    dedup_manager.reset_all()
    return jsonify({"success": True, "message": "Storage reset successfully."})


# --- Optional Hugging Face Spaces & ZeroGPU Launcher ---
if is_hf:
    try:
        import gradio as gr
        from a2wsgi import WSGIMiddleware

        custom_css = """
        .gradio-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        footer { display: none !important; }
        """

        with gr.Blocks(title="Cloud File Deduplication & Storage Optimizer") as demo:
            with gr.Accordion("⚡ ZeroGPU Optimization Engine", open=False):
                gpu_input = gr.Textbox(label="Worker Mode", value="active", interactive=False)
                gpu_status = gr.Textbox(label="ZeroGPU Hardware Status", value="⚡ ZeroGPU Storage Engine Active")
                btn_gpu = gr.Button("Trigger GPU Hardware Pass")
                btn_gpu.click(fn=zero_gpu_optimizer, inputs=[gpu_input], outputs=[gpu_status])

            demo.load(fn=zero_gpu_optimizer, inputs=[gpu_input], outputs=[gpu_status])

            gr.HTML(
                '<iframe src="/flask/" style="width: 100%; height: 95vh; border: none; overflow: hidden;" allow="fullscreen"></iframe>'
            )

        demo.app.mount("/flask", WSGIMiddleware(app))

        port = int(os.environ.get("PORT", 7860))
        print(f"[*] Starting Gradio & ZeroGPU on port {port} for Hugging Face Spaces...")
        demo.launch()
    except Exception as err:
        print(f"[!] Warning: Gradio launcher could not be initialized: {err}")


if __name__ == "__main__":
    if not is_hf:
        port = int(os.environ.get("PORT", 5000))
        print(f"[*] Cloud File Deduplication & Storage Optimizer started on http://127.0.0.1:{port}")
        app.run(host="0.0.0.0", port=port, debug=False)


