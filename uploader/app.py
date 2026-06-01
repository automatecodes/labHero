import json
import os
from pathlib import Path
from time import time
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

app = Flask(__name__)
MEDIA_DIR = Path(os.environ.get("MEDIA_DIR", "/app/media"))
HTML_DIR = Path(os.environ.get("HTML_DIR", "/app/html"))
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "20"))
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "svg"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v", "ogv"}
ALLOWED_CSS_EXTENSIONS = {"css"}
ASSETS_CSS_DIR = Path(os.environ.get("HTML_DIR", "/app/html")) / "assets" / "css"
ALLOWED_UNIFIED_FILENAMES = {"labHero_unified.css", "labHero_unified.json"}

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def allowed(filename: str, extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions


def save_current_logo(file, manifest_name: str, prefix: str):
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    original = secure_filename(file.filename)
    if not original:
        return None, (jsonify({"error": "Nombre de archivo vacío"}), 400)
    if not allowed(original, ALLOWED_IMAGE_EXTENSIONS):
        return None, (jsonify({"error": "Formato no permitido", "allowed": sorted(ALLOWED_IMAGE_EXTENSIONS)}), 400)

    ext = original.rsplit(".", 1)[1].lower()
    target_name = f"{prefix}.{ext}"
    target = MEDIA_DIR / target_name

    for old in MEDIA_DIR.glob(f"{prefix}.*"):
        try:
            old.unlink()
        except OSError:
            pass

    file.save(target)
    manifest = {
        "url": f"/media/{target_name}",
        "filename": target_name,
        "original_filename": original,
        "updated_at": int(time()),
    }
    (MEDIA_DIR / manifest_name).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest, None


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/upload-logo")
def upload_logo():
    if "logo" not in request.files:
        return jsonify({"error": "Campo de archivo esperado: logo"}), 400
    manifest, error = save_current_logo(request.files["logo"], "logo.json", "logo-current")
    if error:
        return error
    return jsonify(manifest)


@app.post("/api/upload-image-logo")
def upload_image_logo():
    if "logo" not in request.files:
        return jsonify({"error": "Campo de archivo esperado: logo"}), 400
    manifest, error = save_current_logo(request.files["logo"], "image-logo.json", "image-logo-current")
    if error:
        return error
    return jsonify(manifest)


@app.get("/api/list-media")
def list_media():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    videos = []
    images = []
    css = []
    for item in sorted(MEDIA_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_file():
            continue
        ext = item.suffix.lower().lstrip(".")
        row = {"name": item.name, "url": f"/media/{item.name}", "size_bytes": item.stat().st_size}
        if ext in ALLOWED_VIDEO_EXTENSIONS:
            videos.append(row)
        elif ext in ALLOWED_IMAGE_EXTENSIONS and item.name not in {"logo.json", "image-logo.json"}:
            images.append(row)
        elif ext in ALLOWED_CSS_EXTENSIONS:
            css.append(row)

    # CSS también en raíz html y assets/css para mantener compatibilidad con versiones anteriores.
    css_roots = [HTML_DIR, HTML_DIR / "assets", HTML_DIR / "assets" / "css"]
    seen = {c["url"] for c in css}
    for root in css_roots:
        if not root.exists():
            continue
        for item in sorted(root.glob("*.css"), key=lambda p: p.name.lower()):
            url = f"/{item.name}" if root == HTML_DIR else (f"/assets/{item.name}" if root == HTML_DIR / "assets" else f"/assets/css/{item.name}")
            if url in seen:
                continue
            seen.add(url)
            css.append({"name": item.name, "url": url, "size_bytes": item.stat().st_size})

    return jsonify({"videos": videos, "images": images, "css": css})


@app.get("/api/list-css")
def list_css():
    data = list_media().get_json()
    return jsonify({"files": data.get("css", [])})


@app.post("/api/save-asset")
def save_asset():
    """Guarda labHero_unified.css o labHero_unified.json en /assets/css/ sobrescribiendo."""
    data = request.get_json(silent=True) or {}
    filename = (data.get("filename") or "").strip()
    content  = data.get("content") or ""

    if filename not in ALLOWED_UNIFIED_FILENAMES:
        return jsonify({
            "error": f"Nombre no permitido. Solo se aceptan: {sorted(ALLOWED_UNIFIED_FILENAMES)}"
        }), 400

    if not content:
        return jsonify({"error": "Contenido vacío"}), 400

    ASSETS_CSS_DIR.mkdir(parents=True, exist_ok=True)
    target = ASSETS_CSS_DIR / filename
    target.write_text(content, encoding="utf-8")

    return jsonify({
        "ok": True,
        "path": f"/assets/css/{filename}",
        "bytes": len(content.encode("utf-8")),
        "updated_at": int(time())
    })
