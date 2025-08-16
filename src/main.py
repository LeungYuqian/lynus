import os
import sys
import logging
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# --- ADD LOGGING ---
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

from flask import Flask, send_from_directory, request
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tasks import tasks_bp
from src.routes.agent import agent_bp

app = Flask(__name__)
logging.info("Flask App Created")

CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = 'lynus-ai-agent-secret-key-2024'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False

app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
app.register_blueprint(agent_bp, url_prefix='/api/agent')
logging.info("Blueprints Registered")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    logging.info("Database Initialized")

@app.route('/api/health', methods=['GET'])
def health_check():
    logging.info("Health check endpoint called")
    return {
        'status': 'healthy',
        'service': 'Lynus AI Backend',
        'version': '1.0.0'
    }, 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # --- ADD LOGGING TO SEE WHAT IS BEING CAUGHT ---
    logging.info(f"Serve static file route caught path: {path}")
    logging.info(f"Request URL: {request.url}")
    
    static_folder_path = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_folder_path):
        os.makedirs(static_folder_path)
        logging.info("Created static folder as it did not exist.")

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            logging.info("No static file found, returning fallback JSON.")
            return {
                'message': 'Lynus AI Backend is running. No static index.html found.',
                'api_docs': '/api/health'
            }, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
else:
    # This block runs when Gunicorn starts the app
    logging.info("Application starting up under Gunicorn")