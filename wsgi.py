"""生产环境 WSGI 入口（gunicorn 使用）。

支持通过 CAMPUSEVENT_URL_PREFIX 挂载到子路径，例如：
    CAMPUSEVENT_URL_PREFIX=/campusevent gunicorn -b 127.0.0.1:8001 wsgi:app

挂载后 Flask 的 SCRIPT_NAME 为 /campusevent，url_for 会自动生成带前缀的
静态资源、表单和跳转地址，因此可以与其他应用共用 80 端口而不冲突。
"""

from __future__ import annotations

import os

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

from app import create_app

flask_app = create_app()
_prefix = (os.environ.get("CAMPUSEVENT_URL_PREFIX") or "").rstrip("/")
if _prefix:
    flask_app.wsgi_app = DispatcherMiddleware(
        Response("Not Found", status=404, mimetype="text/plain"),
        {_prefix: flask_app.wsgi_app},
    )

app = flask_app
