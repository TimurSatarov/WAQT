"""
notification.py — Prayer time notification popup.
Redesigned: compact, localized, better visual hierarchy.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath,
    QFont, QRadialGradient
)

# Try to import theme colors, fallback to defaults
try:
    from themes import THEMES
    _theme = THEMES.get("Dark Green", {})
except ImportError:
    _theme = {}

ACCENT  = _theme.get("accent", "#34D399")
BG      = _theme.get("bg", "#0f172a")
TEXT    = _theme.get("text", "#F9FAFB")
MUTED   = "#6B7280"


class PersonIllustration(QWidget):
    """Draws a person with hands raised (Takbir) — larger with glow."""

    def __init__(self, size: int = 90, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._size = size
        self._s = size / 90  # scale factor

    def _sc(self, v: float) -> float:
        return v * self._s

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sz = self._size
        s = self._s

        # Glow behind person
        glow = QRadialGradient(sz/2, sz/2, sz/2)
        glow.setColorAt(0.0, QColor(ACCENT).lighter(120))
        glow.setColorAt(0.4, QColor(ACCENT))
        glow.setColorAt(1.0, QColor(ACCENT).darker(200))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, sz, sz)

        c = QColor(ACCENT)
        skin = QColor("#f5c895")

        # Head
        p.setBrush(QBrush(skin))
        p.drawEllipse(QPointF(sz/2, self._sc(16)), self._sc(12), self._sc(12))

        # Kufi
        p.setBrush(QBrush(QColor("#2a4a3a")))
        cap = QPainterPath()
        cap.addEllipse(QPointF(sz/2, self._sc(11)), self._sc(12), self._sc(8))
        cap.addRect(QRectF(sz/2 - self._sc(12), self._sc(11), self._sc(24), self._sc(6)))
        p.drawPath(cap)

        # Body (thobe)
        p.setBrush(QBrush(QColor("#dce8f0")))
        body = QPainterPath()
        body.moveTo(sz/2 - self._sc(12), self._sc(28))
        body.lineTo(sz/2 + self._sc(12), self._sc(28))
        body.lineTo(sz/2 + self._sc(15), self._sc(68))
        body.lineTo(sz/2 - self._sc(15), self._sc(68))
        body.closeSubpath()
        p.drawPath(body)

        # Arms raised
        arm_pen = QPen(skin, self._sc(7), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(arm_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Left
        p.drawLine(QPointF(sz/2 - self._sc(10), self._sc(30)),
                   QPointF(sz/2 - self._sc(24), self._sc(22)))
        p.drawLine(QPointF(sz/2 - self._sc(24), self._sc(22)),
                   QPointF(sz/2 - self._sc(22), self._sc(10)))
        # Right
        p.drawLine(QPointF(sz/2 + self._sc(10), self._sc(30)),
                   QPointF(sz/2 + self._sc(24), self._sc(22)))
        p.drawLine(QPointF(sz/2 + self._sc(24), self._sc(22)),
                   QPointF(sz/2 + self._sc(22), self._sc(10)))

        # Hands
        p.setBrush(QBrush(skin))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(sz/2 - self._sc(22), self._sc(8)), self._sc(5), self._sc(5))
        p.drawEllipse(QPointF(sz/2 + self._sc(22), self._sc(8)), self._sc(5), self._sc(5))

        # Legs
        leg_pen = QPen(QColor("#c8d8e4"), self._sc(8), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(leg_pen)
        p.drawLine(QPointF(sz/2 - self._sc(6), self._sc(67)),
                   QPointF(sz/2 - self._sc(7), self._sc(82)))
        p.drawLine(QPointF(sz/2 + self._sc(6), self._sc(67)),
                   QPointF(sz/2 + self._sc(7), self._sc(82)))


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
        self.setFixedSize(300, 160)

        self._build_ui(prayer_name, prayer_time)
        self._position()

        # Auto-dismiss after 15 seconds
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._dismiss)
        self._auto_timer.start(15000)

    def _build_ui(self, name: str, time_str: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(10)

        # Top row: illustration + text
        top = QHBoxLayout()
        top.setSpacing(14)

        person = PersonIllustration(90)
        top.addWidget(person)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        subtitle = QLabel("Время намаза")
        subtitle.setStyleSheet(f"color: {MUTED}; font-size: 11px; background: transparent;")
        text_col.addWidget(subtitle)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: #ffffff; background: transparent;")
        text_col.addWidget(name_lbl)

        time_lbl = QLabel(time_str)
        time_lbl.setFont(QFont("Segoe UI", 14))
        time_lbl.setStyleSheet(f"color: {ACCENT}; background: transparent;")
        text_col.addWidget(time_lbl)

        text_col.addStretch()
        top.addLayout(text_col)
        top.addStretch()

        root.addLayout(top)

        # Divider
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255,255,255,0.06);")
        root.addWidget(div)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        snooze_btn = QPushButton("5 мин")
        snooze_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {MUTED};
                border: 1px solid #374151; border-radius: 8px;
                padding: 6px 14px; font-size: 12px;
            }}
            QPushButton:hover {{ color: {TEXT}; border-color: {ACCENT}; }}
        """)
        snooze_btn.clicked.connect(self._snooze)

        dismiss_btn = QPushButton("Закрыть")
        dismiss_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: #ffffff; border: none;
                border-radius: 8px; padding: 6px 16px; font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {ACCENT}dd; }}
            QPushButton:pressed {{ background: {ACCENT}99; }}
        """)
        dismiss_btn.clicked.connect(self._dismiss)

        btn_row.addStretch()
        btn_row.addWidget(snooze_btn)
        btn_row.addWidget(dismiss_btn)
        root.addLayout(btn_row)

    def _position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20,
                  screen.bottom() - self.height() - 20)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Card background with subtle border
        p.setBrush(QBrush(QColor(BG)))
        p.setPen(QPen(QColor(ACCENT), 1.2))
        p.drawRoundedRect(QRectF(0.5, 0.5, w-1, h-1), 16, 16)

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
    """Create and show a prayer notification."""
    notif = PrayerNotification(prayer_name, prayer_time)
    notif.show()
    return notif