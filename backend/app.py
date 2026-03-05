import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_cors import CORS
from backend.routes import api_bp
from backend.database import init_db

def create_app():
    # Initialize the database on startup
    init_db()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev_surveillance_key'
    
    # Enable CORS so Next.js dashboard can call the API
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register API routes Blueprint
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Surveillance API Backend is running!"

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
