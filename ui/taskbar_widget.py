from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen
from PyQt6.QtCore import QRectF

ACCENT = "#1D9E75"


class TaskbarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedHeight(32)
        self.setMinimumWidth(10)
        # Tell Windows this window belongs to the taskbar band
        try:
            import ctypes
            hwnd = int(self.winId())
            # Remove from taskbar switcher, keep in taskbar area
            GWL_EXSTYLE  = -20
            WS_EX_TOOLWINDOW  = 0x00000080
            WS_EX_NOACTIVATE  = 0x08000000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE,
                style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            )
        except Exception:
            pass

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(5)

        moon = QLabel("☽")
        moon.setStyleSheet(f"color: {ACCENT}; font-size: 11px;")
        layout.addWidget(moon)

        self._name_lbl = QLabel("—")
        self._name_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self._name_lbl.setStyleSheet("color: #ffffff;")
        layout.addWidget(self._name_lbl)

        sep = QLabel("·")
        sep.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px;")
        layout.addWidget(sep)

        self._countdown_lbl = QLabel("--:--:--")
        self._countdown_lbl.setFont(QFont("Segoe UI", 9))
        self._countdown_lbl.setStyleSheet(f"color: {ACCENT};")
        layout.addWidget(self._countdown_lbl)

        self._snap()

    def _snap(self):
        screen = QApplication.primaryScreen().availableGeometry()
        full   = QApplication.primaryScreen().geometry()
        taskbar_h = full.height() - screen.height()
        self.adjustSize()
        x = screen.width() - self.width() - 180  # leave space for clock
        y = screen.height() + (taskbar_h - self.height()) // 2
        if taskbar_h < 10:
            y = screen.height() - self.height() - 4
        self.move(x, y)

    def update_info(self, name: str, countdown: str):
        self._name_lbl.setText(name)
        self._countdown_lbl.setText(countdown)
        self.adjustSize()
        self._snap()

    def update_accent(self, color: str):
        global ACCENT
        ACCENT = color
        self._countdown_lbl.setStyleSheet(f"color: {color};")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(15, 15, 25, 180)))
        p.setPen(QPen(QColor(ACCENT), 0.8))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width()-1, self.height()-1), 5, 5)