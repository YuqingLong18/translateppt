"""Flask application entrypoint for the document translator prototype."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional
from uuid import uuid4

from flask import Flask, abort, jsonify, request, send_from_directory, session, redirect
from langdetect import detect, LangDetectException
from werkzeug.utils import secure_filename

from .config import settings
from .document_handler import TextElement, get_document_handler
from .translator import OpenRouterTranslator, TranslationConfig, TranslationError
from .auth_middleware import require_auth, get_current_user, verify_credentials, check_session

LOGGER = logging.getLogger(__name__)


@dataclass
class FileRecord:
    file_id: str
    original_name: str
    stored_name: str
    path: Path
    size: int
    kind: str  # "source" or "translated"


class FileRegistry:
    """In-memory registry for uploaded and processed files."""

    def __init__(self) -> None:
        self._records: Dict[str, FileRecord] = {}

    def add(self, record: FileRecord) -> None:
        self._records[record.file_id] = record

    def get(self, file_id: str) -> Optional[FileRecord]:
        return self._records.get(file_id)


registry = FileRegistry()


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(settings.static_folder),
        static_url_path="",
    )

    app.config["SECRET_KEY"] = settings.secret_key
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length
    app.config["UPLOAD_FOLDER"] = str(settings.upload_folder)
    app.config["OUTPUT_FOLDER"] = str(settings.output_folder)
    app.config["DEFAULT_MODEL"] = settings.default_model

    settings.upload_folder.mkdir(parents=True, exist_ok=True)
    settings.output_folder.mkdir(parents=True, exist_ok=True)

    register_routes(app)
    return app


def register_routes(app: Flask) -> None:
    @app.get("/favicon.ico")
    def favicon():
        """Return 204 No Content for favicon requests to avoid 404s."""
        return "", 204
    
    @app.get("/")
    def index():
        # Check if user is authenticated
        if not check_session():
            return redirect("/login")
        return app.send_static_file("index.html")
    
    @app.get("/login")
    def login_page():
        # If already authenticated, redirect to main app
        if check_session():
            return redirect("/")
        return app.send_static_file("login.html")
    
    @app.post("/api/auth/login")
    def login():
        """Handle login request."""
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required"}), 400
        
        user_info = verify_credentials(username, password)
        
        if user_info:
            # Set session
            session["authenticated"] = True
            session["user_id"] = user_info["id"]
            session["username"] = user_info["username"]
            return jsonify({"success": True, "user": user_info})
        else:
            return jsonify({"success": False, "error": "Invalid username or password"}), 401
    
    @app.post("/api/auth/logout")
    def logout():
        """Handle logout request."""
        session.clear()
        return jsonify({"success": True})
    
    @app.get("/api/auth/check")
    def check_auth():
        """Check if user is authenticated."""
        user_info = check_session()
        if user_info:
            return jsonify({"authenticated": True, "user": user_info})
        # Return 200 with authenticated: false instead of 401 to avoid console errors
        return jsonify({"authenticated": False}), 200

    @app.get("/health")
    def health() -> tuple:
        return {"status": "ok"}, 200

    @app.post("/upload")
    @require_auth
    def upload(user_info):
        if "file" not in request.files:
            abort(400, description="No file part in request")

        file_storage = request.files["file"]
        if file_storage.filename == "":
            abort(400, description="No file selected")

        if not _allowed_file(file_storage.filename):
            abort(400, description="Unsupported file type")

        file_id = uuid4().hex
        original_name = secure_filename(file_storage.filename)
        extension = Path(original_name).suffix.lower() or ".bin"
        stored_name = f"{file_id}{extension}"
        upload_path = Path(app.config["UPLOAD_FOLDER"]) / stored_name
        file_storage.save(upload_path)
        size = upload_path.stat().st_size

        record = FileRecord(
            file_id=file_id,
            original_name=original_name,
            stored_name=stored_name,
            path=upload_path,
            size=size,
            kind="source",
        )
        registry.add(record)

        return jsonify({"file_id": file_id, "filename": original_name, "size": size})

    @app.post("/translate")
    @require_auth
    def translate(user_info):
        payload = request.get_json(silent=True) or request.form
        file_id = payload.get("file_id") if payload else None
        if not file_id:
            abort(400, description="file_id is required")

        record = registry.get(file_id)
        if not record:
            abort(404, description="File not found")

        target_lang = (payload.get("target_lang") or "").strip()
        if not target_lang:
            abort(400, description="target_lang is required")

        source_lang = (payload.get("source_lang") or "").strip() or None
        font_name = (payload.get("font") or "").strip() or None
        api_key = (payload.get("api_key") or settings.openrouter_api_key or "").strip()
        model = settings.default_model

        try:
            handler = get_document_handler(record.path)
        except ValueError as exc:
            abort(400, description=str(exc))
        elements = handler.extract_text()

        if not elements:
            abort(400, description="No translatable text found in document")

        if source_lang in {None, "auto"}:
            source_lang = _detect_language(elements)

        translator = OpenRouterTranslator(
            TranslationConfig(
                api_key=api_key,
                model=model,
                source_lang=source_lang,
                target_lang=target_lang,
            )
        )

        try:
            translated_texts = translator.translate_texts([element.text for element in elements])
        except TranslationError as exc:
            abort(502, description=str(exc))

        mapping = {element.element_id: translated for element, translated in zip(elements, translated_texts)}

        output_id = uuid4().hex
        original_suffix = Path(record.original_name).suffix or Path(record.path).suffix
        output_filename = f"{Path(record.original_name).stem}_{target_lang}{original_suffix}"
        stored_name = f"{output_id}{original_suffix}"
        output_path = Path(app.config["OUTPUT_FOLDER"]) / stored_name
        handler.apply_translations(mapping, output_path, font_name=font_name)

        output_record = FileRecord(
            file_id=output_id,
            original_name=output_filename,
            stored_name=stored_name,
            path=output_path,
            size=output_path.stat().st_size,
            kind="translated",
        )
        registry.add(output_record)

        response = {
            "file_id": output_id,
            "download_url": f"/download/{output_id}",
            "filename": output_filename,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }
        return jsonify(response)

    @app.get("/download/<file_id>")
    def download(file_id: str):
        record = registry.get(file_id)
        if not record or not record.path.exists():
            abort(404)
        directory = record.path.parent
        return send_from_directory(directory, record.path.name, as_attachment=True, download_name=record.original_name)

    @app.get("/languages")
    def languages():
        languages = [
            {"code": "auto", "label": "Auto Detect"},
            {"code": "en", "label": "English"},
            {"code": "zh", "label": "Chinese"},
            {"code": "ja", "label": "Japanese"},
            {"code": "es", "label": "Spanish"},
            {"code": "fr", "label": "French"},
            {"code": "de", "label": "German"},
        ]
        return jsonify(languages)

    @app.get("/api/user")
    def get_user():
        """Get current user info."""
        user_info = get_current_user()
        if user_info:
            return jsonify({
                "authenticated": True,
                "username": user_info.get("username"),
                "user_type": "user"  # Simple user type for compatibility
            })
        return jsonify({"authenticated": False}), 401


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in settings.allowed_extensions


def _detect_language(elements: Iterable[TextElement]) -> Optional[str]:
    for element in elements:
        try:
            detection = detect(element.text)
            if detection:
                return detection
        except LangDetectException:
            continue
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application = create_app()
    application.run(debug=True)
