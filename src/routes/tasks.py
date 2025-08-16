from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Task, TaskStep
import json
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

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

@tasks_bp.route('/create', methods=['POST'])
@require_auth
def create_task(user):
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
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create task: {str(e)}'}), 500

@tasks_bp.route('/list', methods=['GET'])
@require_auth
def list_tasks(user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        task_type = request.args.get('task_type')
        
        # 構建查詢
        query = Task.query.filter_by(user_id=user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        if task_type:
            query = query.filter_by(task_type=task_type)
        
        # 按創建時間倒序排列
        query = query.order_by(Task.created_at.desc())
        
        # 分頁
        tasks = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': tasks.total,
                'pages': tasks.pages,
                'has_next': tasks.has_next,
                'has_prev': tasks.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list tasks: {str(e)}'}), 500

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@require_auth
def get_task(user, task_id):
    try:
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({'task': task.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get task: {str(e)}'}), 500

@tasks_bp.route('/<int:task_id>/steps', methods=['POST'])
@require_auth
def add_task_step(user, task_id):
    try:
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        step_type = data.get('step_type', '').strip()
        content = data.get('content', '').strip()
        
        if not step_type or not content:
            return jsonify({'error': 'Step type and content are required'}), 400
        
        # 驗證步驟類型
        valid_types = ['thought', 'action', 'observation']
        if step_type not in valid_types:
            return jsonify({'error': 'Invalid step type'}), 400
        
        # 獲取下一個步驟編號
        last_step = TaskStep.query.filter_by(task_id=task_id).order_by(TaskStep.step_number.desc()).first()
        step_number = (last_step.step_number + 1) if last_step else 1
        
        # 創建新步驟
        step = TaskStep(
            task_id=task_id,
            step_number=step_number,
            step_type=step_type,
            content=content
        )
        
        db.session.add(step)
        
        # 更新任務的更新時間
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Step added successfully',
            'step': step.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add step: {str(e)}'}), 500

@tasks_bp.route('/<int:task_id>/status', methods=['PUT'])
@require_auth
def update_task_status(user, task_id):
    try:
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        status = data.get('status', '').strip()
        progress = data.get('progress')
        result_data = data.get('result_data')
        
        # 驗證狀態
        valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        if status and status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        # 更新任務
        if status:
            task.status = status
        
        if progress is not None:
            if not isinstance(progress, int) or progress < 0 or progress > 100:
                return jsonify({'error': 'Progress must be an integer between 0 and 100'}), 400
            task.progress = progress
        
        if result_data is not None:
            if isinstance(result_data, dict):
                task.result_data = json.dumps(result_data)
            else:
                task.result_data = str(result_data)
        
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update task: {str(e)}'}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(user, task_id):
    try:
        task = Task.query.filter_by(id=task_id, user_id=user.id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Task deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete task: {str(e)}'}), 500

@tasks_bp.route('/stats', methods=['GET'])
@require_auth
def get_task_stats(user):
    try:
        # 統計各種狀態的任務數量
        stats = {}
        
        total_tasks = Task.query.filter_by(user_id=user.id).count()
        stats['total'] = total_tasks
        
        for status in ['pending', 'running', 'completed', 'failed', 'cancelled']:
            count = Task.query.filter_by(user_id=user.id, status=status).count()
            stats[status] = count
        
        # 統計各種類型的任務數量
        type_stats = {}
        for task_type in ['image', 'slides', 'webpage', 'spreadsheet', 'visualization', 'general']:
            count = Task.query.filter_by(user_id=user.id, task_type=task_type).count()
            type_stats[task_type] = count
        
        stats['by_type'] = type_stats
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

