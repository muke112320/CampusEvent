"""生成实验二回归测试表 Excel（baseline-v1 + change-v2 教师变更单）。"""

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
ORANGE = "FFF1E6"
ORANGE_TEXT = "C2410C"
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


def write_table(sheet, title: str, headers: list[str], rows: list[tuple],
                widths: dict[int, float], evidence_col: int, mark_col: int,
                row_height: int = 30, aligns: tuple[int, ...] = ()) -> None:
    style_title(sheet, title, len(headers))
    for col, value in enumerate(headers, start=1):
        sheet.cell(row=2, column=col, value=value)
    style_header(sheet, 2, len(headers))
    for index, row in enumerate(rows, start=3):
        for col, value in enumerate(row, start=1):
            sheet.cell(row=index, column=col, value=value)
    style_body(sheet, 3, len(rows) + 2, len(headers))
    for index in range(3, len(rows) + 3):
        sheet.cell(row=index, column=1).font = Font(name="微软雅黑", size=10, bold=True)
        mark_pass(sheet, index, mark_col)
        sheet.cell(row=index, column=evidence_col).font = Font(name="Consolas", size=8.5)
        for col in aligns:
            sheet.cell(row=index, column=col).alignment = Alignment(
                horizontal="center", vertical="center")
        sheet.row_dimensions[index].height = row_height
    set_widths(sheet, widths)
    sheet.freeze_panes = "A3"


def build() -> None:
    workbook = Workbook()

    # ---------------- 环境 ----------------
    env = workbook.active
    env.title = "测试环境"
    style_title(env, "CampusEvent 实验二回归测试环境（baseline-v1 → change-v2）", 2)
    rows = [
        ("测试日期", "2026-11-19（初版） / 2026-11-26（变更版回归）"),
        ("项目版本", "baseline-v1（Git 标签） → change-v2（Git 标签）"),
        ("操作系统", "Windows 11"),
        ("Python", "3.12.14（项目 .venv）"),
        ("Flask", "3.1.3"),
        ("SQLite", "3.53.1"),
        ("pytest", "9.2.0"),
        ("数据库", "每个用例独立临时 SQLite 文件（pytest tmp_path），互不影响"),
        ("执行命令", r".\.venv\Scripts\python.exe -m pytest -v"),
        ("baseline-v1 结果", "29 passed：C1—C10 + 16 条补充 + 3 条子路径部署测试"),
        ("change-v2 结果", "41 passed：上述 29 条全部回归 + 12 条教师变更单测试"),
        ("变更来源", "《实验二教师专用材料》：CR-01 年级限定报名、CR-02 模拟邮件通知"),
        ("测试原则", "所有验收用例通过 HTTP 页面操作，并从数据库核对结果；不使用静态截图代替运行"),
        ("迁移测试", "用 v1 数据库快照执行 migrate()，核对年级回填、数据保留与邮件台账结构"),
        ("部署地址", "http://120.76.59.189/campusevent/"),
        ("线上版本", "change-v2（2026-11-26 升级；迁移前恢复 baseline 数据库）"),
        ("部署环境", "腾讯云 Ubuntu 24.04.2 LTS · Nginx 80 · gunicorn 8001 · systemd"),
    ]
    for index, (key, value) in enumerate(rows, start=2):
        env.cell(row=index, column=1, value=key)
        env.cell(row=index, column=2, value=value)
    style_body(env, 2, len(rows) + 1, 2)
    for index in range(2, len(rows) + 2):
        env.cell(row=index, column=1).font = Font(name="微软雅黑", size=10, bold=True)
        env.row_dimensions[index].height = 25
    set_widths(env, {1: 18, 2: 96})
    env.freeze_panes = "A2"

    # ---------------- C1-C10 ----------------
    acceptance = [
        ("C1", "P2-F01", "管理员创建直接报名活动，容量 2", "创建成功并出现在列表/详情",
         "创建成功，数据库 capacity=2、policy_type=direct", "test_c1_admin_creates_direct_activity"),
        ("C2", "P2-F03/F04/F07", "学生 A 报名直接报名活动", "状态为已通过，并产生通知",
         "状态 approved，站内消息 1 条、出件箱邮件 1 封", "test_c2_direct_registration_is_approved_and_notified"),
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
    sheet = workbook.create_sheet("C1-C10 验收")
    write_table(
        sheet, "指导书 3.5 节核心验收用例 C1—C10（baseline-v1 与 change-v2 均通过）",
        ["用例", "需求", "操作 / 输入", "预期结果", "实际结果", "证据（自动化测试）", "结论"],
        acceptance, {1: 8, 2: 16, 3: 34, 4: 28, 5: 38, 6: 52, 7: 8},
        evidence_col=6, mark_col=7, row_height=44, aligns=(2,),
    )

    # ---------------- 教师变更 CR1 / CR2 ----------------
    change_cases = [
        ("CR1-01", "CR-01", "大二学生 s1 报名年级限定活动", "通过",
         "状态 approved，页面提示报名成功", "test_cr1_01_grade2_student_can_register"),
        ("CR1-02", "CR-01", "大三学生 s2 报名年级限定活动", "通过",
         "状态 approved，页面提示报名成功", "test_cr1_02_grade3_student_can_register"),
        ("CR1-03", "CR-01", "大一学生 s3 报名年级限定活动", "拒绝并显示原因",
         "提示“仅限大二、大三”，含“大一”，报名数 0", "test_cr1_03_grade1_student_rejected_with_reason"),
        ("CR1-04", "CR-01", "大四学生 s4 报名年级限定活动", "拒绝并显示原因",
         "提示“仅限大二、大三”，含“大四”，报名数 0", "test_cr1_04_grade4_student_rejected_with_reason"),
        ("CR1-05a", "CR-01", "年级符合但容量 1 已满，第二位大二报名", "仍受名额限制",
         "提示名额已满，approved 保持 1", "test_cr1_capacity_limit_still_applies"),
        ("CR1-05b", "CR-01", "年级符合时重复报名同一活动", "仍受重复报名限制",
         "提示不能重复报名，仍只有 1 条", "test_cr1_duplicate_registration_still_rejected"),
        ("CR1-05c", "CR-01", "大一学生报名原直接/审核活动", "原策略行为不变",
         "直接报名通过；审核报名为待审核", "test_cr1_existing_policies_unchanged"),
        ("CR2-01", "CR-02", "直接报名通过", "站内消息和模拟邮件均有记录",
         "messages 1 条；email_deliveries sent；email_outbox 1 封",
         "test_cr2_01_direct_approval_records_message_and_email"),
        ("CR2-02", "CR-02", "审核批准与拒绝", "两种渠道记录对应结果",
         "通过/拒绝各有站内消息与 sent 邮件，主题对应", "test_cr2_02_review_approve_and_reject_both_channels"),
        ("CR2-03", "CR-02", "模拟邮件发送失败", "报名状态正确、错误有日志",
         "报名 approved；email_deliveries failed 含 SMTP；出件箱 0",
         "test_cr2_03_email_failure_keeps_registration_and_logs"),
        ("CR2-04", "CR-02", "重复提交同一业务动作", "不应重复生成多份相同通知",
         "两次 publish 只新增 1 封邮件", "test_cr2_04_same_event_sends_only_one_email"),
        ("CR2-05", "CR-02", "v1 数据迁移到 v2", "保留数据并具备年级/邮件台账",
         "版本 2；s1 年级=2；旧活动/报名保留；唯一约束生效",
         "test_cr2_05_migration_from_v1_preserves_data"),
    ]
    sheet = workbook.create_sheet("变更测试 CR1-CR2")
    write_table(
        sheet, "教师变更单测试：CR-01 年级限定报名 + CR-02 模拟邮件通知（12 条）",
        ["编号", "变更单", "操作 / 输入", "预期结果", "实际结果", "证据（自动化测试）", "结论"],
        change_cases, {1: 10, 2: 8, 3: 34, 4: 26, 5: 40, 6: 54, 7: 8},
        evidence_col=6, mark_col=7, row_height=40, aligns=(2,),
    )

    # ---------------- 补充测试 ----------------
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
    sheet = workbook.create_sheet("补充测试")
    write_table(
        sheet, "基线补充测试（策略、边界、权限、通知、幂等）",
        ["编号", "测试点", "类型", "证据（自动化测试）", "结论"],
        supplements, {1: 8, 2: 52, 3: 10, 4: 58, 5: 8},
        evidence_col=4, mark_col=5, row_height=26, aligns=(3,),
    )

    # ---------------- 部署测试 ----------------
    deploy_cases = [
        ("P01", "子路径登录页可访问", "集成", "test_login_page_works_under_prefix"),
        ("P02", "登录后跳转与导航保留前缀", "集成", "test_login_and_navigation_keep_prefix"),
        ("P03", "取消报名重定向保留前缀", "集成", "test_cancel_redirect_keeps_prefix"),
    ]
    sheet = workbook.create_sheet("部署测试")
    write_table(
        sheet, "子路径部署测试（/campusevent）",
        ["编号", "测试点", "类型", "证据（自动化测试）", "结论"],
        deploy_cases, {1: 8, 2: 52, 3: 10, 4: 58, 5: 8},
        evidence_col=4, mark_col=5, row_height=26, aligns=(3,),
    )

    # ---------------- 线上部署验证 ----------------
    checks = [
        ("升级前备份", "恢复 2026-11-25 备份中的 baseline 数据库（v1）", "version=1，4 活动 / 5 报名",
         "备份解包后 version=1；activities=4；registrations=5"),
        ("代码上传", "上传 change-v2 的 app/、wsgi.py、requirements", "新文件到位",
         "app/services/mock_email.py 存在；app/services/email.py 已移除"),
        ("服务重启", "systemctl restart campusevent", "active，无启动异常",
         "active；本地 /campusevent/login 返回 200"),
        ("数据库迁移", "应用启动自动执行 migrate()", "schema_version 1 → 2",
         "升级前 version=1，升级后 version=2"),
        ("年级回填", "迁移脚本按演示账号语义赋值", "s1=2、s2=3、s3=1、s4=4、admin=4",
         "查询 students 得到相同结果"),
        ("既有数据保留", "升级前后统计活动与报名", "行数与状态不变",
         "activities 4→4；registrations 5→5；approved 3、rejected 2"),
        ("邮件台账建表", "检查 email_deliveries", "表存在且唯一约束生效",
         "表存在；迁移测试验证 (event_id, student_id) 唯一"),
        ("公网登录页", "GET http://120.76.59.189/campusevent/login", "HTTP 200 且显示三类报名方式",
         "HTTP 200，含“三类报名方式”“年级限定”"),
        ("管理员表单", "登录 admin 后打开新建活动页", "报名方式含“年级限定报名”",
         "HTTP 200，“年级限定报名”出现 2 次"),
        ("通知台账", "GET /campusevent/admin/notifications", "含“模拟邮件发送记录”",
         "HTTP 200，页面含模拟邮件发送记录"),
        ("既有应用兼容", "GET http://120.76.59.189/", "StudyTask 正常", "HTTP 200"),
    ]
    sheet = workbook.create_sheet("部署验证 V2")
    write_table(
        sheet, "change-v2 线上部署验证（2026-11-26，腾讯云 /campusevent）",
        ["检查项", "操作 / 输入", "预期", "实际", "结论"],
        checks, {1: 18, 2: 44, 3: 32, 4: 54, 5: 8},
        evidence_col=4, mark_col=5, row_height=38,
    )

    # ---------------- 汇总 ----------------
    summary_rows = [
        ("C1—C10 核心验收", 10, "10 / 100%", "初版验收，change-v2 全量回归通过"),
        ("S01—S16 基线补充", 16, "16 / 100%", "策略、边界、权限、通知、幂等"),
        ("CR1 / CR2 变更测试", 12, "12 / 100%", "年级准入、邮件渠道、迁移与幂等"),
        ("P01—P03 部署测试", 3, "3 / 100%", "/campusevent 子路径登录、静态资源、重定向"),
        ("合计", 41, "41 / 100%", "0 失败 / 0 跳过"),
        ("源码规模", "25 个 Python 文件 / 2778 行", "—", "app/ 含 docstring 与类型注解"),
        ("测试代码", "5 个测试文件 / 41 条用例", "—", "含 3 条部署测试"),
    ]
    sheet = workbook.create_sheet("汇总")
    style_title(sheet, "测试结果汇总（change-v2）", 4)
    headers = ["类别", "数量", "通过数 / 通过率", "说明"]
    for col, value in enumerate(headers, start=1):
        sheet.cell(row=2, column=col, value=value)
    style_header(sheet, 2, len(headers))
    for index, row in enumerate(summary_rows, start=3):
        for col, value in enumerate(row, start=1):
            sheet.cell(row=index, column=col, value=value)
    style_body(sheet, 3, len(summary_rows) + 2, 4)
    for index in range(3, len(summary_rows) + 3):
        sheet.cell(row=index, column=2).alignment = Alignment(horizontal="center", vertical="center")
        sheet.cell(row=index, column=3).alignment = Alignment(horizontal="center", vertical="center")
        sheet.row_dimensions[index].height = 26
    set_widths(sheet, {1: 28, 2: 30, 3: 20, 4: 44})

    # ---------------- 两版对照 ----------------
    compare_rows = [
        ("测试用例数", "29", "41", "+12（CR1 / CR2）"),
        ("测试结果", "29 passed", "41 passed", "C1—C10 与全部基线测试无回归"),
        ("报名方式", "direct / review", "direct / review / grade_limited", "+1 策略实现"),
        ("学生字段", "student_id/name/email/role", "另加 grade（1—4）", "+1 字段与 CHECK"),
        ("邮件通道", "出件箱邮件（无独立状态台账）", "MockEmailSender + email_deliveries", "记录收件人/主题/内容/状态/时间"),
        ("核心业务服务修改", "—", "0", "Registration/Approval/Activity 未改"),
        ("Python 文件 / 源码行", "25 / 2497", "25 / 2778", "0 / +281"),
        ("类定义数", "52", "53", "净 +1（新增 4、删除 3）"),
        ("数据库迁移", "v1", "v2（1 步）", "grade 列、CHECK 重建、邮件台账"),
    ]
    sheet = workbook.create_sheet("两版对照")
    write_table(
        sheet, "baseline-v1 与 change-v2 回归对照",
        ["指标", "baseline-v1", "change-v2", "变化 / 说明"],
        compare_rows, {1: 24, 2: 38, 3: 42, 4: 44},
        evidence_col=4, mark_col=4, row_height=26,
    )
    # 对照表最后一列是“说明”，不该标“通过”，清除
    for row in range(3, len(compare_rows) + 3):
        cell = sheet.cell(row=row, column=4)
        cell.value = compare_rows[row - 3][3]
        cell.fill = PatternFill("solid", fgColor="FFFFFF")
        cell.font = Font(name="微软雅黑", size=9.5)

    workbook.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
