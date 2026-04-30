from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer, Qt, QTime, QThread, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QLinearGradient
import sys, os

# Add project root to path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from core.prayer_times import get_prayer_times
from core.settings import load, save

# Add ui folder to path for sibling imports
_ui = os.path.join(_root, "ui")
sys.path.insert(0, _ui)

from overlay import OverlayWidget, OverlayStyleDialog
from notification import show_prayer_notification
from tray import TrayIcon
from themes import ThemesDialog, THEMES

# ── Constants ────────────────────────────────────────────────────────────────

ARABIC = {
    "Fajr": "الفجر", "Sunrise": "الشروق",
    "Dhuhr": "الظهر", "Asr": "العصر",
    "Maghrib": "المغرب", "Isha": "العشاء"
}

TRANSLATIONS = {
    "en": {
        "Fajr": "Fajr", "Sunrise": "Sunrise", "Dhuhr": "Dhuhr",
        "Asr": "Asr", "Maghrib": "Maghrib", "Isha": "Isha",
        "settings": "Settings", "city": "City", "country": "Country",
        "madhab": "Madhab", "method": "Method", "save": "Save",
        "refresh": "Refresh", "auto": "Auto-detect location",
        "language": "Language", "display": "Display mode",
        "overlay": "Overlay", "taskbar": "Taskbar",
        "loading": "Loading...", "error": "Error", "themes": "Themes",
        "next_prayer": "Next prayer", "current_prayer": "Current prayer",
    },
    "ru": {
        "Fajr": "Фаджр", "Sunrise": "Восход", "Dhuhr": "Зухр",
        "Asr": "Аср", "Maghrib": "Магриб", "Isha": "Иша",
        "settings": "Настройки", "city": "Город", "country": "Страна",
        "madhab": "Мазхаб", "method": "Метод", "save": "Сохранить",
        "refresh": "Обновить", "auto": "Определить локацию",
        "language": "Язык", "display": "Режим отображения",
        "overlay": "Поверх окон", "taskbar": "Панель задач",
        "loading": "Загрузка...", "error": "Ошибка", "themes": "Темы",
        "next_prayer": "Следующий намаз", "current_prayer": "Текущий намаз",
    },
    "kg": {
        "Fajr": "Бамдат", "Sunrise": "Күн чыгуу", "Dhuhr": "Бешим",
        "Asr": "Аср", "Maghrib": "Шам", "Isha": "Куптан",
        "settings": "Жөндөөлөр", "city": "Шаар", "country": "Өлкө",
        "madhab": "Мазхаб", "method": "Метод", "save": "Сактоо",
        "refresh": "Жаңыртуу", "auto": "Жайгашууну аныктоо",
        "language": "Тил", "display": "Көрсөтүү режими",
        "overlay": "Терезелердин үстүндө", "taskbar": "Тапшырмалар панели",
        "loading": "Жүктөлүүдө...", "error": "Ката", "themes": "Темалар",
        "next_prayer": "Кийинки намаз", "current_prayer": "Учурдагы намаз",
    },
}

DARK_BG      = "#1a1a2e"
DARK_SURFACE = "#16213e"
ACCENT       = "#1D9E75"
TEXT_PRIMARY = "#e0e0e0"
TEXT_MUTED   = "#8888aa"
BORDER       = "#2a2a4a"


class NoScrollComboBox(QComboBox):
    """ComboBox that ignores mouse wheel to prevent accidental changes."""
    def wheelEvent(self, event):
        event.ignore()

APP_STYLE = f"""
QWidget {{
    background: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 13px;
}}
QLineEdit {{
    background: {DARK_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
QComboBox {{
    background: {DARK_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}}
QComboBox:hover {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; background: transparent; }}
QComboBox::down-arrow {{
    image: none; width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {ACCENT};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: #1e1e3a; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; padding: 4px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff; outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px; min-height: 24px;
}}
QPushButton {{
    background: {ACCENT}; color: #ffffff; border: none;
    border-radius: 6px; padding: 8px 14px; font-size: 13px;
}}
QPushButton:hover {{ background: #17b882; }}
QPushButton:pressed {{ background: #0d6b50; }}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{
    background: {DARK_SURFACE}; width: 4px; border-radius: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 2px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QLabel {{ background: transparent; }}
"""


# ── Background worker ─────────────────────────────────────────────────────────

class FetchWorker(QThread):
    done   = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, city, country, madhab, method):
        super().__init__()
        self._city, self._country = city, country
        self._madhab, self._method = madhab, method

    def run(self):
        try:
            times = get_prayer_times(self._city, self._country, self._madhab, self._method)
            self.done.emit(times)
        except Exception as e:
            self.failed.emit(str(e))


# ── Progress bar widget ───────────────────────────────────────────────────────

class PrayerProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self._progress = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_progress(self, value: float):
        self._progress = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QLinearGradient
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background track
        p.setBrush(QBrush(QColor(255, 255, 255, 25)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, 2, 2)

        # Progress fill with gradient
        if self._progress > 0:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(ACCENT))
            grad.setColorAt(1, QColor("#5DCAA5"))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(0, 0, int(w * self._progress), h, 2, 2)


# ── Next prayer hero card ─────────────────────────────────────────────────────

class NextPrayerCard(QFrame):
    """Large card showing current/next prayer with progress bar."""

    def __init__(self, name: str, time_str: str, label: str, lang: str = "en"):
        super().__init__()
        self.setObjectName("heroCard")
        self.setFixedHeight(110)
        self.setStyleSheet(f"""
            QFrame#heroCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d2b1f, stop:1 #0a1e28
                );
                border: 1px solid {ACCENT};
                border-radius: 16px;
            }}
            QFrame#heroCard QLabel {{ background: transparent; border: none; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 12)
        root.setSpacing(4)

        # Top row: label + time
        top = QHBoxLayout()

        left = QVBoxLayout()
        left.setSpacing(2)

        self._name_lbl = QLabel(name)
        self._name_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._name_lbl.setStyleSheet("color: #ffffff;")

        self._label_lbl = QLabel(label)
        self._label_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 11px;")

        left.addWidget(self._name_lbl)
        left.addWidget(self._label_lbl)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        self._time_lbl = QLabel(time_str)
        self._time_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._time_lbl.setStyleSheet(f"color: {ACCENT};")
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.countdown_lbl = QLabel("--:--:--")
        self.countdown_lbl.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px;")
        self.countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        right.addWidget(self._time_lbl)
        right.addWidget(self.countdown_lbl)

        top.addLayout(left)
        top.addStretch()
        top.addLayout(right)
        root.addLayout(top)

        root.addStretch()

        # Progress bar
        self._bar = PrayerProgressBar()
        root.addWidget(self._bar)

    def set_progress(self, value: float):
        self._bar.set_progress(value)


# ── Regular prayer card ───────────────────────────────────────────────────────

class PrayerCard(QFrame):
    def __init__(self, name, time_str, is_next=False, lang="en"):
        super().__init__()
        self.setObjectName("prayerCard")
        self.setFixedHeight(58)

        if is_next:
            style = f"background: #0d2b1f; border-left: 3px solid {ACCENT}; border-top: none; border-right: none; border-bottom: none; border-radius: 0px;"
        else:
            style = f"background: transparent; border: none; border-bottom: 1px solid {BORDER};"

        self.setStyleSheet(f"""
            QFrame#prayerCard {{ {style} }}
            QFrame#prayerCard QLabel {{ background: transparent; border: none; }}
        """)

        h = QHBoxLayout(self)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(1)
        left.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        arabic_lbl = QLabel(ARABIC.get(name, name))
        arabic_lbl.setFont(QFont("Arabic Typesetting, Scheherazade New, Tahoma, Arial", 15))
        arabic_lbl.setStyleSheet(f"color: {'#5DCAA5' if is_next else '#ccccdd'};")

        latin = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(name, name)
        latin_lbl = QLabel(latin)
        latin_lbl.setStyleSheet(f"color: {ACCENT if is_next else TEXT_MUTED}; font-size: 10px;")

        left.addWidget(arabic_lbl)
        left.addWidget(latin_lbl)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        time_lbl = QLabel(time_str)
        time_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium if is_next else QFont.Weight.Normal))
        time_lbl.setStyleSheet(f"color: {'#ffffff' if is_next else TEXT_MUTED};")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(time_lbl)

        if is_next:
            self.countdown_lbl = QLabel("--:--:--")
            self.countdown_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 10px;")
            self.countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            right.addWidget(self.countdown_lbl)

        h.addLayout(left)
        h.addStretch()
        h.addLayout(right)


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QWidget):
    _icon_cache: dict = {}  # class-level cache

    def __init__(self):
        super().__init__()
        self.settings    = load()
        self.times       = {}
        self.next_prayer = None
        self.active_card = None
        self.lang        = self.settings.get("language", "en")
        self._worker     = None

        self.setWindowTitle("Waqt")
        self.setMinimumSize(480, 580)
        self.setStyleSheet(APP_STYLE)

        # Window icon — load once
        _app_icon = os.path.join(_root, "assets", "icons", "app_icon.png")
        if os.path.exists(_app_icon):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(_app_icon))

        self._build_layout()

        # Overlay
        saved_style = self.settings.get("overlay_style", "pill")
        self._overlay = OverlayWidget(style=saved_style)
        if self.settings.get("display_mode", "overlay") == "overlay":
            self._overlay.show()

        # System tray
        self._tray = TrayIcon(self)
        self._tray.show_action.triggered.connect(self._open_window)
        self._tray.times_action.triggered.connect(self._tray._toggle_popup)
        self._tray.overlay_action.triggered.connect(self._toggle_overlay)
        self._tray.quit_action.triggered.connect(QApplication.quit)
        self._tray.activated.connect(self._tray._on_activated)

        # First run tip
        if not self.settings.get("first_run_shown", False):
            QTimer.singleShot(1500, self._show_first_run_tip)

        # Main tick timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

        # Refresh times every 30 min to handle sleep/wake
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(30 * 60 * 1000)

        # Fetch prayer times after UI is shown
        QTimer.singleShot(100, self.refresh_times)

    # ── Translation helper ────────────────────────────────────────────────────

    def _t(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)

    def _make_icon(self, name: str, size: int = 20) -> "QIcon":
        """Load PNG icon with transparent background. Cached."""
        from PyQt6.QtGui import QIcon, QPixmap

        cache_key = f"{name}_{size}"
        if cache_key in MainWindow._icon_cache:
            return MainWindow._icon_cache[cache_key]

        candidates = [
            os.path.join(_root, "assets", "icons", f"{name}.png"),
            os.path.join(os.getcwd(), "assets", "icons", f"{name}.png"),
            os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "assets", "icons", f"{name}.png"
            )),
        ]

        icon = QIcon()
        for path in candidates:
            if os.path.exists(path):
                try:
                    from PIL import Image
                    import tempfile
                    img = Image.open(path).convert("RGBA")
                    img.putdata([
                        (r, g, b, 0) if r > 230 and g > 230 and b > 230 else (r, g, b, a)
                        for r, g, b, a in img.getdata()
                    ])
                    tmp = os.path.join(tempfile.gettempdir(), f"waqt_{name}.png")
                    img.save(tmp)
                    px = QPixmap(tmp).scaled(size, size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)
                    icon = QIcon(px)
                except ImportError:
                    px = QPixmap(path).scaled(size, size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)
                    icon = QIcon(px)
                break

        MainWindow._icon_cache[cache_key] = icon
        return icon

    # ── Build layout (called once, or on language change) ─────────────────────

    def _build_layout(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_settings_panel())
        root.addWidget(self._build_main_panel(), 1)

    def _build_settings_panel(self):
        panel = QWidget()
        panel.setFixedWidth(200)
        panel.setStyleSheet(f"background: {DARK_SURFACE}; border-right: 1px solid {BORDER};")

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 20, 16, 16)
        v.setSpacing(7)

        # Title with settings icon
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)
        settings_icon = QLabel()
        settings_icon.setPixmap(self._make_icon("settings", 18).pixmap(18, 18))
        title_row.addWidget(settings_icon)
        title = QLabel(self._t("settings"))
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff;")
        title_row.addWidget(title)
        title_row.addStretch()
        v.addLayout(title_row)
        v.addSpacing(2)

        # Auto-detect with location icon
        auto_btn = QPushButton(f"  {self._t('auto')}")
        auto_btn.setIcon(self._make_icon("location", 18))
        auto_btn.setIconSize(QSize(18, 18))
        auto_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {ACCENT};
                border: 1px solid {ACCENT}; border-radius: 6px;
                padding: 6px 10px; font-size: 12px; text-align: left;
            }}
            QPushButton:hover {{ background: #0d2b1f; }}
        """)
        auto_btn.clicked.connect(self._auto_detect)
        v.addWidget(auto_btn)

        # City / Country fields
        for label_key, skey in [("city", "city"), ("country", "country")]:
            lbl = QLabel(self._t(label_key).upper())
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
            v.addWidget(lbl)
            le = QLineEdit(self.settings.get(skey, ""))
            le.textChanged.connect(lambda val, k=skey: self.settings.update({k: val}))
            v.addWidget(le)
            setattr(self, f"_le_{skey}", le)

        # Madhab / Method dropdowns
        for label_key, skey, opts in [
            ("madhab", "madhab", ["Hanafi", "Shafi", "Maliki", "Hanbali"]),
            ("method", "method", ["MWL", "ISNA", "Egypt", "Karachi"]),
        ]:
            lbl = QLabel(self._t(label_key).upper())
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
            v.addWidget(lbl)
            cb = NoScrollComboBox()
            cb.addItems(opts)
            cb.setCurrentText(self.settings.get(skey, opts[0]))
            cb.currentTextChanged.connect(lambda val, k=skey: self.settings.update({k: val}))
            v.addWidget(cb)

        # Language
        lbl = QLabel(self._t("language").upper())
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        v.addWidget(lbl)
        lang_cb = NoScrollComboBox()
        lang_cb.addItems(["EN", "RU", "KG"])
        lang_cb.setCurrentText(self.lang.upper())
        lang_cb.currentTextChanged.connect(lambda val: self._change_language(val.lower()))
        v.addWidget(lang_cb)

        # Display mode checkboxes
        v.addSpacing(2)
        from PyQt6.QtWidgets import QCheckBox
        cb_style = f"""
            QCheckBox {{ color: {TEXT_MUTED}; font-size: 12px; spacing: 8px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid {BORDER}; background: {DARK_BG}; }}
            QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
        """
        overlay_cb = QCheckBox("Show overlay")
        overlay_cb.setStyleSheet(cb_style)
        overlay_cb.setChecked(self.settings.get("display_mode", "overlay") == "overlay")
        overlay_cb.stateChanged.connect(lambda s: self._on_display_mode_changed(0 if s else 1))
        v.addWidget(overlay_cb)

        notif_cb = QCheckBox("Prayer notifications")
        notif_cb.setStyleSheet(cb_style)
        notif_cb.setChecked(self.settings.get("notifications", True))
        notif_cb.stateChanged.connect(lambda s: self.settings.update({"notifications": bool(s)}))
        v.addWidget(notif_cb)

        # Overlay style button — moon icon
        ol_btn = QPushButton(f"  Overlay style")
        ol_btn.setIcon(self._make_icon("moon", 18))
        ol_btn.setIconSize(QSize(18, 18))
        ol_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {ACCENT};
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 6px 10px; font-size: 12px; text-align: left;
            }}
            QPushButton:hover {{ border-color: {ACCENT}; }}
        """)
        ol_btn.clicked.connect(self._open_overlay_style)
        v.addWidget(ol_btn)

        # Themes button — palette icon
        themes_btn = QPushButton(f"  {self._t('themes')}")
        themes_btn.setIcon(self._make_icon("palette", 18))
        themes_btn.setIconSize(QSize(18, 18))
        themes_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {ACCENT};
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 6px 10px; font-size: 12px; text-align: left;
            }}
            QPushButton:hover {{ border-color: {ACCENT}; }}
        """)
        themes_btn.clicked.connect(self._open_themes)
        v.addWidget(themes_btn)

        v.addStretch()

        # Divider
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BORDER}; max-height: 1px; border: none;")
        v.addWidget(sep)
        v.addSpacing(6)

        # Save + Refresh — text only, no icons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        save_btn = QPushButton(self._t("save"))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: #ffffff; border: none;
                border-radius: 6px; padding: 8px 0; font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{ background: #17b882; }}
            QPushButton:pressed {{ background: #0d6b50; }}
        """)
        save_btn.clicked.connect(self._on_save)

        ref_btn = QPushButton(self._t("refresh"))
        ref_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {ACCENT};
                border: 1px solid {ACCENT}; border-radius: 6px;
                padding: 8px 0; font-size: 13px;
            }}
            QPushButton:hover {{ background: #0d2b1f; }}
        """)
        ref_btn.clicked.connect(self.refresh_times)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(ref_btn)
        v.addLayout(btn_row)

        return panel

    def _build_main_panel(self):
        w = QWidget()
        w.setStyleSheet(f"background: {DARK_BG};")
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 20, 20, 16)
        v.setSpacing(6)

        # City large + country small on same line
        loc_row = QHBoxLayout()
        loc_row.setSpacing(8)
        self._city_lbl = QLabel()
        self._city_lbl.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 700;")
        self._country_lbl = QLabel()
        self._country_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px;")
        self._country_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        loc_row.addWidget(self._city_lbl)
        loc_row.addWidget(self._country_lbl)
        loc_row.addStretch()
        v.addLayout(loc_row)

        self._date_lbl = QLabel()
        self._date_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        v.addWidget(self._date_lbl)

        v.addSpacing(6)

        # Hero card (next prayer)
        self._hero_card = NextPrayerCard("—", "--:--", "Loading...", self.lang)
        v.addWidget(self._hero_card)

        v.addSpacing(4)

        # Prayer list
        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(0)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setWidget(self._cards_widget)
        v.addWidget(scroll, 1)

        # Bottom info bar
        self._info_lbl = QLabel()
        self._info_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        v.addWidget(self._info_lbl)

        self._loading_lbl = QLabel(self._t("loading"))
        self._loading_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl.hide()
        v.addWidget(self._loading_lbl)

        return w

    # ── Fetch (non-blocking) ──────────────────────────────────────────────────

    def refresh_times(self):
        if self._worker and self._worker.isRunning():
            return

        # Try cache first for instant display
        from core.settings import get_cached_times
        cached = get_cached_times(self.settings)
        if cached and not self.times:
            self._on_times_ready(cached)

        self._loading_lbl.show()
        self._worker = FetchWorker(
            self.settings.get("city", "Bishkek"),
            self.settings.get("country", "Kyrgyzstan"),
            self.settings.get("madhab", "Hanafi"),
            self.settings.get("method", "MWL"),
        )
        self._worker.done.connect(self._on_times_ready)
        self._worker.failed.connect(self._on_fetch_error)
        self._worker.start()

    def _on_times_ready(self, times):
        self._loading_lbl.hide()
        self.times = times

        # Save to cache for offline use
        from core.settings import save_cached_times
        save_cached_times(self.settings, times)

        city    = self.settings.get("city", "")
        country = self.settings.get("country", "")
        self._city_lbl.setText(city)
        self._country_lbl.setText(country)

        # Localized date
        self._date_lbl.setText(self._localized_date())

        madhab = self.settings.get("madhab", "Hanafi")
        method = self.settings.get("method", "MWL")
        self._info_lbl.setText(f"{madhab}  ·  {method}")

        self._render_prayers()
        if hasattr(self, "_tray"):
            lang_names = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])
            self._tray.set_times(times, self.next_prayer or "", lang_names)

    def _localized_date(self) -> str:
        """Return today's date in the current language."""
        from datetime import date
        today = date.today()
        lang  = self.lang

        days_en = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        days_ru = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
        days_kg = ["Дүйшөмбү","Шейшемби","Шаршемби","Бейшемби","Жума","Ишемби","Жекшемби"]

        months_ru = ["","января","февраля","марта","апреля","мая","июня",
                     "июля","августа","сентября","октября","ноября","декабря"]
        months_kg = ["","январь","февраль","март","апрель","май","июнь",
                     "июль","август","сентябрь","октябрь","ноябрь","декабрь"]

        wd = today.weekday()
        d, m, y = today.day, today.month, today.year

        if lang == "ru":
            return f"{days_ru[wd]}, {d} {months_ru[m]} {y}"
        elif lang == "kg":
            return f"{days_kg[wd]}, {d} {months_kg[m]} {y}"
        else:
            return today.strftime("%A, %d %B %Y")

    def _on_fetch_error(self, msg):
        self._loading_lbl.hide()
        # Try offline cache
        from core.settings import get_cached_times
        cached = get_cached_times(self.settings)
        if cached:
            self.times = cached
            self._city_lbl.setText(self.settings.get("city", ""))
            self._country_lbl.setText(self.settings.get("country", ""))
            self._date_lbl.setText(self._localized_date())
            madhab = self.settings.get("madhab", "Hanafi")
            method = self.settings.get("method", "MWL")
            self._info_lbl.setText(f"{madhab}  ·  {method}  ·  📵 offline")
            self._render_prayers()
        else:
            QMessageBox.warning(self, self._t("error"),
                f"No internet connection and no cached data.\n\n{msg}")

    # ── Render cards ──────────────────────────────────────────────────────────

    def _render_prayers(self):
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        now = QTime.currentTime()
        self.next_prayer = self._get_next_prayer(now)
        self.active_card = None
        lang_names = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        # Update hero card
        current = self._get_current_prayer(now)
        if current and current in self.times:
            hero_name  = lang_names.get(current, current)
            hero_time  = self.times[current]
            hero_label = lang_names.get("current_prayer", "Current prayer")
        else:
            hero_name  = lang_names.get(self.next_prayer, self.next_prayer)
            hero_time  = self.times.get(self.next_prayer, "--:--")
            hero_label = lang_names.get("next_prayer", "Next prayer")

        if hasattr(self, "_hero_card"):
            self._hero_card._name_lbl.setText(hero_name)
            self._hero_card._time_lbl.setText(hero_time)
            self._hero_card._label_lbl.setText(hero_label)
            self.active_card = self._hero_card

        # Calculate progress bar (how far through current prayer period)
        if current and current in self.times:
            prayer_list = [
                (n, t) for n, t in self.times.items() if n != "Sunrise"
            ]
            for i, (n, t) in enumerate(prayer_list):
                if n == current and i + 1 < len(prayer_list):
                    t_start = QTime.fromString(t, "HH:mm")
                    t_end   = QTime.fromString(prayer_list[i+1][1], "HH:mm")
                    total   = t_start.secsTo(t_end)
                    elapsed = t_start.secsTo(now)
                    if total > 0:
                        progress = elapsed / total
                        if hasattr(self, "_hero_card"):
                            self._hero_card.set_progress(progress)
                    break
        else:
            if hasattr(self, "_hero_card"):
                self._hero_card.set_progress(0)

        # Regular cards for all prayers
        for name, time_str in self.times.items():
            is_next = (name == self.next_prayer)
            card = PrayerCard(name, time_str, is_next, lang=self.lang)
            self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()

    def _get_current_prayer(self, now: QTime) -> str | None:
        """
        Returns prayer currently active.
        Logic:
        - Fajr is active from Fajr until Sunrise
        - Dhuhr/Asr/Maghrib/Isha active from their start until next one
        - Between Sunrise and Dhuhr — no current prayer (return None)
        - After Isha — Isha is active until midnight
        """
        times = self.times
        if not times:
            return None

        fajr    = QTime.fromString(times.get("Fajr",    "00:00"), "HH:mm")
        sunrise = QTime.fromString(times.get("Sunrise", "00:00"), "HH:mm")

        # Between midnight and Fajr — no prayer
        if now < fajr:
            return None

        # Fajr time → only until Sunrise
        if fajr <= now < sunrise:
            return "Fajr"

        # After Sunrise — skip to next prayer
        skip = {"Sunrise", "Fajr"}
        prayer_list = [(n, t) for n, t in times.items() if n not in skip]

        for i in range(len(prayer_list) - 1):
            name, time_str = prayer_list[i]
            _, next_time   = prayer_list[i + 1]
            t_start = QTime.fromString(time_str, "HH:mm")
            t_end   = QTime.fromString(next_time, "HH:mm")
            if t_start <= now < t_end:
                return name

        # After Isha
        if prayer_list:
            last_name, last_time = prayer_list[-1]
            t_last = QTime.fromString(last_time, "HH:mm")
            if now >= t_last:
                return last_name

        return None

    def _get_next_prayer(self, now: QTime) -> str:
        """Returns the next prayer after current time. Skips Sunrise."""
        skip = {"Sunrise"}
        for name, time_str in self.times.items():
            if name in skip:
                continue
            t = QTime.fromString(time_str, "HH:mm")
            if t > now:
                return name
        return "Fajr"

    def _auto_refresh(self):
        """Called every 30 min — handles laptop sleep/wake."""
        self.refresh_times()

    # ── Countdown tick ────────────────────────────────────────────────────────

    def _tick(self):
        if not self.active_card or not hasattr(self.active_card, "countdown_lbl"):
            return
        if not self.next_prayer or self.next_prayer not in self.times:
            return

        now  = QTime.currentTime()
        t    = QTime.fromString(self.times[self.next_prayer], "HH:mm")
        secs = now.secsTo(t)

        # After Isha — next Fajr is tomorrow
        if secs < 0:
            secs += 86400

        # Prayer time just arrived
        if secs == 0:
            if self.settings.get("notifications", True):
                lang_names = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])
                name     = lang_names.get(self.next_prayer, self.next_prayer)
                time_str = self.times[self.next_prayer]
                notif = show_prayer_notification(name, time_str)
                notif.dismissed.connect(lambda: None)
                self._last_notif = notif
            self._render_prayers()
            return

        h, rem = divmod(secs, 3600)
        m, s   = divmod(rem, 60)
        countdown = f"in {h:02d}:{m:02d}:{s:02d}"

        # Update hero card countdown
        if hasattr(self, "_hero_card") and hasattr(self._hero_card, "countdown_lbl"):
            self._hero_card.countdown_lbl.setText(countdown)

        # Update progress bar
        if hasattr(self, "_hero_card") and self.times:
            current = self._get_current_prayer(now)
            if current and current in self.times:
                prayer_list = [(n, t) for n, t in self.times.items() if n != "Sunrise"]
                for i, (n, t) in enumerate(prayer_list):
                    if n == current and i + 1 < len(prayer_list):
                        t_start = QTime.fromString(t, "HH:mm")
                        t_end   = QTime.fromString(prayer_list[i+1][1], "HH:mm")
                        total   = t_start.secsTo(t_end)
                        elapsed = t_start.secsTo(now)
                        if total > 0:
                            self._hero_card.set_progress(elapsed / total)
                        break

        lang_names = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        # Tray and overlay: show CURRENT prayer if active, else next
        current = self._get_current_prayer(now)
        if current and current in self.times:
            # Show current prayer + time remaining until next
            cur_name     = lang_names.get(current, current)
            cur_time_str = self.times[current]
            # Time remaining = secs until next prayer
            h2, rem2 = divmod(secs, 3600)
            m2, s2   = divmod(rem2, 60)
            remaining = f"{h2:02d}:{m2:02d}"  # shorter format for tray
            tray_label = cur_name
            tray_count = remaining
            overlay_name = cur_name
            overlay_time = cur_time_str
            overlay_count = countdown
        else:
            # Between Isha and Fajr — show next Fajr
            tray_label   = lang_names.get(self.next_prayer, self.next_prayer)
            tray_count   = f"{h:02d}:{m:02d}"
            overlay_name = tray_label
            overlay_time = self.times[self.next_prayer]
            overlay_count = countdown

        if hasattr(self, "_overlay"):
            self._overlay.update_info(overlay_name, overlay_time, overlay_count)
        if hasattr(self, "_tray"):
            self._tray.update_prayer(tray_label, tray_count)

    def _on_display_mode_changed(self, index: int):
        mode = "overlay" if index == 0 else "taskbar"
        self.settings["display_mode"] = mode
        if hasattr(self, "_overlay"):
            self._overlay.show() if mode == "overlay" else self._overlay.hide()

    def _open_window(self):
        self.show()
        self.raise_()
        self.activateWindow()
        # Restore from minimized if needed
        if self.isMinimized():
            self.showNormal()

    def _show_first_run_tip(self):
        if hasattr(self, "_tray"):
            self._tray.showMessage(
                "Waqt is running",
                "Click the icon to open settings.\nPrayer times are shown in the tray.",
                self._tray.MessageIcon.Information,
                4000
            )
        self.settings["first_run_shown"] = True
        save(self.settings)

    def _toggle_overlay(self):
        if hasattr(self, "_overlay"):
            if self._overlay.isVisible():
                self._overlay.hide()
            else:
                self._overlay.show()

    def _open_overlay_style(self):
        current = self.settings.get("overlay_style", "card")
        dlg = OverlayStyleDialog(current_style=current, parent=self)
        dlg.style_chosen.connect(self._apply_overlay_style)
        dlg.exec()

    def _apply_overlay_style(self, style: str):
        self.settings["overlay_style"] = style
        save(self.settings)
        if hasattr(self, "_overlay"):
            was_visible = self._overlay.isVisible()
            self._overlay.set_style(style)
            if was_visible:
                self._overlay.show()

    def _open_themes(self):
        current = self.settings.get("theme_name", "Dark Green")
        dlg = ThemesDialog(current_theme=current, parent=self)
        dlg.theme_changed.connect(self._apply_theme)
        dlg.exec()

    def _apply_theme(self, colors: dict):
        # Find theme name
        for name, c in THEMES.items():
            if c == colors:
                self.settings["theme_name"] = name
                break
        save(self.settings)
        # Rebuild style with new colors
        global DARK_BG, DARK_SURFACE, ACCENT, TEXT_PRIMARY, BORDER, APP_STYLE
        DARK_BG      = colors["bg"]
        DARK_SURFACE = colors["surface"]
        ACCENT       = colors["accent"]
        TEXT_PRIMARY = colors["text"]
        BORDER       = colors["border"]
        APP_STYLE = f"""
QWidget {{
    background: {DARK_BG}; color: {TEXT_PRIMARY};
    font-family: Segoe UI, Arial, sans-serif; font-size: 13px;
}}
QLineEdit {{
    background: {DARK_BG}; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 10px;
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
QComboBox {{
    background: {DARK_BG}; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 6px 10px; min-height: 20px;
}}
QComboBox:hover {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; background: transparent; }}
QComboBox::down-arrow {{
    image: none; width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 6px solid {ACCENT}; margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: {DARK_SURFACE}; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; padding: 4px;
    selection-background-color: {ACCENT}; selection-color: #ffffff; outline: none;
}}
QComboBox QAbstractItemView::item {{ padding: 6px 10px; min-height: 24px; }}
QPushButton {{
    background: {ACCENT}; color: #ffffff; border: none;
    border-radius: 6px; padding: 8px 14px; font-size: 13px;
}}
QPushButton:hover {{ background: {ACCENT}dd; }}
QPushButton:pressed {{ background: {ACCENT}99; }}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{
    background: {DARK_SURFACE}; width: 4px; border-radius: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 2px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QLabel {{ background: transparent; }}
"""
        self.setStyleSheet(APP_STYLE)
        # Rebuild layout with new colors
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)
        self._build_layout()
        if self.times:
            self._render_prayers()
            self._loc_lbl.setText(
                f"{self.settings.get('city','')} , {self.settings.get('country','')}"
            )
            from datetime import date
            self._date_lbl.setText(date.today().strftime("%d %B %Y"))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_save(self):
        save(self.settings)
        self.refresh_times()

    def _auto_detect(self):
        try:
            from core.location import get_location_by_ip
            loc = get_location_by_ip()
            self.settings["city"]    = loc["city"]
            self.settings["country"] = loc["country"]
            if hasattr(self, "_le_city"):
                self._le_city.setText(loc["city"])
            if hasattr(self, "_le_country"):
                self._le_country.setText(loc["country"])
            save(self.settings)
            self.refresh_times()
        except Exception as e:
            QMessageBox.warning(self, self._t("error"), str(e))

    def _change_language(self, lang):
        if lang == self.lang:
            return
        self.lang = lang
        self.settings["language"] = lang
        save(self.settings)
        # Clean rebuild
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)
        self._build_layout()
        if self.times:
            self._render_prayers()
            self._city_lbl.setText(self.settings.get("city", ""))
            self._country_lbl.setText(self.settings.get("country", ""))
            from datetime import date
            self._date_lbl.setText(date.today().strftime("%A, %d %B %Y"))