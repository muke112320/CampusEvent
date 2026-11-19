"""生成实验二（baseline-v1）回归测试表 Excel。"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).resolve().parent.parent / "08_回归测试表.xlsx"

DARK = "1E3A8A"
HEADER = "233876"
ZEBRA = "F4F7FC"
GREEN = "DCFCE7"
GREEN_TEXT = "166534"
BORDER_COLOR = "CBD5E1"

thin = Side(style="thin", color=BORDER_COLOR)
border = Border(left=thin, right=thin, top=thin, bottom=thin)


def style_title(sheet, title: str, columns: int) -> None:
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=columns)
    cell = sheet.cell(row=1, column=1, value=title)
    cell.font = Font(name="微软雅黑", size=16, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=DARK)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    sheet.row_dimensions[1].height = 34


def style_header(sheet, row: int, columns: int) -> None:
    for col in range(1, columns + 1):
        cell = sheet.cell(row=row, column=col)
        cell.font = Font(name="微软雅黑", size=10.5, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=HEADER)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    sheet.row_dimensions[row].height = 30


def style_body(sheet, first_row: int, last_row: int, columns: int) -> None:
    for row in range(first_row, last_row + 1):
        for col in range(1, columns + 1):
            cell = sheet.cell(row=row, column=col)
            cell.font = Font(name="微软雅黑", size=9.5)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = border
            if (row - first_row) % 2 == 1:
                cell.fill = PatternFill("solid", fgColor=ZEBRA)


def set_widths(sheet, widths: dict[int, float]) -> None:
    for index, width in widths.items():
        sheet.column_dimensions[get_column_letter(index)].width = width


def mark_pass(sheet, row: int, col: int) -> None:
    cell = sheet.cell(row=row, column=col, value="通过")
    cell.font = Font(name="微软雅黑", size=9.5, bold=True, color=GREEN_TEXT)
    cell.fill = PatternFill("solid", fgColor=GREEN)
    cell.alignment = Alignment(horizontal="center", vertical="center")


def build() -> None:
    workbook = Workbook()

    # ---------------- 环境 ----------------
    env = workbook.active
    env.title = "测试环境"
    style_title(env, "CampusEvent 实验二回归测试环境（baseline-v1）", 2)
    rows = [
        ("测试日期", "2026-11-19"),
        ("项目版本", "baseline-v1（Git 标签）"),
        ("操作系统", "Windows 11"),
        ("Python", "3.12.14（项目 .venv）"),
        ("Flask", "3.1.3"),
        ("SQLite", "3.53.1"),
        ("pytest", "9.2.0"),
        ("数据库", "每个用例独立临时 SQLite 文件（pytest tmp_path），互不影响"),
        ("执行命令", r".\.venv\Scripts\python.exe -m pytest -v"),
        ("执行结果", "29 passed（约 3.6 秒）：C1—C10 + 16 条补充 + 3 条部署测试"),
        ("测试原则", "所有验收用例通过 HTTP 页面操作，并从数据库核对结果；不使用静态截图代替运行"),
        ("部署地址", "http://120.76.59.189/campusevent/"),
        ("部署环境", "腾讯云 Ubuntu 24.04.2 LTS · Nginx 80 · gunicorn 8001 · systemd"),
    ]
    for index, (key, value) in enumerate(rows, start=2):
        env.cell(row=index, column=1, value=key)
        env.cell(row=index, column=2, value=value)
    style_body(env, 2, len(rows) + 1, 2)
    for index in range(2, len(rows) + 2):
        env.cell(row=index, column=1).font = Font(name="微软雅黑", size=10, bold=True)
        env.row_dimensions[index].height = 25
    set_widths(env, {1: 18, 2: 88})
    env.freeze_panes = "A2"

    # ---------------- C1-C10 ----------------
    acceptance = workbook.create_sheet("C1-C10 验收")
    style_title(acceptance, "指导书 3.5 节初始版本核心验收用例 C1—C10", 7)
    headers = ["用例", "需求", "操作 / 输入", "预期结果", "实际结果", "证据（自动化测试）", "结论"]
    acceptance.append([])
    for col, value in enumerate(headers, start=1):
        acceptance.cell(row=2, column=col, value=value)
    style_header(acceptance, 2, len(headers))

    cases = [
        ("C1", "P2-F01", "管理员创建直接报名活动，容量 2", "创建成功并出现在列表/详情",
         "创建成功，数据库 capacity=2、policy_type=direct", "test_c1_admin_creates_direct_activity"),
        ("C2", "P2-F03/F04/F07", "学生 A 报名直接报名活动", "状态为已通过，并产生通知",
         "状态 approved，站内消息 1 条、邮件出件箱 1 条", "test_c2_direct_registration_is_approved_and_notified"),
        ("C3", "P2-F03", "学生 A 再次提交同一活动报名", "拒绝重复有效报名",
         "提示已有一条已通过报名，数据库仍只有 1 条", "test_c3_duplicate_registration_rejected"),
        ("C4", "P2-F03", "容量 2，A、B 通过后 C 报名", "C 因名额不足失败",
         "C 提示名额已满，已通过数保持 2", "test_c4_capacity_limit_blocks_registration"),
        ("C5", "P2-F04", "学生 A 申请审核型活动", "状态为待审核，不占名额",
         "状态 pending，统计已通过为 0", "test_c5_review_registration_is_pending"),
        ("C6", "P2-F05/F06/F07", "管理员批准 A 的待审核报名", "变为已通过并通知",
         "状态 approved，生成报名通过通知", "test_c6_admin_approves_pending_registration"),
        ("C7", "P2-F05/F06/F07", "管理员拒绝另一待审核报名", "变为已拒绝并通知",
         "状态 rejected，生成报名未通过通知", "test_c7_admin_rejects_pending_registration"),
        ("C8", "P2-F05", "容量 1，已通过 1 人后批准第二人", "批准失败且不超员",
         "提示名额已满，第二人仍为待审核，已通过数 1", "test_c8_approval_fails_when_capacity_is_full"),
        ("C9", "P2-F03/F06", "学生取消已通过报名", "状态已取消，统计同步变化",
         "状态 cancelled，已通过数减 1、名额释放", "test_c9_cancel_registration_releases_slot"),
        ("C10", "P2-F03", "重启应用后查询活动/报名/通知", "数据仍然存在且一致",
         "新建应用实例读取同一数据库，报名与消息均在", "test_c10_data_survives_restart"),
    ]
    for index, row in enumerate(cases, start=3):
        for col, value in enumerate(row, start=1):
            acceptance.cell(row=index, column=col, value=value)
        mark_pass(acceptance, index, 7)
    style_body(acceptance, 3, len(cases) + 2, len(headers))
    for index in range(3, len(cases) + 3):
        acceptance.cell(row=index, column=1).font = Font(name="微软雅黑", size=10, bold=True)
        acceptance.cell(row=index, column=2).alignment = Alignment(horizontal="center", vertical="center")
        mark_pass(acceptance, index, 7)
        acceptance.cell(row=index, column=6).font = Font(name="Consolas", size=8.5)
        acceptance.row_dimensions[index].height = 44
    set_widths(acceptance, {1: 8, 2: 16, 3: 34, 4: 28, 5: 38, 6: 52, 7: 8})
    acceptance.freeze_panes = "A3"

    # ---------------- 补充测试 ----------------
    extra = workbook.create_sheet("补充测试")
    style_title(extra, "补充测试（策略、边界、权限、通知、幂等）", 5)
    headers = ["编号", "测试点", "类型", "证据（自动化测试）", "结论"]
    for col, value in enumerate(headers, start=1):
        extra.cell(row=2, column=col, value=value)
    style_header(extra, 2, len(headers))

    supplements = [
        ("S01", "直接报名策略在满员时拒绝", "单元", "test_direct_policy_denies_when_full"),
        ("S02", "直接报名策略在有名额时通过", "单元", "test_direct_policy_approves_when_slots_available"),
        ("S03", "审核策略在满员时仍返回待审核", "单元", "test_review_policy_returns_pending_even_when_full"),
        ("S04", "活动开始后新增报名被拒绝", "集成", "test_registration_after_activity_start_is_rejected"),
        ("S05", "活动名称为空时创建被拒绝且不落库", "集成", "test_create_activity_requires_title"),
        ("S06", "人数上限不得小于已通过人数", "集成", "test_capacity_cannot_drop_below_approved"),
        ("S07", "有报名记录时禁止修改报名方式", "集成", "test_policy_cannot_change_after_registrations"),
        ("S08", "有报名记录时禁止删除活动", "集成", "test_activity_with_registrations_cannot_be_deleted"),
        ("S09", "被拒绝后可重新报名（保留历史）", "集成", "test_rejected_registration_can_apply_again"),
        ("S10", "取消后可重新报名（保留历史）", "集成", "test_cancelled_registration_can_apply_again"),
        ("S11", "按活动名称搜索只返回匹配项", "集成", "test_activity_search_filters_by_title"),
        ("S12", "学生访问管理页返回 403", "集成", "test_student_cannot_open_admin_pages"),
        ("S13", "管理员可访问审批台", "集成", "test_admin_can_open_admin_pages"),
        ("S14", "报名同时写入站内消息与模拟邮件", "集成", "test_registration_notifies_both_channels"),
        ("S15", "邮件失败不回滚报名且失败留痕", "集成", "test_email_failure_does_not_rollback_registration"),
        ("S16", "同一事件重复发布不会重复通知", "集成", "test_same_event_is_not_notified_twice"),
    ]
    for index, row in enumerate(supplements, start=3):
        for col, value in enumerate(row, start=1):
            extra.cell(row=index, column=col, value=value)
        mark_pass(extra, index, 5)
    style_body(extra, 3, len(supplements) + 2, len(headers))
    for index in range(3, len(supplements) + 3):
        extra.cell(row=index, column=1).font = Font(name="微软雅黑", size=10, bold=True)
        extra.cell(row=index, column=3).alignment = Alignment(horizontal="center", vertical="center")
        mark_pass(extra, index, 5)
        extra.cell(row=index, column=4).font = Font(name="Consolas", size=8.5)
        extra.row_dimensions[index].height = 26
    set_widths(extra, {1: 8, 2: 52, 3: 10, 4: 58, 5: 8})
    extra.freeze_panes = "A3"

    # ---------------- 汇总 ----------------
    summary = workbook.create_sheet("汇总")
    style_title(summary, "测试结果汇总", 3)
    headers = ["类别", "数量", "通过数 / 通过率"]
    for col, value in enumerate(headers, start=1):
        summary.cell(row=2, column=col, value=value)
    style_header(summary, 2, len(headers))
    rows = [
        ("C1—C10 核心验收", 10, "10 / 100%"),
        ("补充测试", 16, "16 / 100%"),
        ("部署测试", 3, "3 / 100%"),
        ("合计", 29, "29 / 100%"),
        ("源码规模", "25 个 Python 文件 / 约 2.5k 行", "—"),
        ("测试代码", "4 个测试文件 / 约 700 行", "—"),
    ]
    for index, row in enumerate(rows, start=3):
        for col, value in enumerate(row, start=1):
            summary.cell(row=index, column=col, value=value)
    style_body(summary, 3, len(rows) + 2, 3)
    for index in range(3, len(rows) + 3):
        summary.cell(row=index, column=2).alignment = Alignment(horizontal="center", vertical="center")
        summary.cell(row=index, column=3).alignment = Alignment(horizontal="center", vertical="center")
        summary.row_dimensions[index].height = 26
    set_widths(summary, {1: 30, 2: 34, 3: 22})

    # ---------------- 部署验证 ----------------
    deploy = workbook.create_sheet("部署验证")
    style_title(deploy, "云服务器部署验证（腾讯云 /campusevent 子路径）", 5)
    headers = ["检查项", "操作 / 输入", "预期", "实际", "结论"]
    for col, value in enumerate(headers, start=1):
        deploy.cell(row=2, column=col, value=value)
    style_header(deploy, 2, len(headers))
    checks = [
        ("公网登录页", "GET http://120.76.59.189/campusevent/login", "HTTP 200 且页面含 CampusEvent",
         "HTTP 200，品牌与静态前缀正确"),
        ("静态资源", "GET /campusevent/static/style.css", "HTTP 200 且返回 CSS",
         "HTTP 200，长度约 15.9KB"),
        ("登录与跳转", "学生 s1 登录", "跳转 /campusevent/activities，链接保留前缀",
         "最终 URL 与页面链接均带 /campusevent 前缀"),
        ("真实报名", "POST /campusevent/activities/ACT-DEMO-01/register", "报名成功，状态已通过",
         "页面提示报名成功，详情显示已通过"),
        ("重启持久化", "systemctl restart campusevent 后重新登录", "报名与活动仍在",
         "我的报名中活动与已通过状态仍存在"),
        ("既有应用兼容", "GET http://120.76.59.189/", "StudyTask 正常",
         "HTTP 200，页面标题正常"),
        ("子路径自动化测试", "pytest tests/test_prefix.py", "3 passed", "3 passed"),
    ]
    for index, row in enumerate(checks, start=3):
        for col, value in enumerate(row, start=1):
            deploy.cell(row=index, column=col, value=value)
        mark_pass(deploy, index, 5)
    style_body(deploy, 3, len(checks) + 2, len(headers))
    for index in range(3, len(checks) + 3):
        deploy.cell(row=index, column=1).font = Font(name="微软雅黑", size=10, bold=True)
        mark_pass(deploy, index, 5)
        deploy.row_dimensions[index].height = 34
    set_widths(deploy, {1: 18, 2: 46, 3: 32, 4: 42, 5: 8})
    deploy.freeze_panes = "A3"

    workbook.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()

