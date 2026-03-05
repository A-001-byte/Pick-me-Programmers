import sys
import os
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_cors import CORS
from backend.routes import api_bp, limiter
from backend.database import init_db


def create_app():
    # Initialize the database on startup
    init_db()

    app = Flask(__name__)
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
