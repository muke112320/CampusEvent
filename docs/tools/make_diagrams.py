"""生成实验二所需的 UML 图（用例图、类图、时序图）。

使用 Pillow 直接绘制，输出高分辨率 PNG，可嵌入 Word/PPT。
运行：python docs/tools/make_diagrams.py（需要 Pillow）
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = 2  # 超采样倍数
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
OUT = Path(__file__).resolve().parent.parent / "images"

INK = "#1b2437"
MUTED = "#5b6779"
LINE = "#64748b"
HEADER = "#eef2ff"
HEADER_CHANGE = "#fff1e6"
FILL = "#ffffff"
GREEN = "#0f766e"
CHANGE = "#c2410c"


def font(size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, int(size * S))


class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.image = Image.new("RGB", (width * S, height * S), "#ffffff")
        self.draw = ImageDraw.Draw(self.image)
        self._fonts: dict[tuple[float, bool], ImageFont.FreeTypeFont] = {}

    def f(self, size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = font(size, bold)
        return self._fonts[key]

    def text(self, x: float, y: float, value: str, size: float = 12, bold: bool = False,
             fill: str = INK, anchor: str = "lt") -> None:
        self.draw.text((x * S, y * S), value, font=self.f(size, bold), fill=fill, anchor=anchor)

    def text_width(self, value: str, size: float, bold: bool = False) -> float:
        return self.draw.textlength(value, font=self.f(size, bold)) / S

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str = LINE,
             width: float = 1.3, dash: bool = False) -> None:
        if dash:
            length = math.hypot(x2 - x1, y2 - y1)
            if length == 0:
                return
            ux, uy = (x2 - x1) / length, (y2 - y1) / length
            pos = 0.0
            while pos < length:
                end = min(pos + 4, length)
                self.draw.line(
                    [((x1 + ux * pos) * S, (y1 + uy * pos) * S),
                     ((x1 + ux * end) * S, (y1 + uy * end) * S)],
                    fill=color, width=max(1, int(width * S)))
                pos += 7
        else:
            self.draw.line([(x1 * S, y1 * S), (x2 * S, y2 * S)], fill=color,
                           width=max(1, int(width * S)))

    def rect(self, x: float, y: float, w: float, h: float, fill: str | None = None,
             outline: str | None = LINE, width: float = 1.2, radius: float = 0) -> None:
        box = [x * S, y * S, (x + w) * S, (y + h) * S]
        if radius:
            self.draw.rounded_rectangle(box, radius=radius * S, fill=fill, outline=outline,
                                        width=max(1, int(width * S)))
        else:
            self.draw.rectangle(box, fill=fill, outline=outline, width=max(1, int(width * S)))

    def ellipse(self, x: float, y: float, w: float, h: float, fill: str = "#f8fafc",
                outline: str = LINE, width: float = 1.2) -> None:
        self.draw.ellipse([x * S, y * S, (x + w) * S, (y + h) * S], fill=fill,
                          outline=outline, width=max(1, int(width * S)))

    def wrap(self, value: str, size: float, max_width: float, bold: bool = False) -> list[str]:
        lines: list[str] = []
        current = ""
        for char in value:
            if char == "\n":
                lines.append(current)
                current = ""
                continue
            if self.text_width(current + char, size, bold) <= max_width:
                current += char
            else:
                lines.append(current)
                current = char
        if current:
            lines.append(current)
        return lines

    def save(self, name: str) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        self.image.save(OUT / name, "PNG")
        print("saved", OUT / name)


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    def anchor(self, side: str, frac: float = 0.5) -> tuple[float, float]:
        if side == "top":
            return (self.x + self.w * frac, self.y)
        if side == "bottom":
            return (self.x + self.w * frac, self.y + self.h)
        if side == "left":
            return (self.x, self.y + self.h * frac)
        return (self.x + self.w, self.y + self.h * frac)


def class_box(canvas: Canvas, x: float, y: float, w: float, title: str,
              attrs: tuple[str, ...] = (), methods: tuple[str, ...] = (),
              stereotype: str | None = None, fill: str = FILL, header: str = HEADER,
              title_color: str = INK) -> Box:
    head_h = 30 + (16 if stereotype else 0)
    attr_h = (10 + 17 * len(attrs)) if attrs else 8
    method_h = (10 + 17 * len(methods)) if methods else 8
    h = head_h + attr_h + method_h
    canvas.rect(x, y, w, h, fill=fill, outline="#94a3b8", width=1.3, radius=6)
    canvas.rect(x, y, w, head_h, fill=header, outline=None, radius=6)
    canvas.line(x, y + head_h, x + w, y + head_h, color="#94a3b8", width=1.2)
    if stereotype:
        canvas.text(x + w / 2, y + 7, stereotype, 10, False, MUTED, anchor="mt")
        canvas.text(x + w / 2, y + 22, title, 15, True, title_color, anchor="mt")
    else:
        canvas.text(x + w / 2, y + 9, title, 15, True, title_color, anchor="mt")

    cursor = y + head_h + 6
    for attr in attrs:
        canvas.text(x + 10, cursor, attr, 10.5, False, INK)
        cursor += 17
    if attrs:
        canvas.line(x, y + head_h + attr_h - 2, x + w, y + head_h + attr_h - 2,
                    color="#cbd5e1", width=0.9)
    cursor = y + head_h + attr_h + 4
    for method in methods:
        canvas.text(x + 10, cursor, method, 10.5, False, INK)
        cursor += 17
    return Box(x, y, w, h)


def arrow_head(canvas: Canvas, tip: tuple[float, float], direction: tuple[float, float],
               kind: str, color: str) -> None:
    x, y = tip
    ux, uy = direction
    nx, ny = -uy, ux
    if kind == "open":
        size = 9
        canvas.line(x, y, x - ux * size + nx * 4.5, y - uy * size + ny * 4.5, color, 1.4)
        canvas.line(x, y, x - ux * size - nx * 4.5, y - uy * size - ny * 4.5, color, 1.4)
    elif kind in ("filled", "hollow"):
        size = 12
        points = [
            (x * S, y * S),
            ((x - ux * size + nx * 6) * S, (y - uy * size + ny * 6) * S),
            ((x - ux * size - nx * 6) * S, (y - uy * size - ny * 6) * S),
        ]
        canvas.draw.polygon(points, fill=color if kind == "filled" else "#ffffff",
                            outline=color, width=max(1, int(1.3 * S)))
    elif kind == "diamond":
        size = 16
        points = [
            (x * S, y * S),
            ((x - ux * size / 2 + nx * 5) * S, (y - uy * size / 2 + ny * 5) * S),
            ((x - ux * size) * S, (y - uy * size) * S),
            ((x - ux * size / 2 - nx * 5) * S, (y - uy * size / 2 - ny * 5) * S),
        ]
        canvas.draw.polygon(points, fill=color, outline=color)


def label(canvas: Canvas, x: float, y: float, text: str, color: str = LINE,
          size: float = 10, center: bool = True) -> None:
    w = canvas.text_width(text, size) + 8
    left = x - w / 2 if center else x
    canvas.rect(left, y - 9, w, 17, fill="#ffffff", outline=None)
    canvas.text(left + 4, y - 8, text, size, False, color)


def relation(canvas: Canvas, start: tuple[float, float], end: tuple[float, float],
             head: str = "open", dashed: bool = False, color: str = LINE,
             label_text: str | None = None, label_dx: float = 0,
             label_dy: float = -16) -> None:
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    trim = 12 if head in ("filled", "hollow") else 0
    canvas.line(x1, y1, x2 - ux * trim, y2 - uy * trim, color, 1.3, dash=dashed)
    if head:
        arrow_head(canvas, (x2, y2), (ux, uy), head, color)
    if label_text:
        label(canvas, (x1 + x2) / 2 + label_dx, (y1 + y2) / 2 + label_dy, label_text, color)


def polyline(canvas: Canvas, points: list[tuple[float, float]], head: str = "open",
             dashed: bool = False, color: str = LINE, label_text: str | None = None,
             label_segment: int = 0, label_t: float = 0.5,
             label_dx: float = 0, label_dy: float = -14) -> None:
    for i in range(len(points) - 1):
        canvas.line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
                    color, 1.3, dash=dashed)
    (x1, y1), (x2, y2) = points[-2], points[-1]
    length = math.hypot(x2 - x1, y2 - y1)
    if head and length:
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        arrow_head(canvas, (x2, y2), (ux, uy), head, color)
    if label_text:
        (ax, ay), (bx, by) = points[label_segment], points[label_segment + 1]
        lx = ax + (bx - ax) * label_t + label_dx
        ly = ay + (by - ay) * label_t + label_dy
        label(canvas, lx, ly, label_text, color)


def title(canvas: Canvas, text: str, subtitle: str = "") -> None:
    canvas.text(40, 24, text, 22, True, INK)
    if subtitle:
        canvas.text(40, 54, subtitle, 11.5, False, MUTED)


def group_label(canvas: Canvas, x: float, y: float, text: str, color: str = MUTED) -> None:
    canvas.text(x, y, text, 11, True, color)


# ---------------------------------------------------------------------------
# 领域模型类图
# ---------------------------------------------------------------------------
def domain_diagram(version: str = "baseline") -> None:
    is_change = version == "change"
    height = 1010 if is_change else 970
    canvas = Canvas(1400, height)
    title(canvas, "CampusEvent 领域模型类图" + ("（change-v2）" if is_change else "（baseline-v1）"),
          "实体、值对象与状态枚举；变更版仅扩展报名状态，不新增实体")

    student = class_box(canvas, 50, 100, 330, "Student",
                        attrs=("- student_id : str", "- name : str", "- email : str", "- role : Role"),
                        methods=("+ is_admin() : bool",), stereotype="«entity»")
    activity = class_box(canvas, 500, 90, 360, "Activity",
                         attrs=("- activity_id : str", "- title : str", "- category : str",
                                "- start_at : datetime", "- location : str", "- capacity : int",
                                "- policy_type : PolicyType", "- description : str"),
                         methods=("+ is_open_for_registration(now) : bool",
                                  "+ with_updates(**changes) : Activity"),
                         stereotype="«entity»")
    registration = class_box(canvas, 500, 390, 360, "Registration",
                             attrs=("- registration_id : str", "- activity_id : str",
                                    "- student_id : str", "- status : RegistrationStatus",
                                    "- note : str"),
                             methods=("+ is_active() : bool",
                                      "+ with_status(status, note) : Registration"),
                             stereotype="«entity»")
    stats = class_box(canvas, 980, 90, 350, "RegistrationStats",
                      attrs=("- activity_id : str", "- capacity : int", "- approved : int", "- pending : int"),
                      methods=("+ remaining : int", "+ is_full : bool"), stereotype="«value object»")
    message = class_box(canvas, 980, 390, 350, "Message",
                        attrs=("- message_id : str", "- student_id : str", "- activity_id : str | None",
                               "- category : str", "- content : str", "- is_read : bool"),
                        methods=("+ new(student_id, activity_id, category, content)$",),
                        stereotype="«entity»")
    status_attrs = ("- PENDING = \"pending\"", "- APPROVED = \"approved\"",
                    "- REJECTED = \"rejected\"", "- CANCELLED = \"cancelled\"")
    if is_change:
        status_attrs = status_attrs + ("- WAITLISTED = \"waitlisted\"",)
    status = class_box(canvas, 50, 300, 330, "RegistrationStatus", attrs=status_attrs,
                       methods=("+ label : str", "+ is_active : bool"),
                       stereotype="«enumeration»", header=HEADER_CHANGE if is_change else HEADER)
    policy_attrs = ("- DIRECT = \"direct\"", "- REVIEW = \"review\"")
    if is_change:
        policy_attrs = policy_attrs + ("- WAITLIST = \"waitlist\"",)
    policy_type = class_box(canvas, 50, status.y + status.h + 60, 330, "PolicyType",
                            attrs=policy_attrs, methods=("+ label : str",),
                            stereotype="«enumeration»", header=HEADER_CHANGE if is_change else HEADER)
    role = class_box(canvas, 50, policy_type.y + policy_type.h + 55, 330, "Role",
                     attrs=("- STUDENT = \"student\"", "- ADMIN = \"admin\""),
                     methods=("+ label : str",), stereotype="«enumeration»")

    relation(canvas, student.anchor("right", 0.55), registration.anchor("left", 0.25),
             label_text="1 报名 0..*", label_dx=8, label_dy=-14)
    relation(canvas, activity.anchor("bottom", 0.5), registration.anchor("top", 0.5),
             label_text="1 包含 0..*", label_dx=64, label_dy=-2)
    relation(canvas, registration.anchor("left", 0.35), status.anchor("right", 0.55),
             dashed=True, color=GREEN, label_text="status", label_dx=4, label_dy=-10)
    polyline(canvas, [activity.anchor("left", 0.2), (455, activity.y + activity.h * 0.2),
                      (455, policy_type.y + policy_type.h * 0.5),
                      policy_type.anchor("right", 0.5)],
             dashed=True, color=GREEN, label_text="policy_type", label_segment=2,
             label_t=0.5, label_dx=0, label_dy=-11)
    polyline(canvas, [student.anchor("left", 0.3), (25, student.y + student.h * 0.3),
                      (25, role.y + role.h * 0.5), role.anchor("left", 0.5)],
             dashed=True, color=GREEN, label_text="role", label_segment=1,
             label_t=0.5, label_dx=-2, label_dy=-10)
    relation(canvas, activity.anchor("right", 0.45), stats.anchor("left", 0.5),
             dashed=True, label_text="«derive»", label_dx=-6, label_dy=-10)

    note_y = max(role.y + role.h, message.y + message.h) + 30
    canvas.rect(500, note_y, 830, 46, fill="#f8fafc", outline="#cbd5e1", width=1, radius=6)
    canvas.text(516, note_y + 8, "Message 通过 student_id / activity_id 弱关联，不持有对象引用；", 10.5, False, MUTED)
    canvas.text(516, note_y + 25, "状态枚举约束由数据库 CHECK 与领域对象共同保证。", 10.5, False, MUTED)
    if is_change:
        canvas.rect(980, 600, 350, 84, fill="#fff7ed", outline="#fdba74", width=1.2, radius=8)
        canvas.text(996, 612, "变更点（CR-01 / CR-02）", 11, True, CHANGE)
        canvas.text(996, 632, "新增 waitlisted 状态；活动新增 cancelled 状态。", 10.5, False, INK)
        canvas.text(996, 650, "实体字段不变，仅扩展状态枚举与报名策略。", 10.5, False, INK)
    canvas.save("class_domain_change.png" if is_change else "class_domain_baseline.png")


# ---------------------------------------------------------------------------
# 设计类图
# ---------------------------------------------------------------------------
def design_diagram(version: str = "baseline") -> None:
    is_change = version == "change"
    canvas = Canvas(1500, 1340 if is_change else 1160)
    title(canvas, "CampusEvent 设计类图" + ("（change-v2）" if is_change else "（baseline-v1）"),
          "策略模式封装报名规则；观察者模式解耦报名业务与通知渠道")
    group_label(canvas, 40, 78, "报名规则（Strategy）")
    group_label(canvas, 430, 78, "应用服务")
    group_label(canvas, 900, 78, "通知（Observer）")

    policy = class_box(canvas, 40, 105, 330, "RegistrationPolicy",
                       attrs=("+ policy_type : PolicyType", "+ display_name : str"),
                       methods=("+ evaluate(ctx) : PolicyDecision", "# decide(ctx)* : PolicyDecision"),
                       stereotype="«interface»")
    direct = class_box(canvas, 40, 300, 330, "DirectRegistrationPolicy",
                       methods=("+ decide(ctx) : PolicyDecision",), stereotype="«strategy»")
    if is_change:
        waitlist = class_box(canvas, 40, 410, 330, "WaitlistRegistrationPolicy",
                             methods=("+ decide(ctx) : PolicyDecision",),
                             stereotype="«strategy» · NEW", fill="#fff7ed", header=HEADER_CHANGE)
        review_y = 520
        registry_y = 650
        context_y = 780
        decision_y = 975
    else:
        review_y = 415
        registry_y = 545
        context_y = 675
        decision_y = 835
    review = class_box(canvas, 40, review_y, 330, "ReviewRegistrationPolicy",
                       methods=("+ decide(ctx) : PolicyDecision",), stereotype="«strategy»")
    registry = class_box(canvas, 40, registry_y, 330, "PolicyRegistry",
                         attrs=("- _policies : dict[PolicyType, RegistrationPolicy]",),
                         methods=("+ for_activity(activity) : RegistrationPolicy", "+ all() : list"))
    class_box(canvas, 40, context_y, 330, "RegistrationContext",
              attrs=("- activity / student", "- approved_count : int",
                     "- existing_active : Registration | None", "- now : datetime"),
              methods=("+ remaining_slots : int", "+ is_full : bool"), stereotype="«value object»")
    class_box(canvas, 40, decision_y, 330, "PolicyDecision",
              attrs=("- allowed : bool", "- target_status : RegistrationStatus", "- reason : str"),
              methods=("+ approve(status)$", "+ deny(reason)$"), stereotype="«value object»")

    registration_service = class_box(canvas, 430, 105, 400, "RegistrationService",
                                     attrs=("- policies : PolicyRegistry", "- publisher : EventBus"),
                                     methods=("+ register(activity_id, student_id) : Registration",
                                              "+ cancel(registration_id, actor) : Registration",
                                              "+ list_mine(student_id) : list[RegistrationDetail]"))
    approval_service = class_box(canvas, 430, 315, 400, "ApprovalService",
                                 methods=("+ approve(registration_id, actor) : Registration",
                                          "+ reject(registration_id, actor) : Registration"))
    activity_service = class_box(canvas, 430, 455, 400, "ActivityService",
                                 methods=("+ create(actor, payload) : Activity",
                                          "+ update(actor, activity_id, payload) : Activity",
                                          "+ delete(actor, activity_id) : None",
                                          "+ stats(activity) : RegistrationStats"))
    event_bus = class_box(canvas, 430, 700, 400, "EventBus",
                          attrs=("- _subscribers : list[NotificationSubscriber]",),
                          methods=("+ publish(event) : DeliveryReport",))
    if is_change:
        class_box(canvas, 430, 870, 400, "WaitlistService",
                  methods=("+ promote_next(activity_id) : Registration | None",),
                  fill="#fff7ed", header=HEADER_CHANGE, title_color=CHANGE)

    subscriber = class_box(canvas, 900, 105, 400, "NotificationSubscriber",
                           attrs=("+ name : str", "+ channel : str"),
                           methods=("+ supports(event) : bool", "+ handle(event) : None",
                                    "# deliver(student, content)* : None"),
                           stereotype="«interface»")
    in_site = class_box(canvas, 900, 300, 200, "InSiteSubscriber",
                        methods=("# deliver(student, content)",), stereotype="«observer»")
    email = class_box(canvas, 1120, 300, 200, "EmailSubscriber",
                      methods=("# deliver(student, content)",), stereotype="«observer»")
    class_box(canvas, 900, 450, 200, "MessageRepository",
              methods=("+ add(message)", "+ list_for_student(id)"))
    class_box(canvas, 1120, 450, 200, "EmailGateway",
              methods=("+ send(to, subject, body) : str",), stereotype="«interface»")
    delivery = class_box(canvas, 900, 600, 420, "NotificationDeliveryRepository",
                         attrs=("UNIQUE(event_id, subscriber, student_id)",),
                         methods=("+ claim(event_id, subscriber, student_id)",
                                  "+ mark(delivery_id, status, error)"))

    # 继承
    relation(canvas, direct.anchor("top"), policy.anchor("bottom"), head="hollow")
    if is_change:
        polyline(canvas, [waitlist.anchor("left", 0.5), (30, waitlist.y + waitlist.h * 0.5),
                          (30, policy.y + policy.h * 0.78), policy.anchor("left", 0.78)],
                 head="hollow")
        polyline(canvas, [review.anchor("left", 0.5), (20, review.y + review.h * 0.5),
                          (20, policy.y + policy.h * 0.88), policy.anchor("left", 0.88)],
                 head="hollow")
    else:
        polyline(canvas, [review.anchor("left", 0.5), (25, review.y + review.h * 0.5),
                          (25, policy.y + policy.h * 0.8), policy.anchor("left", 0.8)],
                 head="hollow")
    relation(canvas, in_site.anchor("top", 0.5), subscriber.anchor("bottom", 0.3), head="hollow")
    relation(canvas, email.anchor("top", 0.5), subscriber.anchor("bottom", 0.7), head="hollow")

    # 服务与策略
    relation(canvas, registration_service.anchor("left", 0.3), policy.anchor("right", 0.65),
             dashed=True, label_text="选择策略", label_dy=-14)
    polyline(canvas, [registration_service.anchor("left", 0.85), (405, registration_service.y + registration_service.h * 0.85),
                      (405, event_bus.y + 70), event_bus.anchor("left", 0.58)],
             dashed=True, label_text="publish", label_segment=1, label_t=0.55,
             label_dx=14, label_dy=-14)
    polyline(canvas, [approval_service.anchor("left", 0.5), (390, approval_service.y + approval_service.h * 0.5),
                      (390, event_bus.y + 100), event_bus.anchor("left", 0.83)],
             dashed=True, label_text="publish", label_segment=1, label_t=0.7,
             label_dx=14, label_dy=-14)
    relation(canvas, activity_service.anchor("bottom", 0.55), event_bus.anchor("top", 0.55),
             dashed=True, label_text="publish", label_dx=36, label_dy=-2)
    polyline(canvas, [event_bus.anchor("right", 0.5), (865, event_bus.y + event_bus.h * 0.5),
                      (865, subscriber.y + subscriber.h * 0.5), subscriber.anchor("left", 0.5)],
             label_text="notify 1..*", label_segment=1, label_t=0.55, label_dx=-2, label_dy=-14)
    relation(canvas, in_site.anchor("bottom"), (1000, 450), dashed=True,
             label_text="add", label_dy=-6)
    relation(canvas, email.anchor("bottom"), (1220, 450), dashed=True,
             label_text="send", label_dy=-6)
    polyline(canvas, [in_site.anchor("bottom", 0.5), (1000, 398),
                      (1340, 398), (1340, 640), delivery.anchor("right", 0.3)],
             dashed=True, label_text="claim", label_segment=1, label_t=0.6,
             label_dx=-2, label_dy=-10)
    polyline(canvas, [email.anchor("right", 0.8), (1360, email.y + email.h * 0.8),
                      (1360, 680), delivery.anchor("right", 0.65)],
             dashed=True, label_text="claim", label_segment=1, label_t=0.55,
             label_dx=-2, label_dy=-10)
    if is_change:
        relation(canvas, waitlist_service_top(), event_bus.anchor("bottom", 0.5), dashed=True,
                 label_text="publish", label_dx=40, label_dy=-4)
        canvas.text(430, 990, "由 RegistrationService.cancel() 在取消已通过报名后调用；递补写入与其处于同一事务。",
                    10, False, CHANGE)

    notes = [
        "1. evaluate() 是模板方法：先执行活动时间、重复有效报名等公共规则，再委托 decide() 处理策略变化点。",
        "2. 新增报名方式 = 新增策略类 + 在 PolicyRegistry 登记；RegistrationService 无需修改。",
        "3. 报名事务提交后才 publish；订阅者异常被隔离并写入投递台账，不影响已提交的报名。",
        "4. 投递台账唯一约束保证同一事件不重复通知。",
    ]
    if is_change:
        notes.append("5. CR-01：候补递补属于领域写入，由 WaitlistService 完成；通知仍由订阅者处理，不混入观察者。")
    note_y = 1160 if is_change else 1015
    canvas.text(40, note_y, "设计要点", 12, True, INK)
    y = note_y + 22
    for note in notes:
        canvas.text(40, y, note, 10.5, False, MUTED)
        y += 19
    canvas.save("class_design_change.png" if is_change else "class_design_baseline.png")


def waitlist_service_top():
    return (630, 870)


# ---------------------------------------------------------------------------
# 用例图
# ---------------------------------------------------------------------------
def actor(canvas: Canvas, x: float, y: float, name: str) -> None:
    canvas.draw.ellipse([(x - 10) * S, (y - 52) * S, (x + 10) * S, (y - 32) * S],
                        outline=INK, width=max(1, int(1.4 * S)))
    canvas.line(x, y - 32, x, y - 4, INK, 1.6)
    canvas.line(x - 20, y - 22, x + 20, y - 22, INK, 1.6)
    canvas.line(x, y - 4, x - 16, y + 20, INK, 1.6)
    canvas.line(x, y - 4, x + 16, y + 20, INK, 1.6)
    canvas.text(x, y + 30, name, 13, True, INK, anchor="mt")


def use_case(canvas: Canvas, x: float, y: float, w: float, h: float, name: str) -> None:
    canvas.ellipse(x, y, w, h, fill="#f8fafc", outline=LINE, width=1.3)
    lines = canvas.wrap(name, 11, w - 24)
    total = len(lines) * 16
    cursor = y + h / 2 - total / 2
    for line in lines:
        canvas.text(x + w / 2, cursor, line, 11, False, INK, anchor="mt")
        cursor += 16


def use_case_diagram() -> None:
    canvas = Canvas(1400, 900)
    title(canvas, "CampusEvent 用例图", "学生完成浏览与报名，管理员完成活动维护与审批")
    canvas.rect(300, 80, 900, 740, fill="#fbfcff", outline="#94a3b8", width=1.3, radius=10)
    canvas.text(750, 92, "CampusEvent 校园活动报名与管理系统", 12.5, True, MUTED, anchor="mt")

    actor(canvas, 150, 360, "学生 Student")
    actor(canvas, 1300, 370, "管理员 Admin")

    student_cases = [
        ("浏览 / 搜索活动", 120), ("查看活动详情", 215), ("报名活动", 310),
        ("取消报名", 405), ("查看我的报名", 500), ("查看站内消息", 595),
    ]
    admin_cases = [
        ("创建 / 编辑活动", 140), ("删除活动", 235), ("审批报名", 330),
        ("查看报名统计", 425), ("查看通知台账", 520),
    ]
    for name, y in student_cases:
        use_case(canvas, 380, y, 250, 72, name)
    for name, y in admin_cases:
        use_case(canvas, 980, y, 250, 72, name)

    for _, y in student_cases:
        canvas.line(188, 372, 380, y + 36, "#94a3b8", 1.2)
    for _, y in admin_cases:
        canvas.line(1262, 380, 1230, y + 36, "#94a3b8", 1.2)

    use_case(canvas, 700, 310, 230, 72, "报名资格校验")
    relation(canvas, (630, 346), (700, 346), dashed=True, label_text="«include»", label_dy=-12)
    canvas.rect(690, 410, 260, 112, fill="#fffbeb", outline="#f59e0b", width=1.1, radius=6)
    canvas.text(704, 420, "公共规则（模板方法）", 10.5, True, "#92400e")
    canvas.text(704, 440, "· 活动开始前", 10, False, "#92400e")
    canvas.text(704, 458, "· 无重复有效报名", 10, False, "#92400e")
    canvas.text(704, 484, "策略职责（decide）", 10.5, True, "#92400e")
    canvas.text(704, 502, "· 满员拒绝 / 进入待审核", 10, False, "#92400e")

    canvas.text(320, 780, "说明：待审核不占名额；批准时再次校验容量。活动开始后不允许新增报名。",
                10.5, False, MUTED)
    canvas.save("use_case.png")


# ---------------------------------------------------------------------------
# 时序图
# ---------------------------------------------------------------------------
@dataclass
class Participant:
    key: str
    label: str
    x: float


def sequence_diagram(filename: str, heading: str, subtitle: str,
                     participants: list[Participant],
                     messages: list[tuple[str, str, str]],
                     width: int = 1600) -> None:
    height = 200 + len(messages) * 76 + 70
    canvas = Canvas(width, height)
    title(canvas, heading, subtitle)
    head_y = 92
    head_w = 186
    head_h = 58
    for p in participants:
        canvas.rect(p.x - head_w / 2, head_y, head_w, head_h, fill="#eef2ff",
                    outline="#64748b", width=1.2, radius=6)
        lines = canvas.wrap(p.label, 10.5, head_w - 14, bold=True)
        start = head_y + head_h / 2 - (len(lines) * 14) / 2
        for line in lines:
            canvas.text(p.x, start, line, 10.5, True, INK, anchor="mt")
            start += 14
        canvas.line(p.x, head_y + head_h, p.x, height - 40, "#94a3b8", 1.1, dash=True)

    y = 215
    by_key = {p.key: p for p in participants}
    for index, (src, dst, text) in enumerate(messages, start=1):
        sx, dx = by_key[src].x, by_key[dst].x
        if src == dst:
            canvas.line(sx, y - 6, sx + 55, y - 6, INK, 1.3)
            canvas.line(sx + 55, y - 6, sx + 55, y + 24, INK, 1.3)
            relation(canvas, (sx + 55, y + 24), (sx, y + 24), head="filled")
            canvas.text(sx + 66, y + 2, f"{index}. {text}", 10.5, False, INK)
            y += 62
            continue
        direction = 1 if dx > sx else -1
        relation(canvas, (sx + 6 * direction, y), (dx - 6 * direction, y),
                 head="filled", color="#334155")
        full = f"{index}. {text}"
        gap = abs(dx) - 24
        text_w = canvas.text_width(full, 10.5)
        cx = (sx + dx) / 2
        if text_w <= gap:
            canvas.rect(cx - text_w / 2 - 4, y - 25, text_w + 8, 18, fill="#ffffff", outline=None)
            canvas.text(cx, y - 23, full, 10.5, False, INK, anchor="mt")
        else:
            lines = canvas.wrap(full, 10.5, gap)
            offset = 4 + (len(lines) - 1) * 15
            for i, line in enumerate(lines):
                ly = y - 23 - offset + i * 15
                lw = canvas.text_width(line, 10.5)
                canvas.rect(cx - lw / 2 - 4, ly - 1, lw + 8, 17, fill="#ffffff", outline=None)
                canvas.text(cx, ly, line, 10.5, False, INK, anchor="mt")
        y += 76
    canvas.save(filename)


def direct_registration_sequence() -> None:
    participants = [
        Participant("ui", "学生浏览器", 120),
        Participant("svc", "RegistrationService", 390),
        Participant("policy", "RegistrationPolicy\n(Direct)", 660),
        Participant("db", "SQLite\nregistrations", 920),
        Participant("bus", "EventBus", 1180),
        Participant("sub", "站内 / 邮件订阅者", 1450),
    ]
    messages = [
        ("ui", "svc", "POST /activities/{id}/register"),
        ("svc", "db", "读取活动、有效报名、已通过数"),
        ("svc", "policy", "for_activity(activity)"),
        ("svc", "policy", "evaluate(ctx)"),
        ("policy", "policy", "公共规则 + decide 判定满员"),
        ("svc", "db", "INSERT (approved)  [BEGIN IMMEDIATE]"),
        ("db", "svc", "commit"),
        ("svc", "bus", "publish(RegistrationApproved)"),
        ("bus", "sub", "handle(event) × 2 渠道"),
        ("svc", "ui", "302 跳转详情页"),
    ]
    sequence_diagram("seq_direct_registration.png", "时序图：直接报名（baseline-v1）",
                     "公共规则与策略判定在写事务内完成；事务提交后才发送通知",
                     participants, messages)


def review_registration_sequence() -> None:
    participants = [
        Participant("ui", "学生浏览器", 120),
        Participant("svc", "RegistrationService", 390),
        Participant("policy", "RegistrationPolicy\n(Review)", 660),
        Participant("db", "SQLite\nregistrations", 920),
        Participant("bus", "EventBus", 1180),
        Participant("sub", "站内 / 邮件订阅者", 1450),
    ]
    messages = [
        ("ui", "svc", "POST /activities/{id}/register"),
        ("svc", "db", "读取活动、有效报名、已通过数"),
        ("svc", "policy", "evaluate(ctx)"),
        ("policy", "policy", "decide → PENDING（不占名额）"),
        ("svc", "db", "INSERT (pending)"),
        ("db", "svc", "commit"),
        ("svc", "bus", "publish(RegistrationSubmitted)"),
        ("bus", "sub", "站内消息 + 模拟邮件"),
        ("svc", "ui", "302 跳转详情页"),
    ]
    sequence_diagram("seq_review_registration.png", "时序图：审核型报名（baseline-v1）",
                     "待审核不占名额；真正的容量闸门在管理员批准时",
                     participants, messages)


def approval_sequence() -> None:
    participants = [
        Participant("ui", "管理员浏览器", 120),
        Participant("svc", "ApprovalService", 400),
        Participant("db", "SQLite\nregistrations", 680),
        Participant("bus", "EventBus", 960),
        Participant("sub", "站内 / 邮件订阅者", 1230),
        Participant("stu", "学生消息中心", 1490),
    ]
    messages = [
        ("ui", "svc", "POST /admin/approvals/{id}/approve"),
        ("svc", "db", "get_detail(registration)"),
        ("svc", "db", "count(approved)  事务内再次检查"),
        ("svc", "db", "UPDATE status = approved"),
        ("db", "svc", "commit"),
        ("svc", "bus", "publish(RegistrationApproved, via=review)"),
        ("bus", "sub", "handle(event)"),
        ("sub", "stu", "写入 messages / email_outbox"),
        ("svc", "ui", "302 返回审批台"),
    ]
    sequence_diagram("seq_approval.png", "时序图：管理员审批（baseline-v1）",
                     "批准前在写事务内再次统计已通过人数，避免超员（C8）",
                     participants, messages)


def waitlist_sequence() -> None:
    participants = [
        Participant("ui", "学生 A 浏览器", 120),
        Participant("svc", "RegistrationService", 390),
        Participant("wl", "WaitlistService", 660),
        Participant("db", "SQLite", 920),
        Participant("bus", "EventBus", 1180),
        Participant("sub", "通知订阅者", 1450),
    ]
    messages = [
        ("ui", "svc", "POST /registrations/{id}/cancel"),
        ("svc", "db", "UPDATE status = cancelled"),
        ("svc", "wl", "promote_next(activity_id)"),
        ("wl", "db", "查询 waitlisted，按 created_at 取最早"),
        ("wl", "db", "UPDATE status = approved"),
        ("svc", "bus", "publish(RegistrationCancelled)"),
        ("bus", "sub", "通知学生 A：报名已取消"),
        ("wl", "bus", "publish(RegistrationPromoted)"),
        ("bus", "sub", "通知学生 B：候补递补成功"),
    ]
    sequence_diagram("seq_waitlist_promotion.png", "时序图：候补自动递补（change-v2 / CR-01）",
                     "取消与递补在同一事务中完成；通知仍由订阅者处理",
                     participants, messages)


if __name__ == "__main__":
    domain_diagram("baseline")
    design_diagram("baseline")
    use_case_diagram()
    direct_registration_sequence()
    review_registration_sequence()
    approval_sequence()


