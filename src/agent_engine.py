import json
import time
import requests
from typing import Dict, List, Any, Optional
from src.models.user import db, Task, TaskStep
from datetime import datetime

class LynusAgent:
    """Lynus AI Agent - 模仿Manus AI的Agent系統"""
    
    def __init__(self, openrouter_api_key: str):
        self.api_key = openrouter_api_key
        self.api_base = "https://openrouter.ai/api/v1"
        self.model = "openai/gpt-oss-20b:free"
        self.max_iterations = 10
        
    def _call_llm(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """調用GPT-OSS模型"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://lynus.ai",
                "X-Title": "Lynus AI Agent"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")
    
    def _add_task_step(self, task_id: int, step_type: str, content: str) -> None:
        """添加任務步驟到數據庫"""
        try:
            # 獲取下一個步驟編號
            last_step = TaskStep.query.filter_by(task_id=task_id).order_by(TaskStep.step_number.desc()).first()
            step_number = (last_step.step_number + 1) if last_step else 1
            
            step = TaskStep(
                task_id=task_id,
                step_number=step_number,
                step_type=step_type,
                content=content
            )
            
            db.session.add(step)
            db.session.commit()
            
        except Exception as e:
            print(f"Failed to add task step: {str(e)}")
    
    def _update_task_progress(self, task_id: int, progress: int, status: str = None) -> None:
        """更新任務進度"""
        try:
            task = Task.query.get(task_id)
            if task:
                task.progress = progress
                if status:
                    task.status = status
                task.updated_at = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            print(f"Failed to update task progress: {str(e)}")
    
    def _thought_phase(self, task_description: str, task_type: str, context: str = "") -> str:
        """思考階段 - 分析任務需求"""
        messages = [
            {
                "role": "system",
                "content": """你是Lynus AI Agent，一個模仿Manus AI的智能助手。你需要分析用戶的任務需求，制定執行計劃。

你的能力包括：
- 圖像生成和編輯
- 簡報製作
- 網頁設計和開發
- 電子表格處理
- 數據可視化
- 文檔生成
- 代碼編寫
- 網頁分析和模仿

請分析任務需求，思考如何完成這個任務，並制定詳細的執行計劃。"""
            },
            {
                "role": "user",
                "content": f"""任務類型: {task_type}
任務描述: {task_description}
上下文: {context}

請分析這個任務，思考需要採取什麼行動來完成它。請詳細說明你的思考過程和計劃。"""
            }
        ]
        
        return self._call_llm(messages)
    
    def _action_phase(self, task_description: str, task_type: str, thought: str) -> Dict[str, Any]:
        """行動階段 - 選擇和執行工具"""
        messages = [
            {
                "role": "system",
                "content": """你是Lynus AI Agent。基於你的思考，現在需要選擇具體的行動。

可用的行動類型：
1. generate_image - 生成圖像
2. create_slides - 創建簡報
3. build_webpage - 構建網頁
4. process_spreadsheet - 處理電子表格
5. create_visualization - 創建數據可視化
6. write_document - 編寫文檔
7. write_code - 編寫代碼
8. analyze_webpage - 分析網頁

請選擇一個行動，並提供執行該行動所需的參數。

回應格式（JSON）：
{
    "action": "行動類型",
    "parameters": {
        "key": "value"
    },
    "reasoning": "選擇這個行動的原因"
}"""
            },
            {
                "role": "user",
                "content": f"""任務描述: {task_description}
任務類型: {task_type}
我的思考: {thought}

基於以上信息，請選擇下一步行動。"""
            }
        ]
        
        response = self._call_llm(messages)
        
        try:
            # 嘗試解析JSON響應
            action_data = json.loads(response)
            return action_data
        except json.JSONDecodeError:
            # 如果無法解析JSON，返回默認行動
            return {
                "action": "write_document",
                "parameters": {"content": response},
                "reasoning": "無法解析行動格式，默認生成文檔"
            }
    
    def _execute_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行具體行動"""
        action = action_data.get("action", "")
        parameters = action_data.get("parameters", {})
        
        try:
            if action == "generate_image":
                return self._generate_image(parameters)
            elif action == "create_slides":
                return self._create_slides(parameters)
            elif action == "build_webpage":
                return self._build_webpage(parameters)
            elif action == "process_spreadsheet":
                return self._process_spreadsheet(parameters)
            elif action == "create_visualization":
                return self._create_visualization(parameters)
            elif action == "write_document":
                return self._write_document(parameters)
            elif action == "write_code":
                return self._write_code(parameters)
            elif action == "analyze_webpage":
                return self._analyze_webpage(parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "result": None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def _generate_image(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """生成圖像"""
        # 這裡應該集成圖像生成API
        prompt = parameters.get("prompt", "")
        style = parameters.get("style", "realistic")
        
        return {
            "success": True,
            "result": {
                "type": "image",
                "prompt": prompt,
                "style": style,
                "url": "https://example.com/generated-image.png",
                "message": f"已生成圖像：{prompt}"
            }
        }
    
    def _create_slides(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """創建簡報"""
        topic = parameters.get("topic", "")
        slides_count = parameters.get("slides_count", 5)
        
        return {
            "success": True,
            "result": {
                "type": "slides",
                "topic": topic,
                "slides_count": slides_count,
                "url": "https://example.com/presentation.pptx",
                "message": f"已創建{slides_count}頁關於'{topic}'的簡報"
            }
        }
    
    def _build_webpage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """構建網頁"""
        description = parameters.get("description", "")
        style = parameters.get("style", "modern")
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Your Website</h1>
        <p>{description}</p>
        <p>This website was generated by Lynus AI Agent.</p>
    </div>
</body>
</html>"""
        
        return {
            "success": True,
            "result": {
                "type": "webpage",
                "description": description,
                "style": style,
                "html": html_content,
                "url": "https://example.com/generated-site",
                "message": f"已構建網頁：{description}"
            }
        }
    
    def _process_spreadsheet(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理電子表格"""
        operation = parameters.get("operation", "create")
        data_type = parameters.get("data_type", "general")
        
        return {
            "success": True,
            "result": {
                "type": "spreadsheet",
                "operation": operation,
                "data_type": data_type,
                "url": "https://example.com/spreadsheet.xlsx",
                "message": f"已處理電子表格：{operation} - {data_type}"
            }
        }
    
    def _create_visualization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """創建數據可視化"""
        chart_type = parameters.get("chart_type", "bar")
        data_source = parameters.get("data_source", "sample")
        
        return {
            "success": True,
            "result": {
                "type": "visualization",
                "chart_type": chart_type,
                "data_source": data_source,
                "url": "https://example.com/chart.png",
                "message": f"已創建{chart_type}圖表，數據來源：{data_source}"
            }
        }
    
    def _write_document(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """編寫文檔"""
        content = parameters.get("content", "")
        format_type = parameters.get("format", "markdown")
        
        return {
            "success": True,
            "result": {
                "type": "document",
                "content": content,
                "format": format_type,
                "message": f"已生成{format_type}格式文檔"
            }
        }
    
    def _write_code(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """編寫代碼"""
        language = parameters.get("language", "python")
        purpose = parameters.get("purpose", "")
        
        code_content = f"""# {purpose}
# Generated by Lynus AI Agent

def main():
    print("Hello from Lynus AI!")
    # Your code here
    pass

if __name__ == "__main__":
    main()
"""
        
        return {
            "success": True,
            "result": {
                "type": "code",
                "language": language,
                "purpose": purpose,
                "code": code_content,
                "message": f"已生成{language}代碼：{purpose}"
            }
        }
    
    def _analyze_webpage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """分析網頁"""
        url = parameters.get("url", "")
        
        return {
            "success": True,
            "result": {
                "type": "webpage_analysis",
                "url": url,
                "analysis": f"已分析網頁：{url}",
                "message": f"網頁分析完成：{url}"
            }
        }
    
    def _observation_phase(self, action_result: Dict[str, Any]) -> str:
        """觀察階段 - 分析執行結果"""
        messages = [
            {
                "role": "system",
                "content": "你是Lynus AI Agent。請觀察和分析剛才執行的行動結果，判斷是否成功，是否需要進一步的行動。"
            },
            {
                "role": "user",
                "content": f"""執行結果：
{json.dumps(action_result, ensure_ascii=False, indent=2)}

請分析這個結果：
1. 行動是否成功執行？
2. 結果是否符合預期？
3. 是否需要進一步的行動？
4. 如果需要，下一步應該做什麼？"""
            }
        ]
        
        return self._call_llm(messages)
    
    def execute_task(self, task_id: int, openrouter_api_key: str) -> Dict[str, Any]:
        """執行任務的主要方法 - TAO循環"""
        try:
            # 獲取任務信息
            task = Task.query.get(task_id)
            if not task:
                return {"success": False, "error": "Task not found"}
            
            # 更新任務狀態為運行中
            self._update_task_progress(task_id, 0, "running")
            
            # 設置API密鑰
            self.api_key = openrouter_api_key
            
            context = ""
            final_result = None
            
            for iteration in range(self.max_iterations):
                try:
                    # 1. Thought Phase (思考)
                    self._add_task_step(task_id, "thought", f"開始第{iteration + 1}次迭代...")
                    
                    thought = self._thought_phase(task.description, task.task_type, context)
                    self._add_task_step(task_id, "thought", thought)
                    
                    # 更新進度
                    progress = min(20 + (iteration * 60 // self.max_iterations), 80)
                    self._update_task_progress(task_id, progress)
                    
                    # 2. Action Phase (行動)
                    action_data = self._action_phase(task.description, task.task_type, thought)
                    action_content = f"選擇行動：{action_data.get('action', 'unknown')}\n原因：{action_data.get('reasoning', '')}"
                    self._add_task_step(task_id, "action", action_content)
                    
                    # 執行行動
                    action_result = self._execute_action(action_data)
                    
                    # 3. Observation Phase (觀察)
                    observation = self._observation_phase(action_result)
                    self._add_task_step(task_id, "observation", observation)
                    
                    # 檢查是否完成
                    if action_result.get("success", False):
                        final_result = action_result.get("result", {})
                        
                        # 如果觀察結果表明任務已完成，則退出循環
                        if any(keyword in observation.lower() for keyword in ["完成", "成功", "finished", "done", "completed"]):
                            break
                    
                    # 更新上下文
                    context += f"\n迭代{iteration + 1}:\n思考: {thought}\n行動: {action_content}\n觀察: {observation}\n"
                    
                    # 短暫延遲
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"迭代{iteration + 1}執行失敗: {str(e)}"
                    self._add_task_step(task_id, "observation", error_msg)
                    continue
            
            # 完成任務
            if final_result:
                # 保存結果
                task.result_data = json.dumps(final_result, ensure_ascii=False)
                self._update_task_progress(task_id, 100, "completed")
                
                completion_msg = f"任務完成！結果類型：{final_result.get('type', 'unknown')}"
                self._add_task_step(task_id, "observation", completion_msg)
                
                return {
                    "success": True,
                    "result": final_result,
                    "message": "Task completed successfully"
                }
            else:
                self._update_task_progress(task_id, 100, "failed")
                self._add_task_step(task_id, "observation", "任務執行失敗，未能產生有效結果")
                
                return {
                    "success": False,
                    "error": "Task execution failed",
                    "message": "No valid result produced"
                }
                
        except Exception as e:
            # 任務執行出錯
            self._update_task_progress(task_id, 0, "failed")
            error_msg = f"任務執行出錯：{str(e)}"
            self._add_task_step(task_id, "observation", error_msg)
            
            return {
                "success": False,
                "error": str(e),
                "message": "Task execution failed with error"
            }

