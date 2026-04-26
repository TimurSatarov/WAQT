from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen

THEMES = {
    # 14. Сила знаний — тёмно-синий + золото
    "Knowledge": {
        "bg": "#1a1f3a", "surface": "#252b4a",
        "accent": "#e8b84b", "text": "#f0ead6", "border": "#333860",
    },
    # 10. Солнечный городок — тёмный + оранжево-коралловый
    "Sunny Town": {
        "bg": "#1a1210", "surface": "#2a1e1a",
        "accent": "#e8693a", "text": "#faf0e8", "border": "#3d2820",
    },
    # 20. Арктический рассвет — тёмно-синий + ледяной голубой
    "Arctic Dawn": {
        "bg": "#0d1b2e", "surface": "#142338",
        "accent": "#5bc8e8", "text": "#ddf0f8", "border": "#1a3050",
    },
    # 22. Яркая Исландия — тёмный серо-синий + мятный
    "Iceland": {
        "bg": "#111820", "surface": "#192230",
        "accent": "#38d9a9", "text": "#e0f5ef", "border": "#1e3040",
    },
    # 34. От заката до сумерек — тёмный + пурпурно-розовый
    "Sunset": {
        "bg": "#1a0f1e", "surface": "#26162e",
        "accent": "#c868e8", "text": "#f0ddf8", "border": "#3a1e4a",
    },
    # 37. Янтарь и лазурь — тёмный + янтарно-бирюзовый
    "Amber & Azure": {
        "bg": "#0f1a1a", "surface": "#162828",
        "accent": "#e8a030", "text": "#faf5e8", "border": "#1e3838",
    },
    # Оригинальная тема (по умолчанию)
    "Dark Green": {
        "bg": "#1a1a2e", "surface": "#16213e",
        "accent": "#1D9E75", "text": "#e0e0e0", "border": "#2a2a4a",
    },
    # Полночь
    "Midnight": {
        "bg": "#0d1b2a", "surface": "#1b2838",
        "accent": "#4a9eff", "text": "#dce8f5", "border": "#1e3a5f",
    },
}


class ThemeCard(QFrame):
    selected = pyqtSignal(str)

    def __init__(self, name: str, colors: dict, is_active: bool = False):
        super().__init__()
        self._name   = name
        self._colors = colors
        self._active = is_active
        self.setFixedSize(140, 96)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        border = f"2px solid {self._colors['accent']}" if self._active else \
                 f"1px solid {self._colors['border']}"
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._colors['bg']};
                border: {border};
                border-radius: 10px;
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Surface preview rect
        p.setBrush(QBrush(QColor(self._colors["surface"])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(10, 10, w - 20, 42, 6, 6)

        # Mini card inside preview
        p.setBrush(QBrush(QColor(self._colors["bg"])))
        p.drawRoundedRect(14, 14, 40, 28, 4, 4)

        # Accent bar inside mini card
        p.setBrush(QBrush(QColor(self._colors["accent"])))
        p.drawRoundedRect(16, 34, 24, 4, 2, 2)

        # Accent pill bottom
        p.setBrush(QBrush(QColor(self._colors["accent"])))
        p.drawRoundedRect(10, 58, 56, 8, 4, 4)

        # Text strip
        p.setBrush(QBrush(QColor(self._colors["text"])))
        p.setOpacity(0.35)
        p.drawRoundedRect(72, 58, w - 82, 8, 4, 4)
        p.setOpacity(1.0)

        # Name
        p.setPen(QColor(self._colors["text"]))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(10, h - 8, self._name)

        # Active check circle
        if self._active:
            p.setBrush(QBrush(QColor(self._colors["accent"])))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(w - 22, 8, 14, 14)
            p.setPen(QPen(QColor("#ffffff"), 1.8))
            p.drawLine(w - 18, 15, w - 15, 18)
            p.drawLine(w - 15, 18, w - 10, 12)

    def mousePressEvent(self, event):
        self.selected.emit(self._name)

    def set_active(self, active: bool):
        self._active = active
        self._update_style()
        self.update()


class ThemesDialog(QDialog):
    theme_changed = pyqtSignal(dict)

    def __init__(self, current_theme: str = "Dark Green", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Themes")
        self.setModal(True)
        self.setFixedSize(480, 380)
        self._current = current_theme
        self._cards   = {}

        self.setStyleSheet("""
            QDialog { background: #1a1a2e; }
            QLabel { color: #e0e0e0; background: transparent; }
            QPushButton {
                background: #1D9E75; color: #ffffff; border: none;
                border-radius: 6px; padding: 8px 20px; font-size: 13px;
            }
            QPushButton:hover { background: #17b882; }
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        title = QLabel("Choose theme")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        v.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        for i, (name, colors) in enumerate(THEMES.items()):
            card = ThemeCard(name, colors, is_active=(name == self._current))
            card.selected.connect(self._select)
            self._cards[name] = card
            grid.addWidget(card, i // 4, i % 4)  # 4 columns for 8 themes

        v.addLayout(grid)
        v.addStretch()

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply)
        v.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _select(self, name: str):
        if self._current in self._cards:
            self._cards[self._current].set_active(False)
        self._current = name
        self._cards[name].set_active(True)

    def _apply(self):
        self.theme_changed.emit(THEMES[self._current])
        self.accept()