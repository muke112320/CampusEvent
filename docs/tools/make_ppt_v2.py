"""生成实验二答辩 PPT（baseline-v1 + 教师变更单 change-v2，12 页）。"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches

from make_ppt import (
    ACCENT, BLUE, CARD, GRAY, GREEN, INK, LIGHT, LINE, NAVY, ORANGE,
    TEAL, WHITE, arrow, bullets, card, image_fit, notes, rect, textbox,
)

BASE = Path(__file__).resolve().parent.parent
IMG = BASE / "images"
OUT = BASE / "演示PPT.pptx"


def add_slide(prs: Presentation, title: str, subtitle: str = "", page: int = 0,
              total: int = 12):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, 13.333, 0.92, NAVY, None, shape=MSO_SHAPE.RECTANGLE)
    rect(slide, 0, 0.92, 13.333, 0.05, ACCENT, None, shape=MSO_SHAPE.RECTANGLE)
    textbox(slide, 0.55, 0.2, 11.0, 0.55, title, 26, True, WHITE)
    if subtitle:
        textbox(slide, 0.58, 1.12, 12.2, 0.4, subtitle, 12.5, False, GRAY)
    textbox(slide, 0.55, 7.12, 8.0, 0.25,
            "CampusEvent · 软件工程实验二 · baseline-v1 / change-v2", 9, False, GRAY)
    textbox(slide, 11.9, 7.12, 0.9, 0.25, f"{page}/{total}", 9, False, GRAY, PP_ALIGN.RIGHT)
    return slide


def chip(slide, left: float, top: float, width: float, text: str,
         fill: RGBColor = LIGHT, color: RGBColor = GRAY, size: float = 11) -> None:
    rect(slide, left, top, width, 0.34, fill, LINE)
    textbox(slide, left, top + 0.06, width, 0.24, text, size, True, color, PP_ALIGN.CENTER)


def build() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    total = 12

    # ---------------- 1 封面 ----------------
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, 13.333, 7.5, NAVY, None, shape=MSO_SHAPE.RECTANGLE)
    rect(slide, 0, 5.05, 13.333, 0.06, ACCENT, None, shape=MSO_SHAPE.RECTANGLE)
    textbox(slide, 0.9, 1.55, 11.6, 0.5, "《软件工程》实验二 · 课程实践", 16, False,
            RGBColor(0xB9, 0xC6, 0xE6))
    textbox(slide, 0.9, 2.1, 11.8, 1.0, "CampusEvent 校园活动报名与管理系统", 38, True, WHITE)
    textbox(slide, 0.92, 3.15, 11.4, 0.55,
            "策略模式封装报名规则 · 观察者模式解耦通知 · 按教师变更单完成二次演进",
            17, False, RGBColor(0xD7, 0xE1, 0xF5))
    chip(slide, 0.92, 4.05, 1.7, "baseline-v1", RGBColor(0x24, 0x36, 0x66), WHITE)
    chip(slide, 2.75, 4.05, 1.7, "change-v2", RGBColor(0x24, 0x36, 0x66), WHITE)
    chip(slide, 4.58, 4.05, 2.0, "41 passed", RGBColor(0x16, 0x65, 0x34), WHITE)
    chip(slide, 6.72, 4.05, 2.6, "CR-01 / CR-02", RGBColor(0x24, 0x36, 0x66), WHITE)
    textbox(slide, 0.92, 5.35, 11.0, 0.4, "柯文韬　·　2026-11-26　·　GitHub: muke112320/CampusEvent",
            13, False, RGBColor(0xB9, 0xC6, 0xE6))
    notes(slide, "开场：实验二完成两个版本，初版验收后按教师 CR-01/CR-02 做了一次真实变更。")

    # ---------------- 2 目标与范围 ----------------
    slide = add_slide(prs, "项目目标与范围", "不是堆功能，而是完成一次设计驱动开发并接受变更检验", 2, total)
    card(slide, 0.55, 1.65, 3.95, 1.85, "设计先行",
         "用例图、两版类图、五条时序图、模式决策与影响分析都先于对应实现完成", ACCENT)
    card(slide, 4.7, 1.65, 3.95, 1.85, "可验证",
         "41 条 pytest：HTTP 操作 + 数据库核对，含迁移、幂等、邮件故障注入", TEAL)
    card(slide, 8.85, 1.65, 3.95, 1.85, "可复现",
         "两个 Git 标签固定两版代码；统计口径、命令与截图均可复核", ORANGE)
    textbox(slide, 0.55, 3.85, 6.0, 0.4, "初版功能（P2-F01—F08）", 17, True, NAVY)
    bullets(slide, 0.6, 4.3, 6.0, 2.3, [
        "活动管理、浏览搜索、统计",
        "直接报名 / 管理员审核两类策略",
        "报名、审批、取消的状态流转",
        "站内消息 + 出件箱邮件双渠道通知",
    ], 14)
    textbox(slide, 6.85, 3.85, 6.0, 0.4, "教师变更（CR-01 / CR-02）", 17, True, ORANGE)
    bullets(slide, 6.9, 4.3, 5.9, 2.3, [
        "CR-01 年级限定报名：仅大二、大三，其他年级明确拒绝",
        "CR-02 模拟邮件：MockEmailSender + 邮件台账，失败留痕",
        "明确不做：真实账号体系、真实 SMTP、消息队列",
    ], 14, bullet_color=ORANGE)
    notes(slide, "范围控制是设计的一部分：拒绝范围外功能，才能让两版差异可解释。")

    # ---------------- 3 两版概览 ----------------
    slide = add_slide(prs, "两版代码与验证结果", "同一仓库、两个标签，变更只扩展策略与通知实现", 3, total)
    rect(slide, 0.55, 1.7, 6.0, 4.8, CARD, LINE)
    textbox(slide, 0.85, 1.95, 5.4, 0.45, "baseline-v1", 22, True, BLUE)
    textbox(slide, 0.85, 2.45, 5.4, 0.3, "初版验收版本", 12, False, GRAY)
    bullets(slide, 0.9, 2.95, 5.3, 3.2, [
        "两类报名策略：直接 / 审核",
        "4 类领域事件、2 个通知订阅者",
        "29 passed（C1—C10 + 16 补充 + 3 部署）",
        "25 个 Python 文件 / 2497 行 / 52 类",
    ], 14)
    rect(slide, 6.75, 1.7, 6.0, 4.8, RGBColor(0xFF, 0xF7, 0xED), RGBColor(0xFD, 0xBA, 0x74))
    textbox(slide, 7.05, 1.95, 5.4, 0.45, "change-v2", 22, True, ORANGE)
    textbox(slide, 7.05, 2.45, 5.4, 0.3, "教师变更单完成版本", 12, False, GRAY)
    bullets(slide, 7.1, 2.95, 5.3, 3.2, [
        "+ GradeLimited 策略（继承 Direct）",
        "+ Student.grade（1—4）与迁移",
        "+ MockEmailSender / email_deliveries",
        "41 passed；核心业务服务 0 修改",
    ], 14, bullet_color=ORANGE)
    notes(slide, "强调：变更不是重写，是在原结构上扩展；两版都保留测试与标签。")

    # ---------------- 4 分层架构 ----------------
    slide = add_slide(prs, "分层架构与依赖方向", "domain 不依赖框架；服务依赖抽象；装配集中在容器", 4, total)
    layers = [
        ("Web 蓝图 / 模板", "登录态、表单、页面渲染；不直接写 SQL", 1.65, ACCENT),
        ("应用服务", "报名、审批、活动；编排事务与事件发布", 2.55, TEAL),
        ("领域层", "模型 / 3 个策略 / 4 个事件；纯 Python 可单测", 3.45, ORANGE),
        ("仓储 SQLite", "对象↔行映射；被容器注入服务", 4.35, RGBColor(0x6B, 0x72, 0x80)),
    ]
    for index, (name, desc, top, color) in enumerate(layers):
        rect(slide, 0.7, top, 7.2, 0.72, CARD, LINE)
        rect(slide, 0.7, top, 0.09, 0.72, color, None, shape=MSO_SHAPE.RECTANGLE)
        textbox(slide, 0.95, top + 0.08, 2.3, 0.3, name, 15, True, NAVY)
        textbox(slide, 3.25, top + 0.1, 4.4, 0.45, desc, 11.5, False, GRAY)
        if index < len(layers) - 1:
            arrow(slide, 4.1, top + 0.76, 0.25)
    rect(slide, 8.35, 1.65, 4.4, 0.72, CARD, LINE)
    textbox(slide, 8.55, 1.73, 4.0, 0.3, "EventBus → 站内 / 邮件订阅者", 14, True, TEAL)
    textbox(slide, 8.55, 2.02, 4.0, 0.3, "事务提交后发布；失败隔离并留痕", 11, False, GRAY)
    bullets(slide, 8.4, 2.7, 4.4, 3.4, [
        "web 不直接操作 SQL",
        "domain 不导入 Flask / sqlite3",
        "服务依赖 PolicyRegistry / EventBus",
        "MockEmailSender 只依赖仓储与时钟",
        "变更未改变依赖方向",
    ], 12.5)
    notes(slide, "依赖方向没被变更破坏：新增类只依赖既有抽象。")

    # ---------------- 5 领域模型 ----------------
    slide = add_slide(prs, "领域模型：扩展年级与邮件台账", "不新增活动/报名实体；不变量保持不变", 5, total)
    image_fit(slide, IMG / "class_domain_change.png", 0.45, 1.55, 8.4, 5.3)
    bullets(slide, 9.05, 1.7, 3.8, 5.0, [
        "Student + grade（1—4）与 grade_label",
        "PolicyType + grade_limited",
        "EmailDelivery 审计实体",
        "唯一约束 (event_id, student_id)",
        "只有 approved 占名额",
        "原有直接/审核策略不变",
    ], 12.5, bullet_color=ORANGE)
    notes(slide, "橙色是变更点；没有新增活动/报名实体，说明变更被限制在状态与渠道层。")

    # ---------------- 6 策略模式 ----------------
    slide = add_slide(prs, "策略模式：年级限定只加一个判断", "模板方法固定公共规则，decide() 是唯一变化点", 6, total)
    image_fit(slide, IMG / "class_design_change.png", 0.35, 1.5, 7.4, 5.45)
    card(slide, 7.95, 1.6, 4.9, 1.55, "公共规则只写一次",
         "活动未开始、无重复有效报名，由 evaluate() 统一执行", ACCENT, 14, 11.5)
    card(slide, 7.95, 3.3, 4.9, 1.55, "复用直接报名",
         "继承 Direct，只判断 grade ∈ {2,3}，随后调用 super().decide()", TEAL, 14, 11.5)
    card(slide, 7.95, 5.0, 4.9, 1.55, "CR-01 的实测成本",
         "1 个策略类 + 注册 1 行；RegistrationService 零改动", ORANGE, 14, 11.5)
    notes(slide, "用 1 个类 + 1 行注册说明 OCP 的实际收益。")

    # ---------------- 7 观察者 / 邮件 ----------------
    slide = add_slide(prs, "观察者模式：MockEmailSender 接在渠道侧", "业务服务不感知邮件；失败只留痕", 7, total)
    boxes = [("RegistrationService", 1.5, ACCENT), ("EventBus", 4.3, TEAL),
             ("站内订阅者", 7.1, BLUE), ("邮件订阅者", 9.4, ORANGE)]
    widths = [2.2, 1.8, 2.0, 2.2]
    for (name, left, color), width in zip(boxes, widths):
        rect(slide, left, 2.05, width, 0.9, WHITE, LINE)
        rect(slide, left, 2.05, width, 0.08, color, None, shape=MSO_SHAPE.RECTANGLE)
        textbox(slide, left, 2.35, width, 0.4, name, 13, True, NAVY, PP_ALIGN.CENTER)
    arrow(slide, 3.75, 2.38, 0.5)
    arrow(slide, 6.15, 2.38, 0.9)
    arrow(slide, 9.15, 2.38, 0.2)
    rect(slide, 8.3, 3.2, 4.4, 0.75, CARD, LINE)
    textbox(slide, 8.5, 3.3, 4.0, 0.3, "MockEmailSender", 14, True, ORANGE)
    textbox(slide, 8.5, 3.58, 4.0, 0.3, "→ email_outbox + email_deliveries", 11, False, GRAY)
    arrow(slide, 10.5, 2.98, 0.25, 0.2)
    card(slide, 0.6, 4.35, 4.0, 1.55, "失败隔离", "记录 failed + error；报名已提交，不回滚", TEAL, 14, 11.5)
    card(slide, 4.75, 4.35, 4.0, 1.55, "事件级防重", "订阅者 claim + (event_id, student_id) 唯一", ACCENT, 14, 11.5)
    card(slide, 8.9, 4.35, 3.9, 1.55, "可审计", "收件人/主题/内容/状态/时间全部落库", ORANGE, 14, 11.5)
    textbox(slide, 0.6, 6.15, 12.1, 0.6,
            "边界：邮件发送是外部副作用，放在订阅者侧；业务服务只发布“已发生事实”。",
            12.5, True, NAVY)
    notes(slide, "观察者的边界：只做通知，不做业务写入。")

    # ---------------- 8 CR-01 ----------------
    slide = add_slide(prs, "CR-01：年级限定报名", "大二、大三通过；大一、大四得到明确原因且不落库", 8, total)
    image_fit(slide, IMG / "change_grade_detail.png", 0.45, 1.55, 7.1, 4.7)
    steps = [
        ("① 年级门槛", "grade ∈ {2,3} 才继续"),
        ("② 公共规则", "活动未开始、无重复报名"),
        ("③ 容量复用", "super().decide() 判定满员"),
        ("④ 拒绝提示", "“仅限大二、大三（你的年级：大一）”"),
        ("⑤ 零改主流程", "RegistrationService 未修改"),
    ]
    for index, (head, desc) in enumerate(steps):
        top = 1.62 + index * 0.92
        rect(slide, 7.85, top, 4.95, 0.78, CARD, LINE)
        textbox(slide, 8.05, top + 0.08, 1.9, 0.3, head, 13, True, ORANGE)
        textbox(slide, 9.85, top + 0.1, 2.85, 0.55, desc, 10.5, False, GRAY)
    textbox(slide, 7.85, 6.25, 4.95, 0.3, "对应测试：CR1-01—CR1-04 + 容量/重复/原策略回归",
            10.5, False, GRAY)
    notes(slide, "重点讲 ③⑤：复用容量逻辑、核心服务零改动。")

    # ---------------- 9 CR-02 ----------------
    slide = add_slide(prs, "CR-02：模拟邮件通知与台账", "站内通知继续；邮件记录状态与时间，失败不回滚", 9, total)
    image_fit(slide, IMG / "change_email_ledger.png", 0.45, 1.55, 7.1, 4.8)
    bullets(slide, 7.85, 1.7, 4.95, 3.3, [
        "报名通过 / 审核通过或拒绝 → 双渠道",
        "MockEmailSender 写 outbox 与 email_deliveries",
        "记录收件人、主题、内容、状态、时间",
        "失败：failed + error，报名仍有效",
        "重复：唯一约束拦截，不重复发送",
    ], 12.5, bullet_color=ORANGE)
    rect(slide, 7.85, 5.2, 4.95, 1.2, RGBColor(0xFF, 0xF7, 0xED), RGBColor(0xFD, 0xBA, 0x74))
    textbox(slide, 8.05, 5.33, 4.55, 0.3, "验证点（CR2-01—CR2-04）", 13, True, ORANGE)
    textbox(slide, 8.05, 5.65, 4.55, 0.6,
            "双渠道均有记录；故障注入后报名仍 approved；同一事件只发送一封",
            10.5, False, INK)
    notes(slide, "CR-02 的重点是失败边界与幂等，而不是多写一个 if。")

    # ---------------- 10 迁移与影响 ----------------
    slide = add_slide(prs, "迁移与影响：真正难的是边界", "模式降低扩散，但迁移与失败边界必须人工定义", 10, total)
    card(slide, 0.6, 1.65, 3.95, 2.1, "SQLite CHECK 无法修改",
         "重建 activities 表并复制数据；迁移整体事务化", ACCENT, 14, 11.5)
    card(slide, 4.7, 1.65, 3.95, 2.1, "既有数据没有年级",
         "加列时给合法默认值，演示账号按语义回填", TEAL, 14, 11.5)
    card(slide, 8.85, 1.65, 3.95, 2.1, "邮件重复与失败",
         "订阅者 claim + 邮件台账唯一约束；失败只留痕", ORANGE, 14, 11.5)
    textbox(slide, 0.6, 4.05, 12.1, 0.4, "变更扩散范围（git diff --numstat baseline-v1..change-v2）", 15, True, NAVY)
    rows = [
        ("新增类", "4", "策略 + 发送器 + 收据 + 邮件台账"),
        ("删除类", "3", "旧出件箱/故障网关"),
        ("核心业务服务修改", "0", "关键验证"),
        ("数据库迁移", "1 步", "grade、CHECK、email_deliveries"),
        ("源码行数", "+281", "2497 → 2778"),
        ("测试", "+12", "29 → 41，全部通过"),
    ]
    for index, (key, value, note) in enumerate(rows):
        top = 4.55 + index * 0.4
        textbox(slide, 0.65, top, 2.6, 0.3, key, 11.5, False, INK)
        textbox(slide, 3.3, top, 1.2, 0.3, value, 12, True, ORANGE)
        textbox(slide, 4.6, top, 6.0, 0.3, note, 11, False, GRAY)
    textbox(slide, 10.1, 4.55, 2.7, 2.2,
            "结论：模式把变化收敛到策略与渠道；迁移、事务与幂等仍需测试兜底。",
            12, True, NAVY)
    notes(slide, "这一页讲代价与真实缺陷，说明“用了模式”不等于正确。")

    # ---------------- 11 测试与回归 ----------------
    slide = add_slide(prs, "测试与回归：41 passed", "C1—C10 无回归；新增 12 条教师变更测试", 11, total)
    rect(slide, 0.6, 1.65, 3.2, 2.0, NAVY, None)
    textbox(slide, 0.7, 1.85, 3.0, 0.7, "41", 44, True, WHITE, PP_ALIGN.CENTER)
    textbox(slide, 0.7, 2.65, 3.0, 0.35, "passed / 0 failed / 0 skipped", 11, False,
            RGBColor(0xD7, 0xE1, 0xF5), PP_ALIGN.CENTER)
    groups = [
        ("C1—C10 核心验收", "10 / 10", "初版验收全量回归"),
        ("S01—S16 基线补充", "16 / 16", "策略、边界、权限、通知、幂等"),
        ("CR1 / CR2 变更测试", "12 / 12", "年级准入、邮件渠道、迁移"),
        ("P01—P03 部署测试", "3 / 3", "子路径登录、静态资源、重定向"),
    ]
    for index, (name, ratio, desc) in enumerate(groups):
        top = 1.65 + index * 1.15
        rect(slide, 4.1, top, 8.6, 0.98, CARD, LINE)
        textbox(slide, 4.3, top + 0.12, 3.2, 0.3, name, 14, True, NAVY)
        textbox(slide, 7.55, top + 0.1, 1.5, 0.35, ratio, 16, True, GREEN, PP_ALIGN.CENTER)
        textbox(slide, 9.2, top + 0.15, 3.3, 0.55, desc, 10.5, False, GRAY)
    textbox(slide, 0.6, 6.05, 12.1, 0.6,
            "关键用例：CR1-03/04 年级拒绝提示、CR2-03 邮件失败不回滚、CR2-04 重复事件只发一封、CR2-05 迁移保留数据。",
            11.5, True, INK)
    notes(slide, "测试数字与回归表、项目总结一致，可现场跑 pytest 复核。")

    # ---------------- 12 结论 ----------------
    slide = add_slide(prs, "结论：模式是工具，不是正确性证明", "用改动范围与测试证据评价设计", 12, total)
    card(slide, 0.6, 1.7, 3.95, 2.2, "策略模式", "新增 1 个策略类 + 1 行注册即接入年级限定", ACCENT, 15, 12)
    card(slide, 4.7, 1.7, 3.95, 2.2, "观察者模式", "替换邮件实现，业务服务 0 修改", TEAL, 15, 12)
    card(slide, 8.85, 1.7, 3.95, 2.2, "代价", "+281 行、类净 +1；迁移与幂等仍需人保证", ORANGE, 15, 12)
    bullets(slide, 0.65, 4.25, 12.1, 2.3, [
        "可测收益：用 git diff 与测试名说话，而不是模式名称",
        "人工守住：年级迁移、CHECK 重建、邮件失败边界、事件级幂等",
        "遗留局限：通知同步无重试；固定演示账号；SQLite 单机",
        "下一步：通知重试与退避、CSRF、并发压测、数据库替换",
    ], 14, bold_prefix=True)
    textbox(slide, 0.65, 6.55, 12.1, 0.4,
            "仓库：github.com/muke112320/CampusEvent　|　在线：120.76.59.189/campusevent/",
            11, False, GRAY)
    notes(slide, "收尾：设计模式的价值要用改动范围和测试来证明。")

    prs.save(OUT)
    print("saved", OUT, "slides:", len(prs.slides))


if __name__ == "__main__":
    build()
