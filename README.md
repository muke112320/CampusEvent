# CampusEvent · 校园活动报名与管理系统

《软件工程》实验二项目。面向校园活动场景，实现“管理员发布活动、学生报名、管理员审核、结果通知”的完整闭环，并用**策略模式**封装报名规则、用**观察者模式**解耦报名业务与通知渠道；初版验收后再按教师变更单完成一次**需求变更**（年级限定报名 + 模拟邮件通知），用真实差异检验设计的可扩展性。

| 版本 | Git 标签 | 内容 | 测试 |
| --- | --- | --- | --- |
| 初版 | `baseline-v1` | 直接报名 / 审核报名两类策略，站内消息 + 出件箱邮件双渠道通知 | 29 passed |
| 变更版 | `change-v2` | CR-01 年级限定报名；CR-02 MockEmailSender 邮件台账 | 41 passed |

仓库地址：<https://github.com/muke112320/CampusEvent>
在线访问：<http://120.76.59.189/campusevent/>

## 1. 功能范围

### 1.1 初版（baseline-v1）

| 编号 | 功能 | 实现说明 |
| --- | --- | --- |
| P2-F01 | 活动管理 | 管理员创建、编辑、删除活动；设置名称、类型、时间、地点、人数上限、报名方式 |
| P2-F02 | 活动查看 | 学生浏览活动列表与详情，支持按名称搜索 |
| P2-F03 | 报名 / 取消 | 学生报名、取消；同一活动禁止重复有效报名；活动开始后不能新增报名 |
| P2-F04 | 报名策略 | 直接报名即时通过；审核型报名进入待审核 |
| P2-F05 | 审批操作 | 管理员批准/拒绝待审核申请，批准时再次检查剩余名额 |
| P2-F06 | 状态管理 | 待审核 / 已通过 / 已拒绝 / 已取消，状态转换符合业务规则 |
| P2-F07 | 结果通知 | 报名与审核结果写入站内消息；同时投递出件箱邮件 |
| P2-F08 | 统计 | 按活动展示已通过数、待审核数、剩余名额 |

### 1.2 变更（change-v2，教师变更单）

| 变更单 | 能力 |
| --- | --- |
| CR-01 年级限定报名 | Student 增加年级（1—4）；新增第三种报名方式“年级限定报名”，仅大二、大三可报名，其他年级收到明确提示；仍遵守名额、开始时间与重复报名约束 |
| CR-02 模拟邮件通知 | 报名通过、审核通过或拒绝时，站内通知继续运行，同时由 MockEmailSender 模拟发送邮件并记录收件人、主题、内容、状态、时间；失败只留痕、不回滚报名；同一业务事件不重复发送 |

变更影响分析、迁移说明与实测数据见 [`docs/07_变更需求单与影响分析.md`](docs/07_变更需求单与影响分析.md)、[`docs/09_可维护性对照.md`](docs/09_可维护性对照.md)、[`docs/08_回归测试表.xlsx`](docs/08_回归测试表.xlsx)。

明确不做：用户注册、密码体系、多角色权限管理、真实邮件/短信通道、消息队列、移动端 App。

## 2. 技术栈

- Python 3.11+（开发环境 3.12）
- Flask 3.1 + Jinja2 服务端渲染
- SQLite（标准库 `sqlite3`，无 ORM）
- pytest 9（41 条自动化测试）
- 原生 CSS，无前端框架依赖

## 3. 目录结构

```
CampusEvent/
├── app/
│   ├── domain/          # 领域模型、领域事件、报名策略（3 个）、异常
│   ├── services/        # 活动、报名、审批、MockEmailSender、通知、事件总线
│   ├── web/             # Flask 蓝图（认证/活动/报名/审批/消息）
│   ├── templates/       # Jinja2 页面
│   ├── static/style.css
│   ├── migrations.py    # 建表与 v1→v2 迁移（年级、报名方式、邮件台账）
│   ├── repositories.py  # SQLite 仓储（含邮件台账）
│   ├── container.py     # 依赖装配
│   └── seed.py          # 演示数据（含年级与年级限定活动）
├── tests/               # 验收、规则、通知、变更、子路径测试（41 条）
├── tools/               # 演示数据与截图辅助脚本（开发用）
├── deploy/              # systemd / Nginx / 部署与冒烟脚本
├── docs/                # 设计文档、两版 UML、回归表、项目总结
├── run.py               # 开发启动入口
├── wsgi.py              # gunicorn 入口（支持 /campusevent 子路径）
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

| 账号 | 姓名 | 年级 | 角色 | 用途 |
| --- | --- | --- | --- | --- |
| `s1` | 张小明 | 大二 | 学生 | 可报名年级限定活动；报名、取消、查看消息 |
| `s2` | 李小红 | 大三 | 学生 | 可报名年级限定活动；满员/审核场景 |
| `s3` | 王大力 | 大一 | 学生 | 年级限定活动会被明确拒绝 |
| `s4` | 赵晓雨 | 大四 | 学生 | 年级限定活动会被明确拒绝 |
| `admin` | 系统管理员 | 大四 | 管理员 | 创建/编辑活动、审批报名、查看通知与邮件台账 |

首次启动自动建表、执行 v1→v2 迁移并写入演示活动（含“职业规划工作坊（大二/大三限定）”），无需手工初始化。

## 5. 切换两版代码

```bash
git checkout baseline-v1   # 初版：两类报名策略
git checkout change-v2     # 变更版：年级限定 + MockEmailSender
git diff --stat baseline-v1..change-v2
```

## 6. 运行测试

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

测试覆盖（共 41 条，全部通过）：

- `tests/test_acceptance.py`：指导书 3.5 节 C1—C10 全部验收用例（HTTP 操作 + 数据库核对）
- `tests/test_rules.py`：策略选择、满员、重复报名、取消/拒绝后重报、活动开始、容量回退、删除保护、权限
- `tests/test_notifications.py`：站内 + 邮件双渠道、失败留痕、同一事件幂等、事务边界
- `tests/test_change_v2.py`：年级准入（CR1-01—04）、容量/重复/原策略回归、邮件双渠道与失败（CR2-01—03）、事件幂等（CR2-04）、v1→v2 迁移（CR2-05）
- `tests/test_prefix.py`：`/campusevent/` 子路径部署下的登录、静态资源与会话 cookie 隔离

## 7. 设计要点

1. **策略模式**：`RegistrationPolicy` 模板方法先执行公共规则（活动时间、重复有效报名），再委托 `decide()` 处理变化点。`GradeLimitedRegistrationPolicy` 继承 `DirectRegistrationPolicy`，只增加年级校验并复用容量判定；新增报名方式只需新增策略类并在注册表登记。
2. **观察者模式**：报名服务提交事务后发布领域事件，`EventBus` 分发给站内消息与邮件两个独立订阅者；订阅者异常被隔离，不影响业务事务。
3. **名额口径**：只有“已通过”占用名额；“待审核”不占名额，审批时在事务内再次检查容量。
4. **邮件台账**：`MockEmailSender` 记录每封邮件的收件人、主题、内容、状态、错误与时间；`email_deliveries` 以 `(event_id, student_id)` 唯一，配合订阅者 claim 双重防重。
5. **事务边界**：报名先提交、后通知；邮件失败只留痕，不回滚报名。删除有报名的活动直接拒绝，保留历史数据。
6. **迁移不删库**：v1→v2 增加学生年级列、重建活动表以扩展 `policy_type` CHECK、新增邮件台账，旧活动与报名完整保留。

详细设计见 [`docs/`](docs/)。

## 8. 数据与重置

- 数据库默认位于 `instance/campusevent.sqlite3`，已加入 `.gitignore`。
- 需重置演示数据时：停止服务，删除 `instance/` 目录，重新启动。
- 追加一组演示报名数据：`.\.venv\Scripts\python.exe tools\demo_data.py`。

## 9. 部署到服务器

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

**2026-11-26 部署记录**：恢复升级前的 baseline 数据库（v1），上传 change-v2 源码并重启 systemd 服务，应用启动时自动执行 v1→v2 迁移。迁移后 `schema_version=2`，学生年级回填为 s1 大二、s2 大三、s3 大一、s4 大四、admin 大四；原有 4 个活动、5 条报名完整保留；公网登录页显示“三类报名方式”，管理员新建活动表单含“年级限定报名”，通知台账显示“模拟邮件发送记录”，StudyTask 根路径仍返回 200。

常用运维命令：

```bash
sudo systemctl status campusevent
sudo systemctl restart campusevent
sudo journalctl -u campusevent -n 50 --no-pager
curl -I http://120.76.59.189/campusevent/login
```

更新代码：重新上传源码到 `/opt/campusevent`（保留 `instance/` 数据库），`sudo systemctl restart campusevent` 即可。部署辅助文件见 `deploy/`。

## 10. 已知限制

- 固定演示账号、无密码，仅用于课程演示，不具备真实身份认证能力。
- 邮件为 MockEmailSender 模拟发送（写入 `email_outbox` 与 `email_deliveries`），不连接真实 SMTP。
- 通知为进程内同步投递，无失败重试队列；失败只留痕（可在通知台账查看）。
- SQLite 单文件数据库，适合单机演示；高并发场景需替换为 MySQL/PostgreSQL。
- 未实现 CSRF Token（教学项目范围外）。

## 11. 交付物清单

| 交付物 | 路径 |
| --- | --- |
| 初始 SRS 分析（含变更范围） | [`docs/01_初始SRS分析.md`](docs/01_初始SRS分析.md) |
| 用例说明（含变更用例） | [`docs/02_用例说明.md`](docs/02_用例说明.md) |
| 初版与变更版 UML 类图（4 张） | [`docs/03_UML类图.md`](docs/03_UML类图.md) |
| 关键时序图（5 张） | [`docs/04_时序图.md`](docs/04_时序图.md) |
| 设计模式决策报告（含变更验证） | [`docs/05_设计模式决策报告.md`](docs/05_设计模式决策报告.md) |
| 设计评审记录表 | [`docs/06_设计评审记录表.md`](docs/06_设计评审记录表.md) |
| 变更需求单与影响分析 | [`docs/07_变更需求单与影响分析.md`](docs/07_变更需求单与影响分析.md) |
| 回归测试表（41 条） | [`docs/08_回归测试表.xlsx`](docs/08_回归测试表.xlsx) |
| 可维护性对照 | [`docs/09_可维护性对照.md`](docs/09_可维护性对照.md) |
| AI 协作记录 | [`AI_DEV_LOG.md`](AI_DEV_LOG.md) |
| 项目总结（7 页） | [`docs/项目总结.docx`](docs/项目总结.docx) |
| 答辩 PPT | [`docs/演示PPT.pptx`](docs/演示PPT.pptx) |
| 两版源代码 | 标签 `baseline-v1` / `change-v2` |
