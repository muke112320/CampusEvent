"""生成实验二（baseline-v1）实验报告 DOCX。"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parent.parent
IMAGES = BASE / "images"
OUT = BASE / "实验报告.docx"

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
    paragraph.paragraph_format.line_spacing = 1.22
    if indent:
        paragraph.paragraph_format.first_line_indent = Cm(0.74)
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    set_font(run, size=size, bold=bold, color=color)
    return paragraph


def bullet(doc, text: str, size: float = 10.5) -> None:
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.line_spacing = 1.3
    run = paragraph.add_run(text)
    set_font(run, size=size)


def heading(doc, text: str, level: int = 1) -> None:
    style = doc.styles[f"Heading {level}"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(16 if level == 1 else 12.5)
    style.font.bold = True
    style.font.color.rgb = NAVY
    style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "黑体")
    paragraph = doc.add_heading(level=level)
    paragraph.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(text)
    set_font(run, name="黑体", size=16 if level == 1 else 12.5, bold=True, color=NAVY)


def shade(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def cell_text(cell, text: str, size: float = 8.8, bold: bool = False,
              color: RGBColor | None = None, center: bool = False) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.15
    if center:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(str(text))
    set_font(run, size=size, bold=bold, color=color)


def table(doc, headers: list[str], rows: list[list[str]], widths: list[float],
          size: float = 8.8) -> None:
    table_obj = doc.add_table(rows=1, cols=len(headers))
    table_obj.style = "Table Grid"
    table_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_obj.autofit = False
    header_cells = table_obj.rows[0].cells
    for index, (header, width) in enumerate(zip(headers, widths)):
        header_cells[index].width = Cm(width)
        shade(header_cells[index], "1E3A8A")
        cell_text(header_cells[index], header, size=size, bold=True, color=WHITE, center=True)

    # 表头跨页重复，行内容不跨页拆分
    header_tr_pr = table_obj.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    header_tr_pr.append(tbl_header)
    for row in table_obj.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)

    for row_index, row in enumerate(rows):
        cells = table_obj.add_row().cells
        for index, value in enumerate(row):
            cells[index].width = Cm(widths[index])
            if row_index % 2 == 1:
                shade(cells[index], "F4F7FC")
            cell_text(cells[index], value, size=size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figure(doc, filename: str, caption: str, width: float = 15.8) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(IMAGES / filename), width=Cm(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    run = cap.add_run(caption)
    set_font(run, size=8.5, color=GRAY)


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
    paragraph.paragraph_format.space_before = Pt(18)
    run = paragraph.add_run("实验二实验报告")
    set_font(run, name="黑体", size=30, bold=True, color=NAVY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(10)
    run = paragraph.add_run("基于设计模式的校园活动报名与管理系统")
    set_font(run, name="黑体", size=16, color=DARK)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("CampusEvent · 初始验收版本 baseline-v1")
    set_font(run, size=11, color=GRAY)

    # 分隔线
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
        ("提交日期", "2026-11-19"),
        ("版本标签", "baseline-v1"),
    ]
    for key, value in meta:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(8)
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
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.2)
    normal.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    normal.paragraph_format.line_spacing = 1.22

    add_page_number_footer(doc)
    cover(doc)

    # 一、实验目标与需求范围
    heading(doc, "一、实验目标与需求范围")
    heading(doc, "1.1 实验目标", 2)
    body(doc, "本实验以校园活动报名为业务背景，目标不是“把功能堆出来”，而是先由学生完成职责划分与设计决策，"
              "再指导 AI 按设计实现，最后用自动化测试与真实运行证据验收。具体目标包括：")
    for text in [
        "从需求中识别领域对象、业务服务与职责边界，绘制用例图、类图与关键时序图；",
        "用策略模式封装两类报名规则，用观察者/事件机制解耦报名业务与通知渠道；",
        "在 AI 编码前完成设计评审，AI 只负责按既定接口实现，不替学生做架构决策；",
        "建立可复现的验收测试，覆盖 C1—C10 及名额、重复报名、通知失败等边界；",
        "为后续需求变更保留可扩展点，并能用指标而非口号评价设计收益。",
    ]:
        bullet(doc, text)

    heading(doc, "1.2 需求范围", 2)
    body(doc, "项目实现指导书 3.2 节与附录 B 的初始需求：管理员发布活动，学生浏览并报名；"
              "支持“直接报名”和“管理员审核”两类活动，报名与审核结果通过站内消息通知。"
              "功能清单如下：")
    table(
        doc,
        ["编号", "功能", "实现要点"],
        [
            ["P2-F01", "活动管理", "管理员创建、编辑、删除活动；名称、类型、时间、地点、人数上限、报名方式"],
            ["P2-F02", "活动查看", "学生浏览活动列表与详情，可按名称搜索"],
            ["P2-F03", "报名 / 取消", "报名、取消；禁止重复有效报名；活动开始后禁止新增"],
            ["P2-F04", "报名策略", "直接报名即时通过；审核报名进入待审核"],
            ["P2-F05", "审批操作", "管理员批准/拒绝，批准时再次检查名额"],
            ["P2-F06", "状态管理", "待审核 / 已通过 / 已拒绝 / 已取消"],
            ["P2-F07", "站内通知", "报名与审核结果写入站内消息，同时投递模拟邮件"],
            ["P2-F08", "统计", "按活动展示已通过数、待审核数与剩余名额"],
        ],
        widths=[2.0, 3.2, 11.4],
    )
    body(doc, "明确不做：用户注册、密码体系、多角色权限、真实邮件/短信网关、消息队列、移动端 App。"
              "范围外功能不因“看起来更完整”而加入，避免项目膨胀。验收依据为指导书 3.5 节的 C1—C10。")

    # 二、实现方案
    heading(doc, "二、实现方案")
    heading(doc, "2.1 运行环境", 2)
    table(
        doc,
        ["项目", "版本 / 说明"],
        [
            ["操作系统", "Windows 11"],
            ["Python", "3.12.14（项目内 .venv 虚拟环境）"],
            ["Web 框架", "Flask 3.1.3 + Jinja2 服务端渲染"],
            ["数据库", "SQLite 3.53.1（标准库 sqlite3，无 ORM）"],
            ["自动化测试", "pytest 9.2.0，26 条用例"],
            ["浏览器", "Microsoft Edge（无头模式截图）+ 常规桌面浏览器"],
        ],
        widths=[4.0, 12.4],
    )

    heading(doc, "2.2 系统结构", 2)
    body(doc, "系统采用分层结构，依赖方向自上而下，领域层不依赖 Flask 与 SQLite：")
    body(doc, "Web 层（蓝图/模板）→ 应用服务（报名、审批、活动）→ 领域层（模型、策略、事件）"
              "→ 仓储（SQLite）→ 数据库；通知通过 EventBus 分发给站内消息与邮件订阅者。", indent=False)
    bullet(doc, "domain/：Activity、Student、Registration、RegistrationPolicy、领域事件，纯 Python，可单测；")
    bullet(doc, "services/：编排事务、选择策略、提交后发布事件；不渲染页面、不直接拼 SQL；")
    bullet(doc, "repositories.py：对象与数据库行的映射；web/：路由、登录态与页面；")
    bullet(doc, "container.py：依赖装配，测试可替换邮件网关为故障注入实现。")

    heading(doc, "2.3 领域模型", 2)
    figure(doc, "class_domain_baseline.png", "图 1  领域模型类图（baseline-v1）")
    body(doc, "活动与报名是一对多组合，学生与报名是一对多关联；同一学生同一活动最多一条“待审核/已通过”"
              "有效报名，由部分唯一索引与领域查询双重保证。名额只统计“已通过”，待审核不占名额；"
              "统计对象 RegistrationStats 是派生值，不落库，避免状态变化后统计失真。")

    heading(doc, "2.4 策略模式：两类报名规则", 2)
    figure(doc, "class_design_baseline.png", "图 2  设计类图：策略模式与观察者模式")
    body(doc, "RegistrationPolicy.evaluate() 是模板方法，固定执行“公共规则→策略判定”的顺序；"
              "子类只实现 decide()。公共规则包括活动必须未开始、不得重复有效报名；"
              "名额口径（只算已通过）由上下文统一提供，而“满员后拒绝还是待审核”由策略决定，"
              "因此直接报名在满员时拒绝，审核报名仍可提交待审核。")
    body(doc, "RegistrationService 不出现 policy_type 的 if/elif 分支，"
              "新增报名方式只需实现策略并在 PolicyRegistry 注册。测试覆盖："
              "直接策略满员拒绝、有名额通过；审核策略满员仍返回待审核。")

    heading(doc, "2.5 观察者模式：报名与通知解耦", 2)
    body(doc, "报名事务提交后发布领域事件，EventBus 分发给站内消息与模拟邮件两个订阅者。"
              "订阅者异常被隔离并写入 notification_deliveries 台账；同一事件以 "
              "(event_id, subscriber, student_id) 唯一约束防止重复通知。通知失败不回滚报名，"
              "符合“通知失败应留痕、不得让已合法提交的报名无声消失”的要求。")
    body(doc, "报名、审批、取消三类事件复用同一套通知结构；新增通知渠道只需新增订阅者与装配一行，"
              "不需要修改报名或审批服务。")

    heading(doc, "2.6 数据库设计", 2)
    body(doc, "数据库共 6 张表：students 保存固定演示账号；activities 保存活动名称、时间、容量与报名方式；"
              "registrations 保存报名状态，并用部分唯一索引约束“同一学生同一活动最多一条有效报名”；"
              "messages 与 email_outbox 分别保存站内消息和模拟邮件；notification_deliveries 记录每个事件的"
              "投递渠道、状态与错误，并以 (event_id, subscriber, student_id) 唯一约束防止重复通知。")
    body(doc, "写操作使用 BEGIN IMMEDIATE 显式事务：先取写锁再检查名额，避免并发下两个请求同时占用最后一个名额。")

    # 三、实施过程
    heading(doc, "三、实施过程")
    heading(doc, "3.1 设计先行", 2)
    body(doc, "编码前完成需求分析、用例说明、初版 UML 类图、直接报名/审核报名/审批三张时序图，"
              "以及设计模式决策报告。设计评审表列出自检项与证据位置；按课程要求，评审需由其他同学"
              "逐项核对并签名，当前评审表已准备但签名栏留空，未以 AI 代替人工评审。")

    heading(doc, "3.2 AI 协作与人工判断", 2)
    table(
        doc,
        ["环节", "AI 承担", "人工判断与验证"],
        [
            ["需求分析", "根据指导书列出范围、领域对象候选与 C1—C10 清单", "确认只做两类报名与双通知，拒绝范围外功能"],
            ["架构设计", "给出策略/观察者草图与依赖方向", "确定名额公共口径、满员行为归策略；拒绝服务直接写消息表"],
            ["编码实现", "生成领域层、服务、仓储、路由与页面", "逐文件检查事务边界、状态转换与异常提示"],
            ["测试", "生成 26 条 pytest 用例", "逐条实跑并核对数据库结果，补充边界与故障注入"],
            ["验收", "编写文档与截图脚本", "用真实浏览器截图核对页面，不以静态假图代替运行"],
        ],
        widths=[2.6, 6.6, 7.2],
    )
    body(doc, "完整的协作记录（8 次关键事件、真实问题与修复）见项目根目录 AI_DEV_LOG.md；"
              "记录保留提示词要点与人工判断，未粘贴全部对话。")

    heading(doc, "3.3 Git 版本", 2)
    body(doc, "初始代码提交为 41de265（feat: 初始版本），设计文档提交为 048a41f（docs: 初始设计文档、"
              "UML 图与评审表），并以附注标签 baseline-v1 指向初始验收版本，可随时检出复现。")

    # 四、测试结果
    heading(doc, "四、测试结果")
    heading(doc, "4.1 测试环境与结果", 2)
    body(doc, "在项目虚拟环境中执行 .\\.venv\\Scripts\\python.exe -m pytest -v，结果 "
              "26 passed（约 2.8 秒）。每个测试使用独立的临时 SQLite 文件，互不影响；"
              "验收用例通过 HTTP 提交表单，再从数据库核对状态、统计与通知记录。")
    heading(doc, "4.2 核心验收用例 C1—C10", 2)
    table(
        doc,
        ["用例", "需求", "操作 / 输入", "预期结果", "实际结果（证据）", "结论"],
        [
            ["C1", "F01", "创建直接报名活动，容量 2", "创建成功", "数据库 capacity=2，policy_type=direct", "通过"],
            ["C2", "F03/F04", "学生 A 报名直接报名活动", "已通过并通知", "状态 approved，站内 1 条、邮件 1 封", "通过"],
            ["C3", "F03", "A 再次报名同一活动", "拒绝重复", "提示已有有效报名，仍只有 1 条", "通过"],
            ["C4", "F03", "容量 2，A、B 后 C 报名", "C 因满员失败", "提示名额已满，已通过数保持 2", "通过"],
            ["C5", "F04", "A 申请审核型活动", "状态待审核", "状态 pending，待审核不占名额", "通过"],
            ["C6", "F05/F06", "管理员批准 A", "已通过并通知", "状态 approved，生成通过通知", "通过"],
            ["C7", "F05/F06", "管理员拒绝另一申请", "已拒绝并通知", "状态 rejected，生成拒绝通知", "通过"],
            ["C8", "F05", "容量 1，已通过 1 人后批准第二人", "批准失败不超员", "提示名额已满，第二人仍待审核", "通过"],
            ["C9", "F03/F06", "A 取消已通过报名", "已取消，统计同步", "状态 cancelled，名额释放", "通过"],
            ["C10", "F03", "重启应用后查询", "数据仍一致", "新应用实例读取同一库，报名与消息均在", "通过"],
        ],
        widths=[1.2, 1.8, 3.9, 3.4, 5.2, 1.2],
        size=8.2,
    )
    body(doc, "补充 16 条测试覆盖策略、边界、权限、通知与幂等，全部通过；"
              "完整的用例编号、预期、实际与测试函数名见《回归测试表.xlsx》。")

    heading(doc, "4.3 实际界面", 2)
    body(doc, "以下截图由 Edge 无头浏览器访问真实运行实例生成，不是设计稿或静态假图。")
    table_obj = doc.add_table(rows=1, cols=2)
    table_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    images = [
        ("activities.png", "图 3  活动广场与我的报名状态"),
        ("admin_notifications.png", "图 4  通知投递台账与邮件出件箱"),
    ]
    for index, (filename, caption) in enumerate(images):
        cell = table_obj.rows[0].cells[index]
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run().add_picture(str(IMAGES / filename), width=Cm(7.2))
        cap = cell.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        set_font(run, size=8, color=GRAY)
    # 截图表格整体保持在同一页，避免只排下一半
    for row in table_obj.rows:
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.keep_with_next = True
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # 五、结果分析
    heading(doc, "五、结果分析")
    heading(doc, "5.1 设计模式的可测收益", 2)
    table(
        doc,
        ["指标", "基线值", "说明"],
        [
            ["报名主流程中的类型判断", "0 处", "RegistrationService 不出现 policy_type 分支"],
            ["策略实现 / 通知订阅者", "2 个 / 2 个", "新增规则或渠道通过新增类完成"],
            ["源码规模", "25 个 Python 文件，约 2.5k 行", "含 docstring 与类型注解；52 个类/枚举定义"],
            ["自动化测试", "26 条，100% 通过", "C1—C10 + 16 条补充，执行 2.77 秒"],
            ["通知渠道失败影响", "不影响报名事务", "故障注入测试：报名仍 approved，台账记录 failed"],
        ],
        widths=[4.4, 5.2, 6.8],
    )
    body(doc, "策略模式把“满员时怎么办”收敛到两个策略类中，公共校验只写一次；"
              "观察者模式让报名服务在不知道有几个渠道的情况下发布事件，渠道失败被隔离。"
              "这两个收益不是“用了模式”本身，而是体现为：报名服务没有规则分支、通知渠道可独立测试、"
              "失败可追溯且不影响已提交的业务事实。")

    heading(doc, "5.2 成本与局限", 2)
    body(doc, "代价同样明显：类数量与调用链变长，一次报名经过 Web、服务、策略、仓储、事件总线与两个"
              "订阅者，排查问题需要同时看业务表与投递台账；通知为进程内同步投递，没有重试队列；"
              "SQLite 适合单机演示，高并发需要替换数据库。模式不是免费的正确性，"
              "对小规模且规则固定的系统，if/elif 可能更划算。")

    heading(doc, "5.3 变更阶段的准备", 2)
    body(doc, "指导书要求初版验收后由教师发布变更单，学生在此之前不得提前实现变更功能。"
              "本项目当前只交付 baseline-v1：变更单未下发，因此没有实现候补队列、活动取消等任何"
              "变更功能，也没有针对变更单做代码修改。设计上保留了扩展点：新增报名方式只需新增策略，"
              "新增通知渠道只需新增订阅者；变更阶段将按教师变更单重新做影响分析、在 baseline-v1 上"
              "建分支实现并回归。")

    # 六、问题与反思
    heading(doc, "六、问题与反思")
    heading(doc, "问题 1：依赖安装失败，报错并非真正原因", 2)
    body(doc, "首次创建虚拟环境后安装 Flask，默认 PyPI 源无法解析 files.pythonhosted.org，"
              "报错停留在“找不到包”。用 pip download 观察到底层 DNS 解析失败后，改用阿里云镜像完成安装。"
              "经验：安装失败要先看网络层，再判断版本或包名。")
    heading(doc, "问题 2：模板首行被转义，页面进入怪异模式", 2)
    body(doc, "AI 生成的 base.html 把 <!doctype html> 写成了 &lt;!doctype html&gt;，"
              "浏览器缺少标准模式声明，样式与盒模型可能异常。自查模板首行后修正，并用真实浏览器截图复核。"
              "经验：AI 产出的“看起来像 HTML”不等于合法 HTML，关键结构必须人工检查。")
    heading(doc, "问题 3：页面引用了路由未传入的变量", 2)
    body(doc, "审批页模板使用 stats 展示每个活动的剩余名额，但 admin.approvals 路由最初没有传入该字典，"
              "访问时会触发模板错误。对照模板变量与路由上下文后补充统计字典，并在真实页面复核。"
              "经验：模板与路由之间没有编译期约束，必须用页面级测试或实际访问覆盖。")
    heading(doc, "反思", 2)
    body(doc, "AI 能快速生成结构完整的分层代码，但它不会自动对“事务边界、通知失败、重复报名”负责；"
              "这些判断必须由人先写进设计，再用测试固定下来。本项目的测试不是形式："
              "C3、C4、C8、通知失败与幂等用例都对应真实业务风险。后续变更阶段应重点观察"
              "“新增规则需要改多少核心代码”，用修改范围而不是模式名称评价设计。")

    # 七、部署与运行
    heading(doc, "七、部署与运行")
    body(doc, "本地运行已验证：启动 Flask 后浏览器可访问 http://127.0.0.1:5000，登录页提供固定演示账号；"
              "关闭并重启应用后，活动、报名与通知仍然存在（C10）。")
    body(doc, "仓库提供 Linux 部署配置 deploy/：gunicorn 以 2 个 worker 监听 127.0.0.1:8000，"
              "systemd 托管进程，Nginx 反向代理 80 端口并托管静态资源；部署步骤见 README 第 8 节。"
              "本次未在公网云服务器实际部署，因此不填写虚构访问地址；待服务器可用后按 README 执行并补充实地址。")
    body(doc, "演示账号：admin（管理员）、s1—s4（学生）；首次启动自动建表并写入 4 个演示活动。")

    # 附录
    heading(doc, "附录：交付与复现")
    bullet(doc, "项目目录：C:\\Users\\muke\\Desktop\\软件工程实验二CampusEvent")
    bullet(doc, "启动：.\\.venv\\Scripts\\python.exe run.py")
    bullet(doc, "测试：.\\.venv\\Scripts\\python.exe -m pytest -v")
    bullet(doc, "版本：git checkout baseline-v1")
    bullet(doc, "文档：README.md、AI_DEV_LOG.md、docs/01—06 设计文档、docs/08_回归测试表.xlsx")

    doc.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()


