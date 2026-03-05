import sys
import os
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_cors import CORS
from backend.routes import api_bp, limiter
from backend.database import init_db
from core.pipeline import SurveillancePipeline
import threading


def create_app():
    # Initialize the database on startup
    init_db()

    # Start the AI pipeline in a background thread
    def run_pipeline():
        # Resolve project root (one level up from this file)
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        person_model = os.path.join(root_dir, "models", "yolov8m_fixed.pt")
        weapon_model = os.path.join(root_dir, "models", "weapon_detector_fixed.pt")
        
        # Check if models exist and are valid files
        if not os.path.isfile(person_model):
            print(f"[backend] Warning: {person_model} not found. Falling back to backend/models/yolov8n.pt")
            person_model = os.path.join(os.path.dirname(__file__), "models", "yolov8n.pt")
        
        if not os.path.isfile(weapon_model):
            print(f"[backend] Warning: {weapon_model} not found. Weapon detection may be disabled or use default.")
            weapon_model = None

        print(f"[backend] Starting AI Surveillance Pipeline in background...")
        print(f"        > Person Model: {person_model}")
        print(f"        > Weapon Model: {weapon_model}")
        try:
            pipeline = SurveillancePipeline(
                source=0, # Default webcam
                person_model=person_model,
                weapon_model=weapon_model,
                headless=True,
                imgsz=320,       # Smaller for faster inference
                weapon_skip=8,   # Run weapon detection less frequently
                risk_skip=5,     # Run risk engine less frequently
            )
            pipeline.run()
        except Exception as e:
            print(f"[backend] AI Pipeline error: {e}")

    app = Flask(__name__)

    # Start the AI pipeline thread after Flask app is created
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()
    limiter.init_app(app)

    # --- SECRET_KEY: load from env, fail in production if missing ---
    flask_env = os.environ.get("FLASK_ENV", "development")
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        if flask_env == "development":
            # Generate a random dev-only secret (not stable across restarts)
            secret = secrets.token_hex(32)
            print("[WARNING] JWT_SECRET not set — using random dev secret. "
                  "Set JWT_SECRET env var for production.")
        else:
            raise RuntimeError(
                "JWT_SECRET environment variable is required in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
    app.config['SECRET_KEY'] = secret

    # --- CORS: restrict origins via env var ---
    allowed_origins = os.environ.get(
        "TRUSTED_DASHBOARD_HOSTS", "http://localhost:3000"
    ).split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    # Register API routes Blueprint
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Surveillance API Backend is running!"

    return app


if __name__ == '__main__':
    app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host='0.0.0.0', port=5000, debug=debug)
