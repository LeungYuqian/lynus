from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Task
from src.agent_engine import LynusAgent
import threading
import os

agent_bp = Blueprint('agent', __name__)

def require_auth(f):
    """認證裝飾器"""
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            session.pop('user_id', None)
            return jsonify({'error': 'User not found or inactive'}), 401
        
        return f(user, *args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

def execute_task_async(task_id: int, openrouter_api_key: str):
    """異步執行任務"""
    try:
        agent = LynusAgent(openrouter_api_key)
        result = agent.execute_task(task_id, openrouter_api_key)
        print(f"Task {task_id} execution result: {result}")
    except Exception as e:
        print(f"Task {task_id} execution failed: {str(e)}")

@agent_bp.route('/execute', methods=['POST'])
@require_auth
def execute_task(user):
    """執行Agent任務"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        description = data.get('description', '').strip()
        task_type = data.get('task_type', 'general').strip()
        title = data.get('title', '').strip()
        
        if not description:
            return jsonify({'error': 'Task description is required'}), 400
        
        # 如果沒有提供標題，從描述中生成
        if not title:
            title = description[:50] + ('...' if len(description) > 50 else '')
        
        # 驗證任務類型
        valid_types = ['image', 'slides', 'webpage', 'spreadsheet', 'visualization', 'general']
        if task_type not in valid_types:
            task_type = 'general'
        
        # 創建新任務
        task = Task(
            user_id=user.id,
            title=title,
            description=description,
            task_type=task_type,
            status='pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        # 獲取OpenRouter API密鑰
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            # 如果沒有環境變量，嘗試從請求中獲取
            openrouter_api_key = data.get('api_key')
            
        if not openrouter_api_key:
            return jsonify({'error': 'OpenRouter API key is required'}), 400
        
        # 在後台線程中執行任務
        thread = threading.Thread(
            target=execute_task_async,
            args=(task.id, openrouter_api_key)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Task execution started',
            'task': task.to_dict()
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to start task execution: {str(e)}'}), 500

@agent_bp.route('/quick-execute', methods=['POST'])
@require_auth
def quick_execute(user):
    """快速執行 - 根據功能按鈕類型"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        task_type = data.get('task_type', '').strip()
        prompt = data.get('prompt', '').strip()
        
        if not task_type or not prompt:
            return jsonify({'error': 'Task type and prompt are required'}), 400
        
        # 根據任務類型生成描述
        type_descriptions = {
            'image': f'生成圖像：{prompt}',
            'slides': f'創建簡報：{prompt}',
            'webpage': f'構建網頁：{prompt}',
            'spreadsheet': f'處理電子表格：{prompt}',
            'visualization': f'創建數據可視化：{prompt}',
            'general': prompt
        }
        
        description = type_descriptions.get(task_type, prompt)
        title = f"{task_type.title()} - {prompt[:30]}{'...' if len(prompt) > 30 else ''}"
        
        # 創建任務
        task = Task(
            user_id=user.id,
            title=title,
            description=description,
            task_type=task_type,
            status='pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        # 獲取API密鑰
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            openrouter_api_key = data.get('api_key')
            
        if not openrouter_api_key:
            return jsonify({'error': 'OpenRouter API key is required'}), 400
        
        # 在後台執行
        thread = threading.Thread(
            target=execute_task_async,
            args=(task.id, openrouter_api_key)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Quick task execution started',
            'task': task.to_dict()
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to start quick execution: {str(e)}'}), 500

@agent_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """獲取Agent能力列表"""
    capabilities = {
        'task_types': [
            {
                'id': 'image',
                'name': 'Image',
                'description': '圖像生成和編輯',
                'icon': '🖼️',
                'color': 'orange'
            },
            {
                'id': 'slides',
                'name': 'Slides',
                'description': '簡報製作',
                'icon': '📊',
                'color': 'green'
            },
            {
                'id': 'webpage',
                'name': 'Webpage',
                'description': '網頁設計和開發',
                'icon': '🌐',
                'color': 'red'
            },
            {
                'id': 'spreadsheet',
                'name': 'Spreadsheet',
                'description': '電子表格處理',
                'icon': '📈',
                'color': 'blue',
                'badge': 'New'
            },
            {
                'id': 'visualization',
                'name': 'Visualization',
                'description': '數據可視化',
                'icon': '📊',
                'color': 'red'
            },
            {
                'id': 'general',
                'name': 'More',
                'description': '其他功能',
                'icon': '➕',
                'color': 'green'
            }
        ],
        'features': [
            'TAO循環執行 (Thought-Action-Observation)',
            '多步驟任務規劃',
            '實時進度追蹤',
            '結果保存和下載',
            '任務歷史管理',
            '錯誤處理和恢復'
        ],
        'model_info': {
            'name': 'GPT-OSS-20B',
            'provider': 'OpenRouter',
            'cost': 'Free',
            'description': '免費的開源GPT模型'
        }
    }
    
    return jsonify(capabilities), 200

@agent_bp.route('/status', methods=['GET'])
def get_agent_status():
    """獲取Agent系統狀態"""
    try:
        # 檢查數據庫連接
        db_status = "healthy"
        try:
            db.session.execute('SELECT 1')
        except:
            db_status = "error"
        
        # 檢查API密鑰
        api_key_status = "configured" if os.getenv('OPENROUTER_API_KEY') else "missing"
        
        status = {
            'agent_version': '1.0.0',
            'database': db_status,
            'api_key': api_key_status,
            'supported_models': ['openai/gpt-oss-20b:free'],
            'max_iterations': 10,
            'status': 'operational' if db_status == "healthy" else 'degraded'
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

