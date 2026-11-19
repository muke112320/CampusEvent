# CampusEvent · 校园活动报名与管理系统

《软件工程》实验二项目。面向校园活动场景，实现“管理员发布活动、学生报名、管理员审核、结果通知”的完整闭环，并用**策略模式**封装两类报名规则、用**观察者模式**解耦报名业务与通知渠道。

当前代码对应版本：`baseline-v1`（初始验收版本）。

## 1. 功能范围

| 编号 | 功能 | 实现说明 |
| --- | --- | --- |
| P2-F01 | 活动管理 | 管理员创建、编辑、删除活动；设置名称、类型、时间、地点、人数上限、报名方式 |
| P2-F02 | 活动查看 | 学生浏览活动列表与详情，支持按名称搜索 |
| P2-F03 | 报名 / 取消 | 学生报名、取消；同一活动禁止重复有效报名；活动开始后不能新增报名 |
| P2-F04 | 报名策略 | 直接报名即时通过；审核型报名进入待审核 |
| P2-F05 | 审批操作 | 管理员批准/拒绝待审核申请，批准时再次检查剩余名额 |
| P2-F06 | 状态管理 | 待审核 / 已通过 / 已拒绝 / 已取消，状态转换符合业务规则 |
| P2-F07 | 站内通知 | 报名与审核结果写入站内消息；同时投递模拟邮件 |
| P2-F08 | 统计 | 按活动展示已通过数、待审核数、剩余名额 |

明确不做：用户注册、密码体系、多角色权限管理、真实邮件/短信通道、消息队列、移动端 App。

## 2. 技术栈

- Python 3.11+（开发环境 3.12）
- Flask 3.1 + Jinja2 服务端渲染
- SQLite（标准库 `sqlite3`，无 ORM）
- pytest 9（29 条自动化测试）
- 原生 CSS，无前端框架依赖

## 3. 目录结构

```
CampusEvent/
├── app/
│   ├── domain/          # 领域模型、领域事件、报名策略、异常
│   ├── services/        # 活动、报名、审批、通知、事件总线
│   ├── web/             # Flask 蓝图（认证/活动/报名/审批/消息）
│   ├── templates/       # Jinja2 页面
│   ├── static/style.css
│   ├── migrations.py    # 建表与版本迁移
│   ├── repositories.py  # SQLite 仓储
│   ├── container.py     # 依赖装配
│   └── seed.py          # 演示数据
├── tests/               # 验收测试、规则测试、通知测试
├── tools/               # 演示数据与截图辅助脚本（开发用）
├── docs/                # 设计文档、UML 图、报告
├── run.py               # 开发启动入口
├── wsgi.py              # gunicorn 入口
└── requirements*.txt
```

## 4. 快速开始（从零运行）

Windows PowerShell：

```powershell
cd 软件工程实验二CampusEvent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Linux / macOS：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
```

浏览器打开 <http://127.0.0.1:5000>，使用登录页上的固定演示账号进入：

| 账号 | 姓名 | 角色 | 用途 |
| --- | --- | --- | --- |
| `admin` | 系统管理员 | 管理员 | 创建/编辑活动、审批报名、查看通知台账 |
| `s1` | 张小明 | 学生 | 报名、取消、查看站内消息 |
| `s2` / `s3` / `s4` | 李小红 / 王大力 / 赵晓雨 | 学生 | 多人报名与满员场景演示 |

首次启动自动建表并写入 4 个演示活动，无需手工初始化。

## 5. 运行测试

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

测试覆盖：

- `tests/test_acceptance.py`：指导书 3.5 节 C1—C10 全部验收用例（HTTP 操作 + 数据库核对）
- `tests/test_rules.py`：策略选择、满员、重复报名、取消/拒绝后重报、活动开始、容量回退、删除保护、权限
- `tests/test_notifications.py`：站内 + 邮件双渠道、失败留痕、同一事件幂等、事务边界
- `tests/test_prefix.py`：`/campusevent/` 子路径部署下的登录、静态资源与会话 cookie 隔离
- 共 29 条，全部通过（最终版本实测 `29 passed`）

## 6. 设计要点

1. **策略模式**：`RegistrationPolicy` 模板方法先执行公共规则（活动时间、重复有效报名），再委托 `decide()` 处理变化点（满员时拒绝还是进入待审核）。新增报名方式只需新增策略类并在注册表登记。
2. **观察者模式**：报名服务提交事务后发布领域事件，`EventBus` 分发给站内消息与邮件两个独立订阅者；订阅者异常被隔离，不影响业务事务。
3. **名额口径**：只有“已通过”占用名额；“待审核”不占名额，批准时在事务内再次检查容量。
4. **幂等与留痕**：`notification_deliveries` 以 `(event_id, subscriber, student_id)` 唯一约束防止重复通知，同时记录失败原因。
5. **事务边界**：报名先提交、后通知；通知失败不回滚报名。删除有报名的活动直接拒绝，保留历史数据。

详细设计见 `docs/`。

## 7. 数据与重置

- 数据库默认位于 `instance/campusevent.sqlite3`，已加入 `.gitignore`。
- 需重置演示数据时：停止服务，删除 `instance/` 目录，重新启动。
- 追加一组演示报名数据：`.\.venv\Scripts\python.exe tools\demo_data.py`。

## 8. 部署到服务器

系统已部署到腾讯云轻量应用服务器（Ubuntu 24.04.2 LTS），访问地址：

**<http://120.76.59.189/campusevent/>**

部署结构：

```
浏览器 → Nginx :80  /campusevent/ → gunicorn 127.0.0.1:8001 → Flask → SQLite
                     /（根路径）→ 实验一 StudyTask（127.0.0.1:8000）
```

- 应用目录：`/opt/campusevent`，数据库：`/opt/campusevent/instance/campusevent.sqlite3`
- 进程托管：`systemd` 服务 `campusevent`，gunicorn 2 worker
- Nginx 复用现有 80 端口，以 `/campusevent/` 子路径反向代理，不影响根路径的 StudyTask
- 子路径通过 `CAMPUSEVENT_URL_PREFIX=/campusevent` 挂载，`url_for` 自动生成带前缀的静态资源、表单与跳转
- 会话 cookie 使用独立名称 `campusevent_session`，避免与同主机其他 Flask 应用互相覆盖
- 已实测：公网登录、活动列表、报名、重启服务后报名数据仍存在；StudyTask 根路径仍正常

常用运维命令：

```bash
sudo systemctl status campusevent
sudo systemctl restart campusevent
sudo journalctl -u campusevent -n 50 --no-pager
curl -I http://120.76.59.189/campusevent/login
```

更新代码：重新上传源码到 `/opt/campusevent`（保留 `instance/` 数据库），`sudo systemctl restart campusevent` 即可。部署辅助文件见 `deploy/`（`campusevent.service`、`nginx-campusevent.conf`、`add_campusevent_nginx.py`）。

> 注：早期文档中的“8000 端口 + 独立站点”配置适用于独立主机；本机与 StudyTask 共用 80 端口，因此实际使用 8001 + `/campusevent/` 子路径。

## 9. 已知限制

- 固定演示账号、无密码，仅用于课程演示，不具备真实身份认证能力。
- 邮件渠道为出件箱模拟（写入 `email_outbox` 表），不连接真实 SMTP。
- SQLite 单文件数据库，适合单机演示；高并发场景需替换为 MySQL/PostgreSQL。
- 未实现 CSRF Token（教学项目范围外）。

## 10. 交付物清单

| 交付物 | 路径 |
| --- | --- |
| 可运行源代码、模板、测试 | `app/`、`tests/`、`run.py` |
| 实验报告（8 页） | `docs/实验报告.docx` |
| 答辩 PPT（13 页） | `docs/演示PPT.pptx` |
| 回归测试表（C1—C10 + 16 条补充） | `docs/08_回归测试表.xlsx` |
| 初始 SRS 分析、用例说明、UML、时序、设计模式决策、评审表 | `docs/01`—`docs/06` |
| AI 协作记录 | `AI_DEV_LOG.md` |
| 文档索引 | `docs/README.md` |

> 说明：当前只交付 `baseline-v1`。教师尚未发布需求变更单，因此没有提前实现任何变更功能；变更版将在收到正式变更单后，按影响分析—分支实现—回归测试的流程补充。
