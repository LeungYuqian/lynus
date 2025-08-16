import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tasks import tasks_bp
from src.routes.agent import agent_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = 'lynus-ai-agent-secret-key-2024'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False

app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
app.register_blueprint(agent_bp, url_prefix='/api/agent')

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health_check():
    return {
        'status': 'healthy',
        'service': 'Lynus AI Backend',
        'version': '1.0.0'
    }, 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path == "api/health":
        return health_check()

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return {
                'message': 'Lynus AI Backend is running',
                'api_docs': '/api/health',
                'endpoints': {
                    'auth': '/api/auth/*',
                    'tasks': '/api/tasks/*',
                    'agent': '/api/agent/*',
                    'users': '/api/users/*'
                }
            }, 200

if __name__ == '__main__':
    if not os.getenv('OPENROUTER_API_KEY'):
        print("Warning: OPENROUTER_API_KEY environment variable not set")
        print("You can set it by running: export OPENROUTER_API_KEY=your_api_key")

    app.run(host='0.0.0.0', port=5001, debug=True)