from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QApplication, QDialog, QGridLayout, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QCursor, QPainterPath

ACCENT = "#1D9E75"


class CrescentWidget(QWidget):
    """A small crescent moon drawn with QPainter — no emoji."""
    def __init__(self, size: int = 14, color: str = ACCENT, parent=None):
        super().__init__(parent)
        self._size  = size
        self._color = color
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.PenStyle.NoPen)
        sz = self._size
        outer = QPainterPath()
        outer.addEllipse(QPointF(sz/2, sz/2), sz/2 - 1, sz/2 - 1)
        inner = QPainterPath()
        inner.addEllipse(QPointF(sz/2 + sz*0.19, sz/2 - sz*0.04),
                         sz * 0.36, sz * 0.36)
        p.drawPath(outer.subtracted(inner))

# ── Style definitions ─────────────────────────────────────────────────────────

OVERLAY_STYLES = {
    "pill": {
        "name": "Pill",
        "desc": "Compact horizontal pill",
        "w": 210, "h": 36,
    },
    "card": {
        "name": "Card",
        "desc": "Two-line card with accent bar",
        "w": 200, "h": 60,
    },
    "minimal": {
        "name": "Minimal",
        "desc": "Just text, no background",
        "w": 180, "h": 40,
    },
}


# ── Style picker dialog ───────────────────────────────────────────────────────

class StyleCard(QFrame):
    selected = pyqtSignal(str)

    def __init__(self, key: str, info: dict, is_active: bool):
        super().__init__()
        self._key = key
        self.setFixedSize(150, 70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = is_active
        self._update_style()

        v = QVBoxLayout(self)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(2)

        name_lbl = QLabel(info["name"])
        name_lbl.setStyleSheet(
            f"color: {'#5DCAA5' if is_active else '#e0e0e0'}; "
            f"font-size: 12px; font-weight: {'600' if is_active else '400'}; background: transparent;"
        )
        desc_lbl = QLabel(info["desc"])
        desc_lbl.setStyleSheet("color: #8888aa; font-size: 10px; background: transparent;")
        desc_lbl.setWordWrap(True)

        v.addWidget(name_lbl)
        v.addWidget(desc_lbl)
        v.addStretch()

    def _update_style(self):
        border = f"1.5px solid {ACCENT}" if self._active else "1px solid #2a2a4a"
        self.setStyleSheet(f"""
            QFrame {{
                background: {'#0d2b1f' if self._active else '#16213e'};
                border: {border};
                border-radius: 8px;
            }}
        """)

    def mousePressEvent(self, event):
        self.selected.emit(self._key)


class OverlayStyleDialog(QDialog):
    style_chosen = pyqtSignal(str)

    def __init__(self, current_style: str = "card", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Overlay style")
        self.setModal(True)
        self.setFixedSize(360, 200)
        self._current = current_style
        self._cards   = {}

        self.setStyleSheet("""
            QDialog { background: #1a1a2e; }
            QLabel  { color: #e0e0e0; background: transparent; }
            QPushButton {
                background: #1D9E75; color: #fff; border: none;
                border-radius: 6px; padding: 7px 20px; font-size: 13px;
            }
            QPushButton:hover { background: #17b882; }
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        title = QLabel("Choose overlay style")
        title.setStyleSheet("font-size: 13px; font-weight: 600; color: #fff;")
        v.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        for i, (key, info) in enumerate(OVERLAY_STYLES.items()):
            card = StyleCard(key, info, is_active=(key == self._current))
            card.selected.connect(self._select)
            self._cards[key] = card
            grid.addWidget(card, 0, i)

        v.addLayout(grid)
        v.addStretch()

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply)
        v.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _select(self, key: str):
        if self._current in self._cards:
            old = self._cards[self._current]
            old._active = False
            old._update_style()
            # update label color
            for child in old.findChildren(QLabel):
                if child.font().pointSize() >= 11:
                    child.setStyleSheet("color: #e0e0e0; font-size: 12px; background: transparent;")
        self._current = key
        new = self._cards[key]
        new._active = True
        new._update_style()
        for child in new.findChildren(QLabel):
            if child.font().pointSize() >= 11:
                child.setStyleSheet(f"color: #5DCAA5; font-size: 12px; font-weight: 600; background: transparent;")

    def _apply(self):
        self.style_chosen.emit(self._current)
        self.accept()


# ── Overlay widget ────────────────────────────────────────────────────────────

class OverlayWidget(QWidget):
    def __init__(self, style: str = "card"):
        super().__init__()
        self._style    = style
        self._name     = "—"
        self._time_str = "--:--"
        self._countdown = "--:--:--"
        self._drag_pos  = QPoint()
        self._dragging  = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

        self._build()
        self._snap_default()

    def _build(self):
        # Clear existing layout
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)

        s = self._style

        if s == "pill":
            self.setFixedSize(210, 36)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(12, 0, 10, 0)
            layout.setSpacing(6)

            moon = CrescentWidget(12, ACCENT)
            layout.addWidget(moon)

            self._name_lbl = QLabel(self._name)
            self._name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            self._name_lbl.setStyleSheet("color: #ffffff;")
            layout.addWidget(self._name_lbl)

            sep = QLabel("·")
            sep.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 11px;")
            layout.addWidget(sep)

            self._time_lbl = QLabel(self._time_str)
            self._time_lbl.setFont(QFont("Segoe UI", 10))
            self._time_lbl.setStyleSheet("color: rgba(255,255,255,0.55);")
            layout.addWidget(self._time_lbl)

            sep2 = QLabel("·")
            sep2.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 11px;")
            layout.addWidget(sep2)

            self._countdown_lbl = QLabel(self._countdown)
            self._countdown_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            self._countdown_lbl.setStyleSheet(f"color: {ACCENT};")
            layout.addWidget(self._countdown_lbl)

            layout.addStretch()
            self._add_close(layout)

        elif s == "card":
            self.setFixedSize(200, 60)
            root = QVBoxLayout(self)
            root.setContentsMargins(14, 8, 10, 8)
            root.setSpacing(3)

            row1 = QHBoxLayout()
            row1.setSpacing(6)

            moon = CrescentWidget(14, ACCENT)
            row1.addWidget(moon)

            self._name_lbl = QLabel(self._name)
            self._name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self._name_lbl.setStyleSheet("color: #ffffff;")
            row1.addWidget(self._name_lbl)

            row1.addStretch()

            self._time_lbl = QLabel(self._time_str)
            self._time_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            self._time_lbl.setStyleSheet(f"color: {ACCENT};")
            row1.addWidget(self._time_lbl)

            self._add_close(row1)

            row2 = QHBoxLayout()
            row2.setSpacing(4)

            next_lbl = QLabel("next")
            next_lbl.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 9px;")
            row2.addWidget(next_lbl)

            self._countdown_lbl = QLabel(self._countdown)
            self._countdown_lbl.setFont(QFont("Segoe UI", 9))
            self._countdown_lbl.setStyleSheet("color: rgba(255,255,255,0.65);")
            row2.addWidget(self._countdown_lbl)
            row2.addStretch()

            root.addLayout(row1)
            root.addLayout(row2)

        elif s == "minimal":
            self.setFixedSize(180, 40)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(8, 0, 8, 0)
            layout.setSpacing(5)

            self._name_lbl = QLabel(self._name)
            self._name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self._name_lbl.setStyleSheet(f"color: {ACCENT};")
            layout.addWidget(self._name_lbl)

            self._time_lbl = QLabel(self._time_str)
            self._time_lbl.setFont(QFont("Segoe UI", 11))
            self._time_lbl.setStyleSheet("color: #ffffff;")
            layout.addWidget(self._time_lbl)

            sep = QLabel("·")
            sep.setStyleSheet("color: rgba(255,255,255,0.3);")
            layout.addWidget(sep)

            self._countdown_lbl = QLabel(self._countdown)
            self._countdown_lbl.setFont(QFont("Segoe UI", 10))
            self._countdown_lbl.setStyleSheet("color: rgba(255,255,255,0.6);")
            layout.addWidget(self._countdown_lbl)

            layout.addStretch()
            self._add_close(layout)

        self.update()

    def _add_close(self, layout):
        close = QLabel("×")
        close.setFixedSize(14, 14)
        close.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 13px;")
        close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close.mousePressEvent = lambda e: self.hide()
        layout.addWidget(close)

    def set_style(self, style: str):
        if style == self._style:
            return
        self._style = style
        # Hide first to avoid visual glitch
        was_visible = self.isVisible()
        self.hide()
        # Destroy all children
        for child in self.findChildren(QWidget):
            child.deleteLater()
        # Rebuild
        self._build()
        if was_visible:
            self._clamp()
            self.show()

    def _available(self):
        return QApplication.primaryScreen().availableGeometry()

    def _snap_default(self):
        avail = self._available()
        self.move(avail.right() - self.width() - 16, avail.bottom() - self.height() - 8)

    def _clamp(self):
        avail = self._available()
        x = max(avail.left(), min(self.x(), avail.right() - self.width()))
        y = max(avail.top(),  min(self.y(), avail.bottom() - self.height()))
        self.move(x, y)

    def update_info(self, name: str, time_str: str, countdown: str):
        self._name = name
        self._time_str = time_str
        self._countdown = countdown
        if hasattr(self, "_name_lbl"):
            self._name_lbl.setText(name)
        if hasattr(self, "_time_lbl"):
            self._time_lbl.setText(time_str)
        if hasattr(self, "_countdown_lbl"):
            self._countdown_lbl.setText(countdown)
        self._clamp()

    def update_accent(self, color: str):
        global ACCENT
        ACCENT = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self._style == "pill":
            p.setBrush(QBrush(QColor(10, 12, 26, 215)))
            p.setPen(QPen(QColor(ACCENT), 0.8))
            p.drawRoundedRect(QRectF(0.5, 0.5, w-1, h-1), 18, 18)

        elif self._style == "card":
            p.setBrush(QBrush(QColor(10, 12, 26, 220)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(0, 0, w, h), 10, 10)
            # Left accent bar
            p.setBrush(QBrush(QColor(ACCENT)))
            p.drawRoundedRect(QRectF(0, 0, 3, h), 2, 2)
            # Border
            p.setPen(QPen(QColor(ACCENT), 0.6))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w-1, h-1), 10, 10)
            # Divider
            p.setPen(QPen(QColor(255, 255, 255, 18), 0.5))
            p.drawLine(12, h//2 + 2, w-10, h//2 + 2)

        elif self._style == "minimal":
            # Just a very subtle background
            p.setBrush(QBrush(QColor(0, 0, 0, 120)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(0, 0, w, h), 6, 6)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = True

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new   = event.globalPosition().toPoint() - self._drag_pos
            avail = self._available()
            x = max(avail.left(), min(new.x(), avail.right()  - self.width()))
            y = max(avail.top(),  min(new.y(), avail.bottom() - self.height()))
            self.move(x, y)

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def contextMenuEvent(self, event):
        self.hide()