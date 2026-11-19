from pathlib import Path

path = Path("/etc/nginx/sites-available/studytask")
text = path.read_text()
if "location /campusevent/" in text:
    print("campusevent location already configured")
    raise SystemExit(0)

block = """
    # CampusEvent：独立子路径，反向代理到 8001，不影响根路径的 StudyTask
    location = /campusevent {
        return 301 /campusevent/;
    }

    location /campusevent/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
"""

index = text.rfind("}")
if index == -1:
    raise SystemExit("unexpected nginx config: no closing brace")

backup = path.with_name("studytask.bak-campusevent")
backup.write_text(text)
path.write_text(text[:index] + block + text[index:])
print("updated", path, "backup", backup)
