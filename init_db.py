#!/usr/bin/env python3
"""
數據庫初始化腳本
創建所有必要的數據庫表
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.user import db

def init_database():
    """初始化數據庫"""
    with app.app_context():
        try:
            # 刪除所有現有表（如果存在）
            print("正在刪除現有表...")
            db.drop_all()
            
            # 創建所有表
            print("正在創建數據庫表...")
            db.create_all()
            
            print("✅ 數據庫初始化成功！")
            print("創建的表：")
            print("- user: 用戶表")
            print("- task: 任務表")
            print("- task_step: 任務步驟表")
            
        except Exception as e:
            print(f"❌ 數據庫初始化失敗: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("開始初始化Lynus數據庫...")
    success = init_database()
    
    if success:
        print("\n🎉 數據庫初始化完成！現在可以啟動應用了。")
    else:
        print("\n💥 數據庫初始化失敗，請檢查錯誤信息。")
        sys.exit(1)

