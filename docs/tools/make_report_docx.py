"""生成实验二项目总结 DOCX（baseline-v1 + change-v2，教师变更单版本）。"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parent.parent
IMAGES = BASE / "images"
OUT = BASE / "项目总结.docx"

NAVY = RGBColor(0x1E, 0x3A, 0x8A)
DARK = RGBColor(0x17, 0x20, 0x33)
GRAY = RGBColor(0x5B, 0x67, 0x79)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def set_font(run, name: str = "宋体", size: float = 10.5, bold: bool = False,
             color: RGBColor | None = None, mono: bool = False) -> None:
    run.font.name = "Consolas" if mono else "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)


def body(doc, text: str, *, size: float = 10.2, bold: bool = False, indent: bool = True,
         color: RGBColor | None = None, space_after: float = 3, align=None):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.2
    if indent:
        paragraph.paragraph_format.first_line_indent = Cm(0.74)
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    set_font(run, size=size, bold=bold, color=color)
    return paragraph


def bullet(doc, text: str, size: float = 10.2) -> None:
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.2
    run = paragraph.add_run(text)
    set_font(run, size=size)


def heading(doc, text: str, level: int = 1) -> None:
    style = doc.styles[f"Heading {level}"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(15 if level == 1 else 12)
    style.font.bold = True
    style.font.color.rgb = NAVY
    style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "黑体")
    paragraph = doc.add_heading(level=level)
    paragraph.paragraph_format.space_before = Pt(11 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(text)
    set_font(run, name="黑体", size=15 if level == 1 else 12, bold=True, color=NAVY)


def shade(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def cell_text(cell, text: str, size: float = 8.4, bold: bool = False,
              color: RGBColor | None = None, center: bool = False) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.1
    if center:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(str(text))
    set_font(run, size=size, bold=bold, color=color)


def table(doc, headers: list[str], rows: list[list[str]], widths: list[float],
          size: float = 8.4, highlight: set[int] | None = None) -> None:
    table_obj = doc.add_table(rows=1, cols=len(headers))
    table_obj.style = "Table Grid"
    table_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_obj.autofit = False
    header_cells = table_obj.rows[0].cells
    for index, (header, width) in enumerate(zip(headers, widths)):
        header_cells[index].width = Cm(width)
        shade(header_cells[index], "1E3A8A")
        cell_text(header_cells[index], header, size=size, bold=True, color=WHITE, center=True)

    header_tr_pr = table_obj.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    header_tr_pr.append(tbl_header)

    for row_index, row in enumerate(rows):
        cells = table_obj.add_row().cells
        for index, value in enumerate(row):
            cells[index].width = Cm(widths[index])
            if row_index % 2 == 1:
                shade(cells[index], "F4F7FC")
            elif highlight and row_index in highlight:
                shade(cells[index], "FFF1E6")
            cell_text(cells[index], value, size=size)

    for row in table_obj.rows:
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def figure(doc, filename: str, caption: str, width: float = 16.5) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(IMAGES / filename), width=Cm(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(6)
    run = cap.add_run(caption)
    set_font(run, size=8.5, color=GRAY)


def two_figures(doc, items: list[tuple[str, str]], width: float = 7.4) -> None:
    table_obj = doc.add_table(rows=1, cols=len(items))
    table_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, (filename, caption) in enumerate(items):
        cell = table_obj.rows[0].cells[index]
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run().add_picture(str(IMAGES / filename), width=Cm(width))
        cap = cell.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        set_font(run, size=8, color=GRAY)
    for row in table_obj.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_page_number_footer(doc) -> None:
    footer = doc.sections[0].footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("第 ")
    set_font(run, size=9, color=GRAY)

    def field(instruction: str) -> None:
        field_run = paragraph.add_run()
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = instruction
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        field_run._r.append(begin)
        field_run._r.append(instr)
        field_run._r.append(end)
        set_font(field_run, size=9, color=GRAY)

    field("PAGE")
    run = paragraph.add_run(" 页，共 ")
    set_font(run, size=9, color=GRAY)
    field("NUMPAGES")
    run = paragraph.add_run(" 页")
    set_font(run, size=9, color=GRAY)


def cover(doc) -> None:
    for _ in range(3):
        doc.add_paragraph()
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("《软件工程》课程实践")
    set_font(run, name="黑体", size=15, color=GRAY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(16)
    run = paragraph.add_run("实验二 项目总结")
    set_font(run, name="黑体", size=32, bold=True, color=NAVY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(10)
    run = paragraph.add_run("基于设计模式的校园活动报名与管理系统")
    set_font(run, name="黑体", size=16, color=DARK)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("CampusEvent · baseline-v1 → change-v2")
    set_font(run, size=11.5, color=GRAY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("—" * 46)
    set_font(run, size=9, color=RGBColor(0x94, 0xA3, 0xB8))

    for _ in range(4):
        doc.add_paragraph()

    meta = [
        ("项目代号", "CampusEvent"),
        ("姓名", "柯文韬"),
        ("班级 / 学号", "____________ / ____________"),
        ("提交日期", "2026-11-26"),
        ("版本标签", "baseline-v1 / change-v2"),
        ("在线访问", "http://120.76.59.189/campusevent/"),
    ]
    for key, value in meta:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(7)
        key_run = paragraph.add_run(f"{key}：")
        set_font(key_run, size=12, color=GRAY)
        value_run = paragraph.add_run(value)
        set_font(value_run, name="黑体", size=12, color=DARK)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.1)
    section.right_margin = Cm(2.1)
    section.top_margin = Cm(1.9)
    section.bottom_margin = Cm(1.9)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.2)
    normal.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    normal.paragraph_format.line_spacing = 1.2

    add_page_number_footer(doc)
    cover(doc)

    # ------------------------------------------------------------------
    heading(doc, "一、项目概述")
    heading(doc, "1.1 项目目标", 2)
    body(doc, "本项目以校园活动报名为业务背景，重点不是堆功能，而是完成一次完整的设计驱动开发："
              "先从需求中识别领域对象与职责边界，再用策略模式封装报名规则、用观察者模式解耦通知渠道，"
              "随后由 AI 按既定设计实现，最后用自动化测试与真实运行证据验收；初版验收后再按教师变更单"
              "完成一次需求变更，用真实差异检验设计的可扩展性。")
    bullet(doc, "设计先行：用例图、两版类图、五条关键时序图、设计模式决策报告与影响分析均先于对应实现完成。")
    bullet(doc, "可验证：41 条 pytest 用例全部通过，验收用例通过 HTTP 操作并从数据库核对结果。")
    bullet(doc, "可复现：Git 标签 baseline-v1 / change-v2 固定两版代码，文档记录统计口径与执行命令。")

    heading(doc, "1.2 需求范围（两版）", 2)
    table(
        doc,
        ["版本", "编号", "功能", "实现要点"],
        [
            ["v1", "P2-F01", "活动管理", "创建、编辑、删除活动；名称、类型、时间、地点、容量、报名方式"],
            ["v1", "P2-F02", "活动查看", "活动列表与详情，按名称搜索"],
            ["v1", "P2-F03", "报名 / 取消", "报名、取消；禁止重复有效报名；开始后禁止新增"],
            ["v1", "P2-F04", "报名策略", "直接报名即时通过；审核报名进入待审核"],
            ["v1", "P2-F05", "审批操作", "管理员批准/拒绝，批准时再次检查名额"],
            ["v1", "P2-F06", "状态管理", "待审核 / 已通过 / 已拒绝 / 已取消"],
            ["v1", "P2-F07", "结果通知", "站内消息 + 出件箱邮件，失败留痕且不影响报名"],
            ["v1", "P2-F08", "统计", "已通过数、待审核数与剩余名额"],
            ["v2", "CR-01", "年级限定报名", "Student.grade（1—4）；仅大二、大三可报名，其他年级明确拒绝"],
            ["v2", "CR-02", "模拟邮件通知", "MockEmailSender + 邮件台账（收件人/主题/内容/状态/时间）；失败留痕、不重复发送"],
        ],
        widths=[1.3, 2.0, 2.8, 10.6],
        highlight={8, 9},
    )
    body(doc, "明确不做：用户注册、密码体系、真实邮件/短信网关、消息队列、移动端 App。范围外功能不因“看起来更完整”而加入。")

    # ------------------------------------------------------------------
    heading(doc, "二、设计")
    heading(doc, "2.1 分层与依赖方向", 2)
    body(doc, "Web 层（蓝图/模板）→ 应用服务（报名、审批、活动）→ 领域层（模型、策略、事件）→ 仓储（SQLite）→ 数据库；"
              "通知通过 EventBus 分发给站内消息与邮件订阅者。domain/ 不导入 Flask 与 sqlite3，可独立单测；"
              "web/ 不直接写 SQL；服务依赖 PolicyRegistry 与 EventBus 抽象，装配集中在 container.py。")

    heading(doc, "2.2 领域模型与状态", 2)
    figure(doc, "class_domain_change.png", "图 1  变更版领域模型类图（橙色为 CR-01/CR-02 变更点）")
    body(doc, "两版之间没有新增活动/报名实体，只扩展学生年级、报名方式枚举与邮件审计实体。关键不变量保持："
              "只有 approved 占用名额；同一学生同一活动最多一条 pending/approved；活动入口统一由 "
              "is_open_for_registration 判断。年级限定活动与普通活动共用 Activity 结构。")

    heading(doc, "2.3 策略模式与观察者模式", 2)
    body(doc, "RegistrationPolicy.evaluate() 是模板方法，固定执行“公共规则→策略判定”；子类只实现 decide()。"
              "初版有两个策略：直接报名（满员拒绝）、审核报名（一律待审核）。变更版新增 GradeLimitedRegistrationPolicy，"
              "它继承 DirectRegistrationPolicy，只增加年级校验并复用容量判定；RegistrationService 在本次变更中零修改。")
    body(doc, "报名事务提交后发布领域事件，EventBus 分发给站内消息与模拟邮件两个订阅者。变更版把邮件渠道实现"
              "替换为 MockEmailSender，新增 email_deliveries 台账记录收件人、主题、内容、状态与时间；"
              "站内订阅者与业务服务未修改，邮件失败只留痕、不回滚报名。")
    figure(doc, "class_design_change.png", "图 2  变更版设计类图：年级策略、MockEmailSender 与邮件台账")

    # ------------------------------------------------------------------
    heading(doc, "三、需求变更与影响分析")
    heading(doc, "3.1 教师变更单", 2)
    table(
        doc,
        ["变更单", "内容", "关键约束"],
        [
            ["CR-01 年级限定报名", "Student 增加 grade（1—4）；新增 grade_limited 报名方式；仅大二、大三可报名，"
                                  "其他年级收到明确提示",
             "仍遵守名额、活动开始时间、重复报名；原有直接/审核行为不变"],
            ["CR-02 模拟邮件通知", "报名通过、审核通过或拒绝时，站内通知继续运行，同时由 MockEmailSender "
                                  "记录邮件收件人、主题、内容、状态与时间",
             "失败只留痕不回滚报名；同一业务事件不重复发送"],
        ],
        widths=[3.0, 8.6, 5.1],
    )

    heading(doc, "3.2 影响分析与实际结果", 2)
    table(
        doc,
        ["影响对象", "变更内容", "实际结果"],
        [
            ["领域模型", "Student.grade + grade_label；PolicyType 增加 grade_limited", "models.py +17/−1；无新增活动子类"],
            ["报名策略", "GradeLimitedRegistrationPolicy 继承 Direct", "仅新增 1 个策略类 + 注册 1 行；核心服务零改动"],
            ["数据迁移", "students 增列；activities 扩展 CHECK；新增 email_deliveries", "1 步迁移；旧数据 4 活动/5 报名保留"],
            ["邮件通道", "MockEmailSender 取代旧出件箱网关", "新增 4 类、删除 3 类；站内订阅者未改"],
            ["页面", "年级限定提示、按钮文案、邮件台账展示", "详情页/管理页/登录页同步"],
        ],
        widths=[2.6, 7.4, 6.7],
    )

    heading(doc, "3.3 迁移与实施", 2)
    body(doc, "SQLite 不支持直接修改 CHECK 约束，迁移采用“建新表→复制数据→删旧表→重命名”：students 增加 grade 列"
              "（默认 1，CHECK 1—4），演示账号按语义回填；activities 重建并允许 grade_limited；新增 email_deliveries "
              "邮件台账与 (event_id, student_id) 唯一约束。整个过程在显式事务内完成，异常整体回滚，版本号写为 2。")
    body(doc, "实现中真实遇到两个问题：服务器上旧的数据库结构与本次 v2 迁移不一致，不能直接复用"
              "（改为从升级前备份恢复 baseline 数据后再迁移）；SQLite 添加带 CHECK 的列只能在建列时完成——"
              "迁移顺序与事务边界必须一次写对。")

    # ------------------------------------------------------------------
    heading(doc, "四、测试与回归")
    heading(doc, "4.1 环境与结果", 2)
    body(doc, "在项目虚拟环境执行 .\\.venv\\Scripts\\python.exe -m pytest -q：baseline-v1 为 29 passed，"
              "change-v2 为 41 passed（约 5 秒），0 失败 / 0 跳过。每个用例使用独立临时 SQLite 文件；"
              "验收用例通过 HTTP 提交表单并从数据库核对状态、统计、通知与邮件台账。")
    table(
        doc,
        ["类别", "数量", "结果", "说明"],
        [
            ["C1—C10 核心验收", "10", "全部通过", "初版验收，change-v2 全量回归无退化"],
            ["S01—S16 基线补充", "16", "全部通过", "策略、边界、权限、通知失败与幂等"],
            ["CR1 / CR2 变更测试", "12", "全部通过", "年级准入、容量/重复、邮件渠道、迁移"],
            ["P01—P03 部署测试", "3", "全部通过", "/campusevent 子路径登录、静态资源、重定向"],
        ],
        widths=[4.2, 1.8, 2.6, 8.1],
    )

    heading(doc, "4.2 变更测试明细", 2)
    table(
        doc,
        ["编号", "变更", "测试点", "结果"],
        [
            ["CR1-01", "CR-01", "大二学生报名年级限定活动 → 通过", "通过"],
            ["CR1-02", "CR-01", "大三学生报名年级限定活动 → 通过", "通过"],
            ["CR1-03", "CR-01", "大一学生 → 拒绝并提示“仅限大二、大三”", "通过"],
            ["CR1-04", "CR-01", "大四学生 → 拒绝并提示实际年级", "通过"],
            ["CR1-05a", "CR-01", "年级符合但名额已满 → 仍拒绝", "通过"],
            ["CR1-05b", "CR-01", "年级符合但重复报名 → 仍拒绝", "通过"],
            ["CR1-05c", "CR-01", "原直接/审核策略行为不变", "通过"],
            ["CR2-01", "CR-02", "直接报名通过 → 站内 + 邮件均有记录", "通过"],
            ["CR2-02", "CR-02", "审核通过/拒绝 → 双渠道对应结果", "通过"],
            ["CR2-03", "CR-02", "邮件失败 → 报名正确、错误留痕", "通过"],
            ["CR2-04", "CR-02", "重复事件 → 只发送一封", "通过"],
            ["CR2-05", "CR-02", "v1→v2 迁移保留数据并回填年级", "通过"],
        ],
        widths=[2.2, 1.6, 10.2, 1.7],
    )

    heading(doc, "4.3 运行界面证据", 2)
    two_figures(doc, [
        ("change_grade_detail.png", "图 3  年级限定活动：大一学生看到明确提示"),
        ("change_email_ledger.png", "图 4  通知台账：MockEmailSender 邮件记录"),
    ])

    # ------------------------------------------------------------------
    heading(doc, "五、结果分析")
    heading(doc, "5.1 两版度量", 2)
    table(
        doc,
        ["指标", "baseline-v1", "change-v2", "说明"],
        [
            ["Python 文件 / 源码行", "25 / 2497", "25 / 2778", "+281 行；删除旧邮件网关、新增 MockEmailSender"],
            ["类定义数", "52", "53", "净 +1：新增 4、删除 3"],
            ["报名策略 / 报名方式", "2 / 2 种", "3 / 3 种", "新增年级限定策略"],
            ["核心业务服务修改", "—", "0", "Registration/Approval/Activity 未改"],
            ["测试用例 / 结果", "29 / 全过", "41 / 全过", "C1—C10 无回归"],
        ],
        widths=[4.4, 3.4, 3.4, 5.9],
    )

    heading(doc, "5.2 设计模式的可测收益", 2)
    body(doc, "策略模式的收益不是“用了模式”，而是 CR-01 只新增 1 个策略类并在注册表登记 1 行，报名主流程与公共校验零改动；"
              "观察者模式的收益是 CR-02 把邮件实现替换为 MockEmailSender 时，站内订阅者与业务服务零修改。"
              "这两点都可以用 git diff 与测试名复核，而不是主观判断。")

    heading(doc, "5.3 成本与局限", 2)
    body(doc, "代价同样明显：类数量与调用链变长，一次报名跨 Web、服务、策略、仓储、事件总线与两个订阅者；"
              "通知为进程内同步投递，没有重试队列；SQLite 适合单机演示，高并发需替换数据库。"
              "更重要的是，模式不保证正确性：年级迁移、CHECK 重建、邮件失败边界与事件级幂等，"
              "都必须由设计者显式定义并由测试固定。")

    # ------------------------------------------------------------------
    heading(doc, "六、问题与反思")
    table(
        doc,
        ["问题", "现象与定位", "处理与经验"],
        [
            ["依赖安装失败", "默认 PyPI 源无法解析 files.pythonhosted.org，报错停留在“找不到包”",
             "用 pip download 观察到 DNS 解析失败，改用国内镜像；先看网络层再判断版本"],
            ["HTML 首行被转义", "base.html 写成 &lt;!doctype html&gt;，缺少标准模式声明",
             "自查模板首行并修正，用真实浏览器截图复核；AI 产出的“像 HTML”不等于合法 HTML"],
            ["模板变量缺失", "审批页使用 stats，但路由未传入，访问时报模板错误",
             "对照模板与路由上下文补字典；模板与路由无编译期约束，需页面级测试覆盖"],
            ["CHECK 约束无法修改", "SQLite 不能 ALTER 已有 CHECK，grade_limited 无法写入旧表",
             "重建 activities 表并复制数据；迁移整体事务化，迁移测试固定旧数据保留"],
            ["邮件幂等的两层保证", "仅靠订阅者 claim 时，直接重建事件对象仍可能重复发送",
             "订阅者 claim + email_deliveries 唯一约束双保险；CR2-04 验证只发送一封"],
        ],
        widths=[2.8, 6.6, 7.3],
    )
    body(doc, "反思：AI 能快速生成结构完整的分层代码，但它不会自动对“事务边界、通知失败、数据迁移”负责；"
              "这些判断必须由人先写进设计与影响分析，再用测试固定。变更阶段最值得记录的不是“新增了多少功能”，"
              "而是“新增一种规则需要改多少核心代码、哪些不变量必须人工守住”。本项目用 1 个策略类与 0 个核心服务修改"
              "回答了前者，用迁移测试、故障注入与唯一约束回答了后者。")

    # ------------------------------------------------------------------
    heading(doc, "七、部署与运行")
    body(doc, "系统已部署到腾讯云轻量应用服务器（Ubuntu 24.04.2 LTS），访问地址 http://120.76.59.189/campusevent/ 。"
              "Nginx 监听 80，将 /campusevent/ 反向代理到 gunicorn 127.0.0.1:8001，由 systemd 服务 campusevent 托管；"
              "应用通过 CAMPUSEVENT_URL_PREFIX 挂载子路径，会话 cookie 使用独立名称 campusevent_session，"
              "与同主机根路径的 StudyTask 互不影响。")
    body(doc, "2026-11-26 已将线上从 baseline-v1 升级到 change-v2：先用升级前备份恢复 baseline 数据库，再上传新代码并重启；"
              "应用启动时自动执行 v1→v2 迁移，schema_version 由 1 升为 2，学生年级完成回填，"
              "原有 4 个活动、5 条报名完整保留；公网登录页显示“三类报名方式”，管理员新建活动表单含“年级限定报名”，"
              "通知台账显示“模拟邮件发送记录”，StudyTask 根路径未受影响。")
    body(doc, "复现：安装 requirements.txt 后运行 .\\.venv\\Scripts\\python.exe run.py；测试运行 pytest -q。"
              "首次启动自动建表并执行 v1→v2 迁移，写入演示数据；固定账号 admin（管理员）与 s1—s4（学生）。")

    heading(doc, "附录：交付物与复现")
    table(
        doc,
        ["交付物", "路径"],
        [
            ["初始 SRS 分析 / 用例说明", "docs/01_初始SRS分析.md、docs/02_用例说明.md"],
            ["初版与变更版 UML 类图", "docs/03_UML类图.md（4 张图）"],
            ["时序图（含年级限定与邮件）", "docs/04_时序图.md"],
            ["设计模式决策报告", "docs/05_设计模式决策报告.md"],
            ["设计评审记录表（含变更评审）", "docs/06_设计评审记录表.md"],
            ["变更需求单与影响分析", "docs/07_变更需求单与影响分析.md"],
            ["回归测试表", "docs/08_回归测试表.xlsx"],
            ["可维护性对照", "docs/09_可维护性对照.md"],
            ["AI 协作记录", "AI_DEV_LOG.md"],
            ["两版源码", "git checkout baseline-v1 / git checkout change-v2"],
            ["项目总结 / 答辩 PPT", "docs/项目总结.docx、docs/演示PPT.pptx"],
        ],
        widths=[5.6, 11.1],
    )

    doc.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
