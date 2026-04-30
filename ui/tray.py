from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QApplication
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QFont,
    QColor, QBrush, QPen, QPainterPath
)
from PyQt6.QtCore import Qt, QRectF, QPointF

ACCENT = "#1D9E75"
BG     = "#16213e"
BORDER = "#2a2a4a"
TEXT   = "#e0e0e0"
MUTED  = "#8888aa"


def _crescent_path(sz: float) -> QPainterPath:
    """
    Draws a proper crescent moon using two circles:
    outer circle minus inner offset circle = crescent shape.
    """
    path = QPainterPath()
    cx, cy = sz / 2, sz / 2
    r_outer = sz * 0.42

    # Outer circle (full moon shape)
    outer = QPainterPath()
    outer.addEllipse(QPointF(cx, cy), r_outer, r_outer)

    # Inner circle offset to the right to cut out crescent
    r_inner = sz * 0.34
    offset  = sz * 0.18
    inner = QPainterPath()
    inner.addEllipse(QPointF(cx + offset, cy - offset * 0.3), r_inner, r_inner)

    # Crescent = outer minus inner
    return outer.subtracted(inner)


def _make_default_icon(accent: str = ACCENT) -> QIcon:
    """Crescent moon icon for initial tray state."""
    sz = 128
    px = QPixmap(sz, sz)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    crescent = _crescent_path(sz)
    p.setBrush(QBrush(QColor(accent)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(crescent)

    p.end()
    return QIcon(px)


def _make_text_icon(name: str, countdown: str, accent: str = ACCENT) -> QIcon:
    """
    Small crescent + prayer name on top, countdown below.
    All rendered at 128x128 for crisp downscaling.
    """
    sz = 128
    px = QPixmap(sz, sz)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Small crescent top-left
    moon_sz = sz * 0.35
    moon_path = QPainterPath()
    outer = QPainterPath()
    outer.addEllipse(QPointF(moon_sz * 0.5, moon_sz * 0.5), moon_sz * 0.42, moon_sz * 0.42)
    inner = QPainterPath()
    inner.addEllipse(QPointF(moon_sz * 0.5 + moon_sz * 0.18,
                              moon_sz * 0.5 - moon_sz * 0.05),
                     moon_sz * 0.32, moon_sz * 0.32)
    moon_path = outer.subtracted(inner)
    p.setBrush(QBrush(QColor(accent)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(moon_path)

    # Prayer name — bold, accent color
    p.setPen(QColor(accent))
    p.setFont(QFont("Segoe UI", 42, QFont.Weight.Black))
    p.drawText(QRectF(0, sz * 0.25, sz, sz * 0.4),
               Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
               name[:4])

    # Countdown — white, smaller
    p.setPen(QColor("#ffffff"))
    p.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
    p.drawText(QRectF(0, sz * 0.63, sz, sz * 0.37),
               Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
               countdown)

    p.end()
    return QIcon(px)


# ── Prayer popup ──────────────────────────────────────────────────────────────

class PrayerPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QWidget()
        self._card.setObjectName("card")
        self._card.setStyleSheet(f"""
            QWidget#card {{
                background: {BG};
                border: 1px solid {ACCENT};
                border-radius: 12px;
            }}
            QWidget#card QLabel {{ background: transparent; border: none; }}
        """)

        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(0)

        header = QLabel("Prayer times")
        header.setStyleSheet(f"color: {MUTED}; font-size: 10px; letter-spacing: 0.08em;")
        inner.addWidget(header)
        inner.addSpacing(8)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(0)
        inner.addLayout(self._rows_layout)

        outer.addWidget(self._card)

    def update_times(self, times, next_prayer, lang_names, countdown):
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = list(times.items())
        for i, (name, time_str) in enumerate(items):
            is_next = (name == next_prayer)
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 6, 0, 6)

            display = lang_names.get(name, name)
            nl = QLabel(display)
            nl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium if is_next else QFont.Weight.Normal))
            nl.setStyleSheet(f"color: {'#5DCAA5' if is_next else TEXT};")

            vl = QLabel(countdown if is_next else time_str)
            vl.setStyleSheet(f"color: {ACCENT if is_next else MUTED}; font-size: 11px;" +
                             (" font-weight: 500;" if is_next else ""))
            vl.setAlignment(Qt.AlignmentFlag.AlignRight)

            h.addWidget(nl); h.addStretch(); h.addWidget(vl)

            wrap = QWidget()
            wrap.setStyleSheet("background: transparent;")
            wv = QVBoxLayout(wrap)
            wv.setContentsMargins(0, 0, 0, 0)
            wv.setSpacing(0)
            wv.addWidget(row)
            if i < len(items) - 1:
                sep = QWidget()
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background: {BORDER};")
                wv.addWidget(sep)

            self._rows_layout.addWidget(wrap)

        self._card.adjustSize()
        self.adjustSize()

    def show_near_tray(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        self.move(screen.right() - self.width() - 12, screen.bottom() - self.height() - 8)
        self.show()
        self.raise_()

    def leaveEvent(self, event):
        self.hide()


# ── Tray ──────────────────────────────────────────────────────────────────────

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(_make_default_icon(), parent)
        self.setToolTip("Waqt")

        self._popup      = PrayerPopup()
        self._times      = {}
        self._next       = ""
        self._lang_names = {}
        self._countdown  = "--:--"

        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background: {BG}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 4px; font-family: Segoe UI; font-size: 13px;
            }}
            QMenu::item {{ padding: 7px 20px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {ACCENT}; color: #ffffff; }}
            QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
        """)

        self._info_action    = menu.addAction("Waqt")
        self._info_action.setEnabled(False)
        menu.addSeparator()
        self._show_action    = menu.addAction("Open Waqt")
        self._times_action   = menu.addAction("Prayer times")
        self._overlay_action = menu.addAction("Show overlay")
        menu.addSeparator()
        self._quit_action    = menu.addAction("Quit")

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)
        self.show()

    def update_prayer(self, name: str, countdown: str):
        self._countdown = countdown
        self._next      = name

        short = countdown.replace("in ", "")
        parts = short.split(":")
        if len(parts) == 3:
            h = int(parts[0])
            short = f"{h}:{parts[1]}" if h > 0 else f":{parts[1]}"

        self.setIcon(_make_text_icon(name, short))
        self.setToolTip(f"Waqt  ·  {name}  {countdown}")
        self._info_action.setText(f"{name}  ·  {countdown}")

        if self._popup.isVisible() and self._times:
            self._popup.update_times(self._times, self._next, self._lang_names, countdown)

    def set_times(self, times, next_prayer, lang_names):
        self._times      = times
        self._next       = next_prayer
        self._lang_names = lang_names

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single left click → toggle popup
            self._toggle_popup()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click → open main window (handled via show_action)
            pass

    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
        else:
            if self._times:
                self._popup.update_times(
                    self._times, self._next, self._lang_names, self._countdown
                )
            self._popup.show_near_tray()

    @property
    def show_action(self):      return self._show_action
    @property
    def times_action(self):     return self._times_action
    @property
    def overlay_action(self):   return self._overlay_action
    @property
    def quit_action(self):      return self._quit_action

    def update_prayer(self, name: str, countdown: str):
        self._countdown = countdown
        self._next      = name

        # Show only H:MM in tray — no seconds, no "in"
        short = countdown.replace("in ", "")
        parts = short.split(":")
        if len(parts) == 3:
            h = int(parts[0])
            short = f"{h}:{parts[1]}" if h > 0 else f":{parts[1]}"

        self.setIcon(_make_text_icon(name, short))
        self.setToolTip(f"Waqt  ·  {name}  {countdown}")
        self._info_action.setText(f"{name}  ·  {countdown}")

        if self._popup.isVisible() and self._times:
            self._popup.update_times(self._times, self._next, self._lang_names, countdown)

    def set_times(self, times, next_prayer, lang_names):
        self._times      = times
        self._next       = next_prayer
        self._lang_names = lang_names

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click → open main window
            # (popup accessible via right-click menu)
            pass  # handled by show_action signal in main_window
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            if self._popup.isVisible():
                self._popup.hide()
            else:
                if self._times:
                    self._popup.update_times(self._times, self._next, self._lang_names, self._countdown)
                self._popup.show_near_tray()

    @property
    def show_action(self):      return self._show_action
    @property
    def overlay_action(self):   return self._overlay_action
    @property
    def quit_action(self):      return self._quit_action
    