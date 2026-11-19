"""生成实验二（baseline-v1）答辩 PPT。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parent.parent
IMG = BASE / "images"
OUT = BASE / "演示PPT.pptx"

NAVY = RGBColor(0x14, 0x22, 0x4A)
BLUE = RGBColor(0x1E, 0x3A, 0x8A)
ACCENT = RGBColor(0x25, 0x63, 0xEB)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
ORANGE = RGBColor(0xC2, 0x41, 0x0C)
INK = RGBColor(0x17, 0x20, 0x33)
GRAY = RGBColor(0x5B, 0x67, 0x79)
LIGHT = RGBColor(0xF3, 0xF5, 0xFA)
CARD = RGBColor(0xF8, 0xFA, 0xFC)
LINE = RGBColor(0xE3, 0xE8, 0xF2)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x16, 0x65, 0x34)

FONT = "微软雅黑"


def set_font(run, size: float = 16, bold: bool = False, color: RGBColor = INK,
             font: str = FONT) -> None:
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    r_pr = run._r.get_or_add_rPr()
    ea = r_pr.find(qn("a:ea"))
    if ea is None:
        ea = r_pr.makeelement(qn("a:ea"), {})
        r_pr.append(ea)
    ea.set("typeface", font)


def textbox(slide, left: float, top: float, width: float, height: float,
            text: str, size: float = 16, bold: bool = False, color: RGBColor = INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing: float = 1.1):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    paragraph.line_spacing = spacing
    run = paragraph.add_run()
    run.text = text
    set_font(run, size, bold, color)
    return box


def bullets(slide, left: float, top: float, width: float, height: float,
            items: list[str], size: float = 15, color: RGBColor = INK,
            spacing: float = 8, bullet_color: RGBColor = ACCENT, bold_prefix: bool = False):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(spacing)
        paragraph.line_spacing = 1.15
        marker = paragraph.add_run()
        marker.text = "●  "
        set_font(marker, size - 2, True, bullet_color)
        if "：" in item and bold_prefix:
            prefix, rest = item.split("：", 1)
            head = paragraph.add_run()
            head.text = prefix + "："
            set_font(head, size, True, INK)
            tail = paragraph.add_run()
            tail.text = rest
            set_font(tail, size, False, color)
        else:
            run = paragraph.add_run()
            run.text = item
            set_font(run, size, False, color)
    return box


def rect(slide, left: float, top: float, width: float, height: float,
         fill: RGBColor, line: RGBColor | None = None, radius: bool = True,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    shape_obj = slide.shapes.add_shape(
        shape if radius else MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height),
    )
    shape_obj.fill.solid()
    shape_obj.fill.fore_color.rgb = fill
    if line is None:
        shape_obj.line.fill.background()
    else:
        shape_obj.line.color.rgb = line
        shape_obj.line.width = Pt(1)
    shape_obj.shadow.inherit = False
    return shape_obj


def card(slide, left: float, top: float, width: float, height: float,
         title: str, body: str, accent: RGBColor = ACCENT, title_size: float = 16,
         body_size: float = 12.5):
    rect(slide, left, top, width, height, CARD, LINE)
    rect(slide, left, top, 0.08, height, accent, None, shape=MSO_SHAPE.RECTANGLE)
    textbox(slide, left + 0.25, top + 0.18, width - 0.45, 0.4, title, title_size, True, NAVY)
    textbox(slide, left + 0.25, top + 0.65, width - 0.45, height - 0.8, body,
            body_size, False, GRAY, spacing=1.15)


def add_slide(prs: Presentation, title: str, subtitle: str = "", page: int = 0,
              total: int = 0) -> object:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, 13.333, 0.92, NAVY, None, shape=MSO_SHAPE.RECTANGLE)
    rect(slide, 0, 0.92, 13.333, 0.05, ACCENT, None, shape=MSO_SHAPE.RECTANGLE)
    textbox(slide, 0.55, 0.2, 10.5, 0.55, title, 26, True, WHITE)
    if subtitle:
        textbox(slide, 0.58, 1.12, 12.2, 0.4, subtitle, 12.5, False, GRAY)
    textbox(slide, 0.55, 7.12, 7.5, 0.25,
            "CampusEvent · 软件工程实验二 · baseline-v1", 9, False, GRAY)
    textbox(slide, 11.9, 7.12, 0.9, 0.25, f"{page}/{total}", 9, False, GRAY, PP_ALIGN.RIGHT)
    return slide


def image_fit(slide, path: Path, left: float, top: float, max_w: float, max_h: float,
              border: bool = True):
    with Image.open(path) as image:
        width, height = image.size
    ratio = min(max_w / width, max_h / height)
    draw_w, draw_h = width * ratio, height * ratio
    x = left + (max_w - draw_w) / 2
    y = top + (max_h - draw_h) / 2
    if border:
        rect(slide, x - 0.03, y - 0.03, draw_w + 0.06, draw_h + 0.06, WHITE, LINE)
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(draw_w), Inches(draw_h))


def arrow(slide, left: float, top: float, width: float, height: float = 0.25,
          color: RGBColor = ACCENT) -> None:
    shape_obj = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(left), Inches(top),
                                       Inches(width), Inches(height))
    shape_obj.fill.solid()
    shape_obj.fill.fore_color.rgb = color
    shape_obj.line.fill.background()


def notes(slide, text: str) -> None:
    slide.notes_slide.notes_text_frame.text = text


def build() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    total = 13

    # 1 封面
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, 13.333, 7.5, NAVY, None, shape=MSO_SHAPE.RECTANGLE)
    rect(slide, 0, 0, 0.18, 7.5, ACCENT, None, shape=MSO_SHAPE.RECTANGLE)
    rect(slide, 7.2, 0, 6.133, 7.5, RGBColor(0x1B, 0x2E, 0x5E), None, shape=MSO_SHAPE.RECTANGLE)
    textbox(slide, 0.9, 1.45, 6.0, 0.4, "《软件工程》课程实践 · 实验二", 15, False,
            RGBColor(0xBF, 0xD2, 0xF0))
    textbox(slide, 0.9, 2.0, 6.2, 1.6, "校园活动\n报名与管理系统", 40, True, WHITE)
    textbox(slide, 0.9, 3.95, 6.0, 0.5, "CampusEvent", 22, True, RGBColor(0x93, 0xC5, 0xFD))
    textbox(slide, 0.9, 4.5, 6.0, 0.35, "设计模式 · 策略 / 观察者 · 初始验收版本", 13, False,
            RGBColor(0xCB, 0xD5, 0xE1))
    rect(slide, 0.9, 5.2, 4.6, 0.04, RGBColor(0xF5, 0x9E, 0x0B), None, shape=MSO_SHAPE.RECTANGLE)
    textbox(slide, 0.9, 5.5, 5.5, 0.35, "姓名：柯文韬　　2026-11-19", 14, False, WHITE)
    textbox(slide, 0.9, 5.92, 5.5, 0.35, "版本标签：baseline-v1", 12, False,
            RGBColor(0xBF, 0xD2, 0xF0))
    textbox(slide, 7.7, 2.5, 4.9, 0.4, "本项目的三个关键词", 14, True, RGBColor(0x93, 0xC5, 0xFD))
    bullets(slide, 7.7, 3.05, 4.9, 2.8, [
        "职责先行：先画类图与时序图，再让 AI 编码",
        "模式落地：策略封装报名规则，观察者解耦通知",
        "证据验收：C1—C10 自动化测试 + 真实页面截图",
    ], size=14, color=WHITE, bullet_color=RGBColor(0xF5, 0x9E, 0x0B))
    notes(slide, "开场：这是实验二的初始验收版本，重点是设计与可验证性，而不是功能数量。")

    # 2 范围
    slide = add_slide(prs, "一、项目范围：两个角色，八项功能", "只做需求内的事，避免项目膨胀", 2, total)
    card(slide, 0.55, 1.75, 3.9, 2.25, "学生 Student",
         "浏览 / 搜索活动 · 查看详情\n报名 / 取消报名 · 查看我的报名\n接收站内消息", ACCENT)
    card(slide, 4.72, 1.75, 3.9, 2.25, "管理员 Admin",
         "创建 / 编辑 / 删除活动\n审批报名 · 查看统计\n查看通知投递台账", TEAL)
    card(slide, 8.89, 1.75, 3.9, 2.25, "报名规则",
         "直接报名：名额充足即通过\n审核报名：先待审核，再批准\n名额只统计“已通过”", ORANGE)
    rect(slide, 0.55, 4.35, 12.24, 0.55, CARD, LINE)
    textbox(slide, 0.8, 4.45, 11.8, 0.35,
            "明确不做：用户注册 / 密码体系 / 真实邮件短信 / 消息队列 / 移动端 App", 13, False, GRAY)
    textbox(slide, 0.55, 5.2, 12.2, 0.4, "验收依据", 15, True, NAVY)
    bullets(slide, 0.55, 5.65, 12.2, 1.3, [
        "指导书 3.5 节 C1—C10：创建、报名、重复报名、满员、审核、批准、拒绝、超员、取消、持久化",
        "补充 16 条：策略边界、权限、通知双渠道、通知失败留痕、同一事件幂等",
    ], size=13.5)
    notes(slide, "范围控制是实验要求的一部分：范围外功能不因“看起来完整”而加入。")

    # 3 流程
    slide = add_slide(prs, "二、核心业务流程", "从活动发布到结果通知的闭环", 3, total)
    steps = [
        ("管理员\n发布活动", "设置容量与\n报名方式"),
        ("学生\n浏览报名", "校验活动时间 /\n重复报名"),
        ("策略\n判定", "直接通过 /\n待审核"),
        ("管理员\n审批", "批准前再次\n检查名额"),
        ("结果通知", "站内消息 +\n模拟邮件"),
    ]
    x = 0.45
    for index, (title, body) in enumerate(steps):
        rect(slide, x, 2.1, 1.95, 1.45, CARD, LINE)
        textbox(slide, x + 0.12, 2.25, 1.7, 0.6, title, 14, True, NAVY, PP_ALIGN.CENTER)
        textbox(slide, x + 0.1, 2.95, 1.75, 0.5, body, 10.5, False, GRAY, PP_ALIGN.CENTER)
        if index < len(steps) - 1:
            arrow(slide, x + 2.0, 2.7, 0.38)
        x += 2.42
    rect(slide, 0.55, 4.15, 12.24, 1.15, RGBColor(0xEF, 0xF6, 0xFF), RGBColor(0xBF, 0xDB, 0xFE))
    textbox(slide, 0.8, 4.3, 11.8, 0.85,
            "状态机：待审核 → 已通过 / 已拒绝；已通过 → 已取消；已拒绝/已取消保留历史，可再次报名。\n"
            "关键约束：同一学生同一活动只能有一条“待审核/已通过”的有效报名。", 13, False, BLUE)
    bullets(slide, 0.55, 5.6, 12.2, 1.3, [
        "报名事务提交后才发送通知：通知失败不回滚报名，失败原因写入投递台账",
        "批准时在写事务内再次统计已通过人数，避免并发超员",
    ], size=13.5)
    notes(slide, "强调状态机与两个关键约束，后面测试用例会逐条对应。")

    # 4 架构
    slide = add_slide(prs, "三、系统结构：分层与依赖方向", "领域层不依赖 Flask / SQLite，业务规则可单测", 4, total)
    layers = [
        ("Web 层", "Flask 蓝图 · Jinja2 模板 · 登录态", ACCENT, 0.5),
        ("应用服务", "RegistrationService · ApprovalService · ActivityService", TEAL, 1.35),
        ("领域层", "Activity / Registration / RegistrationPolicy / 领域事件", ORANGE, 2.2),
        ("仓储层", "ActivityRepository · RegistrationRepository · MessageRepository", BLUE, 3.05),
        ("SQLite", "students · activities · registrations · messages · 通知台账", NAVY, 3.9),
    ]
    rect(slide, 0.55, 1.7, 7.5, 4.9, CARD, LINE)
    for name, detail, color, top in layers:
        rect(slide, 0.85, top, 6.9, 0.68, WHITE, LINE)
        rect(slide, 0.85, top, 0.09, 0.68, color, None, shape=MSO_SHAPE.RECTANGLE)
        textbox(slide, 1.05, top + 0.08, 1.5, 0.3, name, 13, True, NAVY)
        textbox(slide, 2.45, top + 0.11, 5.1, 0.32, detail, 9.5, False, GRAY)
        if top < 3.9:
            shape_obj = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(4.1), Inches(top + 0.7),
                                               Inches(0.22), Inches(0.13))
            shape_obj.fill.solid()
            shape_obj.fill.fore_color.rgb = RGBColor(0x94, 0xA3, 0xB8)
            shape_obj.line.fill.background()
    card(slide, 8.35, 1.7, 4.45, 1.5, "技术栈",
         "Python 3.12 · Flask 3.1 · SQLite · pytest 9\n原生 CSS，无前端框架依赖", ACCENT)
    card(slide, 8.35, 3.4, 4.45, 1.5, "依赖注入",
         "container.py 统一装配；测试可替换邮件网关为故障注入实现", TEAL)
    card(slide, 8.35, 5.1, 4.45, 1.5, "可观测性",
         "通知台账记录渠道 / 状态 / 错误；报名失败有明确中文提示", ORANGE)
    notes(slide, "依赖方向是设计重点：Web 只依赖服务，服务依赖抽象，领域层纯 Python。")

    # 5 领域模型
    slide = add_slide(prs, "四、领域模型", "实体、状态与统计口径", 5, total)
    image_fit(slide, IMG / "class_domain_baseline.png", 0.35, 1.55, 8.55, 5.2)
    bullets(slide, 8.95, 1.75, 3.95, 4.9, [
        "Activity 与 Registration：一对多组合，活动删除受报名保护",
        "Student 与 Registration：一对多关联，同一活动最多一条有效报名",
        "名额口径：只统计已通过，待审核不占名额",
        "RegistrationStats 是派生值，不落库，避免统计过期",
        "Message 通过 ID 弱关联，作为历史快照不随活动修改",
    ], size=12.5, spacing=10)
    notes(slide, "这张图回答“有哪些业务概念、关系如何”，设计类图回答“职责怎么分”。")

    # 6 策略
    slide = add_slide(prs, "五、设计模式（一）：策略模式", "把“满员后怎么办”收敛到策略类", 6, total)
    rect(slide, 3.0, 1.75, 7.3, 1.25, CARD, LINE)
    textbox(slide, 3.2, 1.85, 6.9, 0.35, "«interface» RegistrationPolicy", 15, True, NAVY,
            PP_ALIGN.CENTER)
    textbox(slide, 3.2, 2.25, 6.9, 0.55, "evaluate(ctx)：公共规则 → decide(ctx)      decide(ctx) 为抽象方法",
            11.5, False, GRAY, PP_ALIGN.CENTER)
    rect(slide, 1.2, 3.55, 4.0, 1.05, CARD, LINE)
    textbox(slide, 1.35, 3.68, 3.7, 0.3, "DirectRegistrationPolicy", 13, True, NAVY, PP_ALIGN.CENTER)
    textbox(slide, 1.35, 4.05, 3.7, 0.3, "名额充足 → 已通过；满员 → 拒绝", 11, False, GRAY, PP_ALIGN.CENTER)
    rect(slide, 8.1, 3.55, 4.0, 1.05, CARD, LINE)
    textbox(slide, 8.25, 3.68, 3.7, 0.3, "ReviewRegistrationPolicy", 13, True, NAVY, PP_ALIGN.CENTER)
    textbox(slide, 8.25, 4.05, 3.7, 0.3, "一律 → 待审核；批准时再查名额", 11, False, GRAY, PP_ALIGN.CENTER)
    for child_x in (3.2, 10.1):
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(child_x), Inches(3.0), Inches(child_x), Inches(3.5)
        )
        connector.line.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
        connector.line.width = Pt(1.5)
    textbox(slide, 5.55, 3.15, 2.3, 0.35, "继承", 10, False, GRAY, PP_ALIGN.CENTER)
    bullets(slide, 1.2, 5.05, 6.2, 1.8, [
        "公共规则：活动未开始、无重复有效报名 — 只写一次",
        "变化点：满员行为与落地状态 — 由策略决定",
        "服务中 0 处 policy_type 分支，新增规则只需注册策略",
    ], size=12, spacing=7)
    rect(slide, 7.8, 5.05, 4.4, 1.55, RGBColor(0xFF, 0xF7, 0xED), RGBColor(0xFD, 0xBA, 0x74))
    textbox(slide, 8.0, 5.18, 4.0, 1.3,
            "名额检查拆成两半：\n额度口径公共（只算已通过）；\n满员行为归策略（拒绝 / 待审核）。",
            11.5, False, ORANGE)
    notes(slide, "这是本实验的核心设计决策：公共规则不能重复实现，但满员行为不能写死。")

    # 7 观察者
    slide = add_slide(prs, "六、设计模式（二）：观察者 / 事件", "报名事务与通知渠道解耦", 7, total)
    rect(slide, 0.8, 2.6, 2.5, 1.0, CARD, LINE)
    textbox(slide, 0.95, 2.73, 2.2, 0.3, "RegistrationService", 12.5, True, NAVY, PP_ALIGN.CENTER)
    textbox(slide, 0.95, 3.1, 2.2, 0.3, "事务提交后 publish", 10.5, False, GRAY, PP_ALIGN.CENTER)
    arrow(slide, 3.35, 2.98, 0.55)
    rect(slide, 3.95, 2.5, 2.2, 1.4, RGBColor(0xEF, 0xF6, 0xFF), RGBColor(0xBF, 0xDB, 0xFE))
    textbox(slide, 4.05, 2.75, 2.0, 0.3, "EventBus", 13, True, BLUE, PP_ALIGN.CENTER)
    textbox(slide, 4.05, 3.15, 2.0, 0.3, "按订阅者分发", 10.5, False, GRAY, PP_ALIGN.CENTER)
    for index, (name, detail, color) in enumerate([
        ("InSiteSubscriber", "写入 messages 表", TEAL),
        ("EmailSubscriber", "写入 email_outbox", ORANGE),
    ]):
        top = 1.85 + index * 1.6
        arrow(slide, 6.2, 2.55 if index == 0 else 3.6, 0.5)
        rect(slide, 6.75, top, 2.65, 0.85, CARD, LINE)
        textbox(slide, 6.9, top + 0.1, 2.35, 0.3, name, 12, True, NAVY)
        textbox(slide, 6.9, top + 0.42, 2.35, 0.3, detail, 10.5, False, GRAY)
    bullets(slide, 0.8, 4.5, 6.0, 2.0, [
        "订阅者异常被隔离：邮件失败不影响站内消息与报名",
        "投递台账 (event_id, subscriber, student_id) 唯一，防重复",
        "新增渠道 = 新增订阅者 + 装配一行，服务不改",
    ], size=11.5, spacing=6)
    rect(slide, 7.3, 4.75, 5.2, 1.35, RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0xA7, 0xF3, 0xD0))
    textbox(slide, 7.5, 4.88, 4.8, 1.1,
            "故障注入实测：邮件 SMTP 失败时，报名仍为 approved；\n"
            "站内消息照常送达；台账记录 failed 与错误原因。", 11, False, GREEN)
    notes(slide, "观察者的收益要能说清楚：新增渠道不改核心服务，失败不影响业务事实。")

    # 8 时序
    slide = add_slide(prs, "七、关键时序：直接报名", "公共规则与策略判定在事务内，通知在提交后", 8, total)
    image_fit(slide, IMG / "seq_direct_registration.png", 0.3, 1.5, 9.1, 5.3)
    bullets(slide, 9.55, 1.75, 3.45, 4.9, [
        "1 读取活动与有效报名",
        "2 策略注册表选择实现",
        "3 evaluate：公共规则",
        "4 decide：名额判定",
        "5 事务内 INSERT",
        "6 commit",
        "7 publish 事件",
        "8 两个渠道各自投递",
    ], size=11.5, spacing=6)
    notes(slide, "这条时序覆盖 C2、C3、C4；审批时序在实验报告与 docs/04 中。")

    # 9 界面 1
    slide = add_slide(prs, "八、界面演示：学生端", "真实运行截图，非设计稿", 9, total)
    image_fit(slide, IMG / "activities.png", 0.45, 1.55, 6.15, 4.95)
    image_fit(slide, IMG / "activity_detail.png", 6.8, 1.55, 6.05, 4.95)
    textbox(slide, 0.45, 6.6, 6.15, 0.3, "活动广场：类型、报名方式、名额与“我的状态”", 10.5, False, GRAY, PP_ALIGN.CENTER)
    textbox(slide, 6.8, 6.6, 6.05, 0.3, "活动详情：报名统计、策略说明与操作入口", 10.5, False, GRAY, PP_ALIGN.CENTER)
    notes(slide, "截图来自真实运行实例；报名状态、名额、通知都可现场复现。")

    # 10 界面 2
    slide = add_slide(prs, "八、界面演示：管理端", "审批、统计与通知可追溯", 10, total)
    image_fit(slide, IMG / "admin_approvals.png", 0.45, 1.55, 6.15, 4.95)
    image_fit(slide, IMG / "admin_notifications.png", 6.8, 1.55, 6.05, 4.95)
    textbox(slide, 0.45, 6.6, 6.15, 0.3, "审批台：按活动筛选，实时显示剩余名额", 10.5, False, GRAY, PP_ALIGN.CENTER)
    textbox(slide, 6.8, 6.6, 6.05, 0.3, "通知台账：双渠道投递结果与失败原因", 10.5, False, GRAY, PP_ALIGN.CENTER)
    notes(slide, "审批页的“剩余名额”与通知台账是现场答辩的可验证点。")

    # 11 测试
    slide = add_slide(prs, "九、测试与验收", "26 条自动化测试全部通过", 11, total)
    rect(slide, 0.55, 1.65, 3.3, 2.2, RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0xA7, 0xF3, 0xD0))
    textbox(slide, 0.75, 1.8, 2.9, 0.9, "26", 48, True, GREEN, PP_ALIGN.CENTER)
    textbox(slide, 0.75, 2.75, 2.9, 0.35, "全部通过", 13, False, GREEN, PP_ALIGN.CENTER)
    textbox(slide, 0.75, 3.15, 2.9, 0.35, "C1—C10 + 16 条补充", 11, False, GRAY, PP_ALIGN.CENTER)
    rect(slide, 4.15, 1.65, 8.65, 2.2, CARD, LINE)
    textbox(slide, 4.4, 1.78, 8.2, 0.3, "覆盖的风险点", 13, True, NAVY)
    bullets(slide, 4.4, 2.15, 8.2, 1.6, [
        "重复报名、直接报名满员、审批满员（C3 / C4 / C8）",
        "审核批准 / 拒绝与通知；取消释放名额（C6 / C7 / C9）",
        "通知失败不回滚、重复事件不重复通知；重启后数据仍在（C10）",
    ], size=11, spacing=4)
    rows = [
        ("验收项", "结果", "证据"),
        ("C1—C10 核心验收", "10 / 10", "tests/test_acceptance.py"),
        ("策略与边界补充", "13 / 13", "tests/test_rules.py"),
        ("通知与幂等", "3 / 3", "tests/test_notifications.py"),
    ]
    table = slide.shapes.add_table(len(rows), 3, Inches(0.55), Inches(4.25), Inches(12.25), Inches(2.0)).table
    widths = [4.6, 2.4, 5.25]
    for index, width in enumerate(widths):
        table.columns[index].width = Inches(width)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = value
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    set_font(run, 11.5, r == 0, WHITE if r == 0 else INK)
            cell.fill.solid()
            cell.fill.fore_color.rgb = BLUE if r == 0 else (CARD if r % 2 else WHITE)
            cell.margin_left = Inches(0.12)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
    notes(slide, "测试不是形式：每条都对应一个业务风险，且能一条命令复现。")

    # 12 取舍
    slide = add_slide(prs, "十、设计取舍：收益与成本", "用指标说明，而不是“用了模式”", 12, total)
    card(slide, 0.55, 1.7, 6.0, 2.55, "收益",
         "报名主流程 0 处类型判断\n新增规则 / 渠道 = 新增类\n通知失败不影响报名，且可追溯\n策略与订阅者可独立单测",
         TEAL)
    card(slide, 6.8, 1.7, 6.0, 2.55, "成本与局限",
         "25 个 Python 文件、约 2.5k 行\n一次报名跨 6 个协作对象，调试链更长\n通知同步投递，无重试队列\n小规模固定规则下可能过度设计",
         ORANGE)
    rect(slide, 0.55, 4.5, 12.25, 1.85, CARD, LINE)
    textbox(slide, 0.8, 4.62, 11.8, 0.3, "可测指标（baseline-v1）", 13, True, NAVY)
    metrics = [
        ("策略实现", "2 个"), ("通知订阅者", "2 个"), ("主流程类型分支", "0 处"),
        ("自动化测试", "26 条 100%"), ("源码规模", "≈2.5k 行"),
    ]
    for index, (label, value) in enumerate(metrics):
        x = 0.8 + index * 2.35
        textbox(slide, x, 5.05, 2.1, 0.55, value, 20, True, ACCENT)
        textbox(slide, x, 5.65, 2.1, 0.3, label, 10.5, False, GRAY)
    notes(slide, "成本要如实讲：模式增加了类和调用链，不是免费的正确性。")

    # 13 下一步
    slide = add_slide(prs, "十一、下一步：等待变更单，再做变更", "不在教师发布变更请求前提前实现", 13, total)
    steps = [
        ("已完成", "需求分析\n设计评审\nbaseline-v1", GREEN),
        ("等待", "教师发布\n变更单 CR", ORANGE),
        ("变更", "影响分析\n分支实现\n回归测试", ACCENT),
        ("交付", "标签 change-v2\n可维护性对照\n项目总结", TEAL),
    ]
    x = 0.6
    for index, (head, body, color) in enumerate(steps):
        rect(slide, x, 2.0, 2.85, 1.9, CARD, LINE)
        rect(slide, x, 2.0, 2.85, 0.08, color, None, shape=MSO_SHAPE.RECTANGLE)
        textbox(slide, x + 0.2, 2.2, 2.45, 0.3, head, 13, True, color)
        textbox(slide, x + 0.2, 2.65, 2.45, 1.0, body, 12, False, INK)
        if index < len(steps) - 1:
            arrow(slide, x + 2.92, 2.85, 0.4, color=RGBColor(0x94, 0xA3, 0xB8))
        x += 3.2
    bullets(slide, 0.6, 4.35, 12.2, 2.0, [
        "当前只交付 baseline-v1：没有实现候补队列、活动取消等任何变更功能",
        "扩展点已保留：新增报名规则 = 新增策略；新增通知渠道 = 新增订阅者",
        "拿到变更单后：先写影响分析，再在 baseline-v1 上建分支实现，最后跑全量回归",
    ], size=13, spacing=8)
    textbox(slide, 0.6, 6.35, 12.2, 0.4, "谢谢，请老师批评指正。", 15, True, NAVY)
    notes(slide, "明确说明没有提前实现变更，符合指导书的流程要求。")

    prs.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()

