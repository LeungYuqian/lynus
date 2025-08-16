import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from serverless_wsgi import handle # Import the handler

app = Flask(__name__)

CORS(app, supports_credentials=True)

# All your app.config and blueprint registration remains the same
app.config['SECRET_KEY'] = 'lynus-ai-agent-secret-key-2024'
app.register_blueprint(user_bp, url_prefix='/api/users')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:////tmp/app.db" # Use /tmp for serverless environment
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# This is the function Netlify will call
def handler(event, context):
    with app.app_context():
        # It's better to create tables on-demand or via a separate script in serverless
        db.create_all() 
    return handle(app, event, context)