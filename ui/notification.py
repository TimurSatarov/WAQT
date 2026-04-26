"""
notification.py — Prayer time notification popup.
Shows when a prayer time arrives with a person illustration.
Can be disabled via settings.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath,
    QFont, QLinearGradient, QRadialGradient
)

ACCENT  = "#1D9E75"
BG      = "#0f1e2e"
TEXT    = "#e0e0e0"
MUTED   = "#8888aa"


class PersonIllustration(QWidget):
    """Draws a simple person with hands raised to ears (Takbir position)."""

    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._size = size

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sz = self._size
        c  = QColor(ACCENT)
        skin = QColor("#f5c895")

        # ── Glow circle background ────────────────────────────────────────
        glow = QRadialGradient(sz/2, sz/2, sz/2)
        glow.setColorAt(0.0, QColor(29, 158, 117, 40))
        glow.setColorAt(1.0, QColor(29, 158, 117, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, sz, sz)

        s = sz / 80  # scale factor (base design at 80px)

        def sc(v): return v * s  # scale value

        # ── Head ──────────────────────────────────────────────────────────
        p.setBrush(QBrush(skin))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(sz/2, sc(14)), sc(10), sc(10))

        # ── Kufi (cap) ────────────────────────────────────────────────────
        p.setBrush(QBrush(QColor("#2a4a3a")))
        cap = QPainterPath()
        cap.addEllipse(QPointF(sz/2, sc(10)), sc(10), sc(7))
        cap.addRect(QRectF(sz/2 - sc(10), sc(10), sc(20), sc(5)))
        p.drawPath(cap)

        # ── Body (thobe) ──────────────────────────────────────────────────
        p.setBrush(QBrush(QColor("#dce8f0")))
        body = QPainterPath()
        body.moveTo(sz/2 - sc(10), sc(25))
        body.lineTo(sz/2 + sc(10), sc(25))
        body.lineTo(sz/2 + sc(13), sc(62))
        body.lineTo(sz/2 - sc(13), sc(62))
        body.closeSubpath()
        p.drawPath(body)

        # ── Left arm raised (Takbir) ──────────────────────────────────────
        arm_pen = QPen(skin, sc(6), Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap)
        p.setPen(arm_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Left arm: shoulder → elbow → hand near ear
        p.drawLine(QPointF(sz/2 - sc(9), sc(28)),
                   QPointF(sz/2 - sc(20), sc(22)))
        p.drawLine(QPointF(sz/2 - sc(20), sc(22)),
                   QPointF(sz/2 - sc(18), sc(12)))

        # Right arm
        p.drawLine(QPointF(sz/2 + sc(9), sc(28)),
                   QPointF(sz/2 + sc(20), sc(22)))
        p.drawLine(QPointF(sz/2 + sc(20), sc(22)),
                   QPointF(sz/2 + sc(18), sc(12)))

        # ── Hands near ears ───────────────────────────────────────────────
        p.setBrush(QBrush(skin))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(sz/2 - sc(18), sc(10)), sc(4), sc(4))
        p.drawEllipse(QPointF(sz/2 + sc(18), sc(10)), sc(4), sc(4))

        # ── Legs ──────────────────────────────────────────────────────────
        leg_pen = QPen(QColor("#c8d8e4"), sc(7), Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap)
        p.setPen(leg_pen)
        p.drawLine(QPointF(sz/2 - sc(5), sc(61)),
                   QPointF(sz/2 - sc(6), sc(74)))
        p.drawLine(QPointF(sz/2 + sc(5), sc(61)),
                   QPointF(sz/2 + sc(6), sc(74)))


class PrayerNotification(QWidget):
    dismissed = pyqtSignal()

    def __init__(self, prayer_name: str, prayer_time: str, parent=None):
        super().__init__(parent)
        self._prayer = prayer_name

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(280, 180)

        self._build_ui(prayer_name, prayer_time)
        self._position()

        # Auto-dismiss after 15 seconds
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._dismiss)
        self._auto_timer.start(15000)

    def _build_ui(self, name: str, time_str: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 14)
        root.setSpacing(8)

        # ── Top row: illustration + text ──────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(12)

        person = PersonIllustration(72)
        top.addWidget(person)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        it_lbl = QLabel("It's time for")
        it_lbl.setStyleSheet(f"color: {MUTED}; font-size: 11px; background: transparent;")
        text_col.addWidget(it_lbl)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"color: #ffffff; font-size: 20px; font-weight: 700; background: transparent;"
        )
        text_col.addWidget(name_lbl)

        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 14px; background: transparent;")
        text_col.addWidget(time_lbl)

        text_col.addStretch()
        top.addLayout(text_col)
        top.addStretch()

        root.addLayout(top)

        # ── Divider ───────────────────────────────────────────────────────
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: rgba(255,255,255,0.08);")
        root.addWidget(div)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: #ffffff; border: none;
                border-radius: 6px; padding: 6px 16px; font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: #17b882; }}
        """)
        dismiss_btn.clicked.connect(self._dismiss)

        snooze_btn = QPushButton("5 min")
        snooze_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {MUTED}; border: 1px solid #2a2a4a;
                border-radius: 6px; padding: 6px 12px; font-size: 12px;
            }}
            QPushButton:hover {{ color: {TEXT}; border-color: {ACCENT}; }}
        """)
        snooze_btn.clicked.connect(self._snooze)

        btn_row.addStretch()
        btn_row.addWidget(snooze_btn)
        btn_row.addWidget(dismiss_btn)
        root.addLayout(btn_row)

    def _position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 16,
                  screen.bottom() - self.height() - 16)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Card background
        p.setBrush(QBrush(QColor("#0f1e2e")))
        p.setPen(QPen(QColor(ACCENT), 1.0))
        p.drawRoundedRect(QRectF(0.5, 0.5, w-1, h-1), 14, 14)

        # Top accent line
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(QRectF(0, 0, w, 3), 2, 2)

    def _dismiss(self):
        self._auto_timer.stop()
        self.hide()
        self.dismissed.emit()

    def _snooze(self):
        """Hide and re-show after 5 minutes."""
        self._auto_timer.stop()
        self.hide()
        QTimer.singleShot(5 * 60 * 1000, self.show)
        QTimer.singleShot(5 * 60 * 1000, self._position)


def show_prayer_notification(prayer_name: str, prayer_time: str) -> PrayerNotification:
    """Create and show a prayer notification. Returns widget so caller can connect signals."""
    notif = PrayerNotification(prayer_name, prayer_time)
    notif.show()
    return notif