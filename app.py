import os
from flask import Flask, render_template, request, jsonify, send_file, Response
from core.dedup_engine import DeduplicationManager
from core.analytics import StorageAnalytics
from core.cloud_storage import CloudStorageAdapter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB upload limit

# Initialize Cloud Storage & Deduplication Engine
storage_adapter = CloudStorageAdapter(bucket_dir="cloud_storage_bucket")
dedup_manager = DeduplicationManager(db_path="metadata_catalog.db", storage_adapter=storage_adapter)
analytics = StorageAnalytics(db_path="metadata_catalog.db")


@app.route("/")
def index():
    """Serves the interactive cloud storage optimizer dashboard."""
    return render_template("index.html")


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


# --- Hugging Face Spaces & ASGI Compatibility ---
try:
    from fastapi import FastAPI
    from a2wsgi import WSGIMiddleware
    import gradio as gr
    import uvicorn

    server = FastAPI()
    with gr.Blocks(title="Cloud File Deduplication") as demo:
        gr.Markdown("# ☁️ Cloud File Deduplication & Storage Optimizer")

    app_asgi = gr.mount_gradio_app(server, demo, path="/gradio")
    server.mount("/", WSGIMiddleware(app))
except Exception as err:
    demo = None
    app_asgi = None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860 if os.environ.get("SPACE_ID") else 5000))
    if os.environ.get("SPACE_ID") and app_asgi:
        import uvicorn
        print(f"[*] Starting ASGI server on port {port} for Hugging Face Spaces...")
        uvicorn.run(app_asgi, host="0.0.0.0", port=port)
    else:
        print(f"[*] Cloud File Deduplication & Storage Optimizer started on http://127.0.0.1:{port}")
        app.run(host="0.0.0.0", port=port, debug=False)

