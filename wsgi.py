"""生产环境 WSGI 入口（gunicorn 使用）：gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app"""

from app import create_app

app = create_app()
