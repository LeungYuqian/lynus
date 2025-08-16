# Lynus AI Agent 後端部署指南

本指南將幫助您將Lynus AI Agent的後端部署到生產環境。

## 1. 環境準備

確保您的服務器或部署環境已安裝以下組件：
- Python 3.8+
- pip (Python 包管理器)
- Git (用於克隆代碼)
- 數據庫 (推薦PostgreSQL或MySQL，本項目默認使用SQLite)

## 2. 克隆項目

```bash
git clone <您的項目Git倉庫地址>
cd lynus-backend
```

## 3. 創建虛擬環境並安裝依賴

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. 配置環境變量

創建一個 `.env` 文件在 `lynus-backend` 目錄下，並設置以下變量：

```
SECRET_KEY=您的Flask應用密鑰 (請生成一個強密鑰)
DATABASE_URL=您的數據庫連接字符串 (例如：sqlite:///site.db 或 postgresql://user:password@host:port/database)
OPENROUTER_API_KEY=您的OpenRouter API密鑰 (用於GPT-OSS模型)
```

**注意：** 對於生產環境，強烈建議使用PostgreSQL或MySQL等關係型數據庫，而不是SQLite。

## 5. 初始化數據庫

```bash
python init_db.py
```

這將創建所有必要的數據庫表。如果您從SQLite遷移到其他數據庫，請確保更新 `DATABASE_URL` 並重新運行此命令。

## 6. 運行後端服務

推薦使用Gunicorn或uWSGI等WSGI服務器來運行Flask應用。

### 使用Gunicorn (推薦)

首先安裝Gunicorn：

```bash
pip install gunicorn
```

然後運行應用：

```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

- `-w 4`: 運行4個工作進程
- `-b 0.0.0.0:5000`: 綁定到所有網絡接口的5000端口

### 使用Supervisor (用於進程管理)

為了確保應用在後台持續運行並在崩潰時自動重啟，您可以使用Supervisor。

創建一個Supervisor配置文件 (例如：`/etc/supervisor/conf.d/lynus.conf`)：

```ini
[program:lynus]
command=/path/to/your/lynus-backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
directory=/path/to/your/lynus-backend
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/lynus/lynus.err.log
stdout_logfile=/var/log/lynus/lynus.out.log
```

替換 `/path/to/your/lynus-backend` 為您的實際項目路徑。

然後更新Supervisor配置並啟動服務：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start lynus
```

## 7. 配置Nginx (反向代理)

為了提供更好的性能、安全性並處理SSL，建議使用Nginx作為反向代理。

創建一個Nginx配置文件 (例如：`/etc/nginx/sites-available/lynus`)：

```nginx
server {
    listen 80;
    server_name your_domain.com www.your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

替換 `your_domain.com` 為您的實際域名。然後啟用配置並重啟Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/lynus /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 8. 配置SSL (HTTPS)

推薦使用Certbot來獲取和配置Let's Encrypt的免費SSL證書。

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com -d www.your_domain.com
```

按照提示完成配置。Certbot會自動修改Nginx配置以啟用HTTPS並設置證書自動續期。

## 9. 監控和日誌

定期檢查應用日誌 (`/var/log/lynus/`) 和Nginx日誌 (`/var/log/nginx/`) 以監控應用程序的運行狀況。

## 10. 更新應用

當您更新代碼時，只需拉取最新代碼並重啟Gunicorn進程即可：

```bash
cd /path/to/your/lynus-backend
git pull
source venv/bin/activate
pip install -r requirements.txt # 如果有新的依賴
sudo supervisorctl restart lynus # 如果使用Supervisor
# 或者直接重啟Gunicorn進程
```

這將確保您的Lynus AI Agent後端在生產環境中穩定運行。

