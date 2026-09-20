
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFrame, QStackedWidget,
    QFileDialog, QMessageBox, QSizePolicy, QScrollArea, QProgressBar,
    QComboBox, QLineEdit, QCheckBox, QSlider, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)

from sonar_integration import run_detection, DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH


class DetectionWorker(QThread):
    """Runs the NLM -> YOLO11s sonar pipeline off the GUI thread so the app
    doesn't freeze while a detection is in progress."""

    finished_ok = Signal(dict)     # emits the pipeline's result dict
    finished_err = Signal(str)     # emits an error message

    def __init__(self, model_path, classes_path, image_path, confidence):
        super().__init__()
        self.model_path = model_path
        self.classes_path = classes_path
        self.image_path = image_path
        self.confidence = confidence

    def run(self):
        try:
            results = run_detection(
                self.image_path,
                model_path=self.model_path,
                classes_path=self.classes_path,
                confidence=self.confidence,
            )
            self.finished_ok.emit(results)
        except Exception as e:
            self.finished_err.emit(f"{type(e).__name__}: {e}")


# ============================================================
# MarineVision UI
# Redesigned to prevent clipping/overlap and closely match
# the supplied MarineVision prototype.
# ============================================================

NAVY = "#100F3F"
NAVY_2 = "#15144A"
NAVY_3 = "#24205F"
BG = "#F7F4EE"
WHITE = "#FFFFFF"
TEXT = "#141A3D"
MUTED = "#747795"
BORDER = "#D9D8E2"
PURPLE = "#3430A8"
PURPLE_LIGHT = "#E9E8FA"
ORANGE = "#F58A27"
ORANGE_DARK = "#DB7518"
GREEN = "#2E9B72"
BLUE = "#315FAF"

# Change this one value to switch the font used across the whole app.
# Falls back silently to a system default if the font isn't installed.
FONT_FAMILY = "Segoe UI"


def label(text, size=14, color=TEXT, bold=False, object_name=None):
    w = QLabel(text)
    if object_name:
        w.setObjectName(object_name)
    f = QFont(FONT_FAMILY)
    f.setPointSize(size)
    f.setWeight(QFont.Bold if bold else QFont.Normal)
    w.setFont(f)
    w.setStyleSheet(f"color:{color}; background:transparent;")
    return w


def make_button(text, kind="secondary", height=46):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setFixedHeight(height)
    b.setFont(QFont(FONT_FAMILY, 11))
    b.setStyleSheet({
        "primary": f"""
            QPushButton {{
                background:{ORANGE}; color:white; border:none;
                border-radius:7px; padding:0 22px; font-weight:700;
            }}
            QPushButton:hover {{ background:{ORANGE_DARK}; }}
        """,
        "secondary": f"""
            QPushButton {{
                background:white; color:{TEXT}; border:1px solid {BORDER};
                border-radius:7px; padding:0 20px; font-weight:600;
            }}
            QPushButton:hover {{ background:{PURPLE_LIGHT}; border-color:#B8B5DE; }}
        """,
        "ghost": """
            QPushButton {
                background:transparent; color:white;
                border:1px solid rgba(255,255,255,80);
                border-radius:7px; padding:0 20px; font-weight:600;
            }
            QPushButton:hover { background:rgba(255,255,255,18); }
        """,
        "nav": """
            QPushButton {
                background:transparent; color:#BDBBD9;
                border:none; border-radius:6px;
                padding:0 12px; font-size:15px;
            }
            QPushButton:hover { color:white; background:rgba(255,255,255,14); }
            QPushButton[active="true"] {
                color:white; background:#302C75;
            }
        """
    }[kind])
    return b


class HeroBackground(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(405)
        self.setMaximumHeight(430)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = self.rect()
        g = QLinearGradient(0, 0, r.width(), r.height())
        g.setColorAt(0, QColor(NAVY))
        g.setColorAt(0.65, QColor(NAVY_2))
        g.setColorAt(1, QColor("#211F5D"))
        p.fillRect(r, g)

        # Subtle sonar rings on the right.
        cx = r.width() - 160
        cy = 145
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        for radius in (70, 110, 150, 190):
            p.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        p.setPen(QPen(QColor(255, 255, 255, 10), 1))
        p.drawLine(cx - 205, cy, cx + 205, cy)
        p.drawLine(cx, cy - 205, cx, cy + 205)
        p.end()


class StatBlock(QFrame):
    def __init__(self, value, title):
        super().__init__()
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(3)

        v = label(value, 25, WHITE, True)
        t = label(title, 11, "#B8B7D2")
        lay.addWidget(v)
        lay.addWidget(t)


class CapabilityCard(QFrame):
    def __init__(self, icon, title, description, accent):
        super().__init__()
        self.setMinimumHeight(178)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setStyleSheet("QFrame { background:transparent; border:none; }")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)

        icon_box = QLabel(icon)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(38, 38)
        icon_box.setStyleSheet(
            f"background:{accent}18; color:{accent}; border-radius:9px; "
            "font-size:18px; font-weight:700;"
        )

        title_w = label(title, 16, TEXT, True)
        title_w.setMinimumHeight(22)

        body = label(description, 12, MUTED)
        body.setWordWrap(True)
        body.setMinimumHeight(54)

        lay.addWidget(icon_box, 0, Qt.AlignLeft)
        lay.addWidget(title_w)
        lay.addWidget(body)
        lay.addStretch(1)


class MissionRow(QFrame):
    def __init__(self, name, date, status, detections, show_divider=True):
        super().__init__()
        self.setObjectName("missionRow")
        self.setMinimumHeight(62)
        divider_css = f"border-bottom:1px solid {BORDER};" if show_divider else "border:none;"
        self.setStyleSheet(f"""
            QFrame#missionRow {{
                background:transparent;
                {divider_css}
                border-radius:0px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(18)

        name_w = label(name, 13, TEXT, True)
        name_w.setMinimumWidth(220)

        date_w = label(date, 12, MUTED)
        date_w.setMinimumWidth(145)

        det = label(f"{detections} detections", 12, MUTED)
        det.setMinimumWidth(125)

        status_w = label(status, 11, GREEN, True)
        status_w.setAlignment(Qt.AlignCenter)
        status_w.setFixedWidth(82)
        status_w.setFixedHeight(26)
        status_w.setStyleSheet(
            f"color:{GREEN}; background:#EAF7F1; border-radius:13px;"
        )

        lay.addWidget(name_w)
        lay.addWidget(date_w)
        lay.addWidget(det)
        lay.addStretch(1)
        lay.addWidget(status_w)


class HomePage(QWidget):
    def __init__(self, navigate):
        super().__init__()
        self.navigate = navigate

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet(f"background:{BG};")
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- HERO ----------------
        hero = HeroBackground()
        h = QVBoxLayout(hero)
        h.setContentsMargins(72, 42, 72, 30)
        h.setSpacing(0)

        title = label(
            "AI-Powered Sonar Detection & Mapping",
            39, WHITE, True
        )
        title.setMinimumHeight(52)
        title.setMaximumHeight(58)

        subtitle = label(
            "Intelligent systems for real-time underwater debris detection",
            16, "#C9C8DC"
        )
        subtitle.setMinimumHeight(24)

        h.addWidget(title)
        h.addSpacing(7)
        h.addWidget(subtitle)
        h.addSpacing(22)
        h.addStretch(1)

        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(0)

        data = [
            ("595", "Sonar Frames"),
            ("4", "Detect Classes"),
            ("87.7%", "Avg. Confidence"),
            ("124 ms", "Inference Time"),
        ]

        for i, (value, text) in enumerate(data):
            stats.addWidget(StatBlock(value, text), 1)
            if i < len(data) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.VLine)
                line.setFixedHeight(48)
                line.setStyleSheet("color:rgba(255,255,255,35);")
                stats.addWidget(line)

        h.addLayout(stats)
        root.addWidget(hero)

        # ---------------- CAPABILITIES ----------------
        section = QWidget()
        sl = QVBoxLayout(section)
        sl.setContentsMargins(72, 38, 72, 25)
        sl.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(10)

        heading_box = QVBoxLayout()
        heading_box.setSpacing(3)

        heading = label("What MarineVision can do", 29, TEXT, True)
        heading.setMinimumHeight(38)

        heading_box.addWidget(heading)

        top.addLayout(heading_box)
        top.addStretch(1)
        sl.addLayout(top)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        cards = [
            ("◎", "Real-time Sonar Analysis",
             "Process sonar imagery and inspect signal quality in one workspace.",
             PURPLE),
            ("☑", "Multi-class Detection",
             "Detect marine debris and anomalies with confidence scores.",
             ORANGE),
            ("⌂", "Geospatial Mapping",
             "Connect detections to mission coordinates and sonar tracks.",
             "#D7961D"),
            ("▧", "Mission Reporting",
             "Create clear mission summaries with findings and model metrics.",
             BLUE),
        ]

        for i, item in enumerate(cards):
            grid.addWidget(CapabilityCard(*item), 0, i)

        sl.addLayout(grid)

        # ---------------- RECENT MISSIONS ----------------
        recent_top = QHBoxLayout()
        recent_top.setContentsMargins(0, 12, 0, 0)

        recent_box = QVBoxLayout()
        recent_box.setSpacing(3)
        recent_box.addWidget(label("Recent Missions", 27, TEXT, True))
        recent_top.addLayout(recent_box)
        recent_top.addStretch(1)
        sl.addLayout(recent_top)

        recent_container = QFrame()
        recent_container.setObjectName("recentContainer")
        recent_container.setStyleSheet(f"""
            QFrame#recentContainer {{
                background:white;
                border:1px solid {BORDER};
                border-radius:10px;
            }}
        """)
        recent = QVBoxLayout(recent_container)
        recent.setContentsMargins(0, 0, 0, 0)
        recent.setSpacing(0)
        recent.addWidget(MissionRow("Mission 024 · Arabian Sea", "11 Sep 2026",
                                    "Completed", 24))
        recent.addWidget(MissionRow("Mission 023 · Konkan Coast", "09 Sep 2026",
                                    "Completed", 18))
        recent.addWidget(MissionRow("Mission 022 · Training Run", "06 Sep 2026",
                                    "Completed", 31, show_divider=False))
        sl.addWidget(recent_container)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 15, 0, 5)
        footer.addWidget(label("© 2026 MarineVision", 10, "#8B887D"))
        footer.addStretch(1)
        footer.addWidget(label("AI-assisted marine intelligence", 10, "#8B887D"))
        sl.addLayout(footer)

        root.addWidget(section)
        root.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)


class PageShell(QWidget):
    def __init__(self, eyebrow, title, subtitle):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(56, 44, 56, 40)
        root.setSpacing(8)

        root.addWidget(label(title, 30, TEXT, True))
        root.addWidget(label(subtitle, 14, MUTED))
        root.addSpacing(26)

        self.body = QVBoxLayout()
        self.body.setSpacing(16)
        root.addLayout(self.body)
        root.addStretch(1)


class AnalyzePage(PageShell):
    def __init__(self):
        super().__init__(
            "Detection Workspace",
            "Analyze Sonar Data",
            "Load side-scan sonar imagery, configure detection and review the output."
        )
        self.selected_file = None

        steps = QHBoxLayout()
        steps.setSpacing(0)
        for i, text in enumerate(["1  Load", "2  Preprocess", "3  Detect", "4  Results"]):
            s = label(text, 12, WHITE if i == 0 else MUTED, True)
            s.setAlignment(Qt.AlignCenter)
            s.setFixedHeight(38)
            s.setStyleSheet(
                f"background:{PURPLE if i == 0 else '#ECEBF2'};"
                f"color:{WHITE if i == 0 else MUTED}; border-radius:5px;"
            )
            steps.addWidget(s, 1)
            if i < 3:
                steps.addSpacing(5)
        self.body.addLayout(steps)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        # Upload card
        upload = QFrame()
        upload.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        upload.setStyleSheet("QFrame { background:transparent; border:none; }")
        ul = QVBoxLayout(upload)
        ul.setContentsMargins(25, 24, 25, 24)
        ul.setSpacing(12)

        ul.addWidget(label("SONAR INPUT", 11, "#7779A1", True))
        self.file_title = label("No sonar file selected", 17, TEXT, True)
        self.file_title.setWordWrap(True)
        self.file_hint = label(
            "PNG, JPG, TIFF, XTF or CSV files",
            12, MUTED
        )
        self.file_hint.setWordWrap(True)

        browse = make_button("Browse Sonar Files", "secondary", 44)
        browse.clicked.connect(self.browse)

        ul.addWidget(self.file_title)
        ul.addWidget(self.file_hint)
        ul.addSpacing(5)
        ul.addWidget(browse, 0, Qt.AlignLeft)
        ul.addStretch(1)

        # Config card
        config = QFrame()
        config.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        config.setStyleSheet(f"""
            QFrame {{ background:transparent; border:none; }}
            QComboBox, QLineEdit {{
                background:#FAFAFC; border:1px solid {BORDER};
                border-radius:6px; padding:8px 10px; color:{TEXT};
            }}
        """)
        cl = QVBoxLayout(config)
        cl.setContentsMargins(25, 24, 25, 24)
        cl.setSpacing(12)
        cl.addWidget(label("DETECTION SETTINGS", 11, "#7779A1", True))

        cl.addWidget(label("Model", 11, MUTED))
        self.model = QComboBox()
        self.model.addItems([
            "YOLO11s Sonar Detector (bundled)",
            "Custom Model"
        ])
        self.model.setMinimumHeight(38)
        cl.addWidget(self.model)

        cl.addSpacing(4)
        cl.addWidget(label("Model weights (.pt)", 11, MUTED))
        weights_row = QHBoxLayout()
        weights_row.setSpacing(8)
        # Defaults to the trained weights bundled in sonar_model/models/,
        # so most users never need to touch this - it's here for
        # "Custom Model" or testing a different checkpoint.
        self.weights_path = (
            str(DEFAULT_MODEL_PATH) if DEFAULT_MODEL_PATH.exists() else None
        )
        default_label = (
            DEFAULT_MODEL_PATH.name if self.weights_path
            else "No weights file selected"
        )
        self.weights_label = label(default_label, 12, MUTED)
        self.weights_label.setWordWrap(True)
        weights_browse = make_button("Browse", "secondary", 38)
        weights_browse.clicked.connect(self.browse_weights)
        weights_row.addWidget(self.weights_label, 1)
        weights_row.addWidget(weights_browse, 0)
        cl.addLayout(weights_row)

        cl.addSpacing(4)
        cl.addWidget(label("Confidence threshold", 11, MUTED))
        self.threshold = QLineEdit("0.25")
        self.threshold.setMinimumHeight(38)
        cl.addWidget(self.threshold)

        cl.addSpacing(10)
        self.start_btn = make_button("Start Analysis", "primary", 44)
        self.start_btn.clicked.connect(self.start_analysis)
        cl.addWidget(self.start_btn)
        cl.addStretch(1)

        grid.addWidget(upload, 0, 0)
        grid.addWidget(config, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.body.addLayout(grid)

        result = QFrame()
        result.setMinimumHeight(245)
        result.setStyleSheet(
            f"background:#11113E; border-radius:10px;"
        )
        rl = QVBoxLayout(result)
        rl.setContentsMargins(24, 20, 24, 20)
        rl.setSpacing(9)
        rl.addWidget(label("RESULT PREVIEW", 11, "#A9A7CF", True))
        self.result_label = label(
            "Load a sonar image to preview AI detections.",
            16, WHITE, True
        )
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumHeight(130)
        rl.addWidget(self.result_label)

        self.result_image = QLabel()
        self.result_image.setAlignment(Qt.AlignCenter)
        self.result_image.hide()
        rl.addWidget(self.result_image)

        self.body.addWidget(result)

        self.worker = None

    def browse_weights(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLO11 Weights", "",
            "PyTorch Weights (*.pt);;All Files (*)"
        )
        if path:
            self.weights_path = path
            self.weights_label.setText(Path(path).name)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Sonar Data", "",
            "Sonar/Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.xtf);;"
            "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.selected_file = path
            self.file_title.setText(Path(path).name)
            self.file_hint.setText(path)
            self.result_label.setText(
                "SONAR IMAGE LOADED\n\n"
                f"{Path(path).name}\n\n"
                "Ready for preprocessing and detection."
            )

    def start_analysis(self):
        if not self.selected_file:
            QMessageBox.warning(
                self, "No File Selected",
                "Please select a sonar image or mission file first."
            )
            return

        if not self.weights_path:
            QMessageBox.warning(
                self, "No Model Selected",
                "Please browse to your trained YOLO11 weights (.pt) file first."
            )
            return

        try:
            confidence = float(self.threshold.text())
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Confidence",
                "Confidence threshold must be a number between 0 and 1."
            )
            return

        self.result_image.hide()
        self.result_label.setText(
            "ANALYZING...\n\n"
            f"File: {Path(self.selected_file).name}\n"
            f"Model: {self.model.currentText()}\n"
            f"Confidence: {confidence}\n\n"
            "Running YOLO11 inference - this may take a moment."
        )
        self.start_btn.setEnabled(False)

        self.worker = DetectionWorker(
            self.weights_path, str(DEFAULT_CLASSES_PATH),
            self.selected_file, confidence,
        )
        self.worker.finished_ok.connect(self.on_analysis_done)
        self.worker.finished_err.connect(self.on_analysis_error)
        self.worker.start()

    def on_analysis_done(self, results: dict):
        self.start_btn.setEnabled(True)

        detections = results.get("detections", [])
        count = results.get("detection_count", len(detections))

        if detections:
            counts_by_class = {}
            for d in detections:
                counts_by_class[d["class_name"]] = counts_by_class.get(d["class_name"], 0) + 1
            summary = ",  ".join(f"{n}x {name}" for name, n in counts_by_class.items())
        else:
            summary = "No objects detected above the confidence threshold."

        json_path = results.get("results_json_path")
        saved_note = f"\nSaved: {Path(json_path).name}" if json_path else ""

        self.result_label.setText(
            "ANALYSIS COMPLETE\n\n"
            f"File: {results.get('image', Path(self.selected_file).name)}\n"
            f"{count} detection(s):  {summary}"
            f"{saved_note}"
        )

        overlay_path = results.get("overlay_path")
        if overlay_path and Path(overlay_path).exists():
            pixmap = QPixmap(overlay_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToHeight(220, Qt.SmoothTransformation)
                self.result_image.setPixmap(pixmap)
                self.result_image.show()

    def on_analysis_error(self, message: str):
        self.start_btn.setEnabled(True)
        self.result_label.setText(
            "ANALYSIS FAILED\n\n" + message
        )
        QMessageBox.critical(self, "Detection Error", message)


class MapPage(PageShell):
    def __init__(self):
        super().__init__(
            "Mission Intelligence",
            "Mission Map",
            "Visualize sonar tracks, mission positions and detected underwater targets."
        )

        toolbar = QHBoxLayout()
        toolbar.addWidget(label("Mission", 12, MUTED, True))
        mission = QComboBox()
        mission.addItems(["Mission 024 · Arabian Sea", "Mission 023 · Konkan Coast"])
        mission.setFixedHeight(38)
        mission.setFixedWidth(260)
        toolbar.addWidget(mission)
        toolbar.addStretch(1)

        center = make_button("Center Mission", "secondary", 38)
        center.clicked.connect(
            lambda: QMessageBox.information(
                self, "Mission Map",
                "Map center control is ready for GPS/map integration."
            )
        )
        toolbar.addWidget(center)
        self.body.addLayout(toolbar)

        frame = QFrame()
        frame.setMinimumHeight(500)
        frame.setStyleSheet(
            f"background:#E9EBF2; border:1px solid {BORDER}; border-radius:10px;"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)

        map_text = label(
            "MISSION MAP\n\n"
            "◎  Mission route\n"
            "•  Detection points\n"
            "—  Sonar track\n\n"
            "GPS / geospatial layer ready for integration",
            16, "#676B82", True
        )
        map_text.setAlignment(Qt.AlignCenter)
        fl.addWidget(map_text)
        self.body.addWidget(frame)


class ReportsPage(PageShell):
    def __init__(self):
        super().__init__(
            "Mission History",
            "Mission Reports",
            "Review detection results and export mission evidence."
        )

        table = QTableWidget(4, 5)
        table.setHorizontalHeaderLabels(
            ["Mission", "Date", "Detections", "Confidence", "Status"]
        )
        rows = [
            ("Mission 024", "11 Sep 2026", "24", "87.7%", "Completed"),
            ("Mission 023", "09 Sep 2026", "18", "91.2%", "Completed"),
            ("Mission 022", "06 Sep 2026", "31", "84.9%", "Completed"),
            ("Mission 021", "03 Sep 2026", "15", "89.5%", "Completed"),
        ]
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(value))

        table.setMinimumHeight(250)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet(f"""
            QTableWidget {{
                background:white; border:1px solid {BORDER};
                border-radius:8px; gridline-color:#ECEBF0;
            }}
            QHeaderView::section {{
                background:#F2F1F6; color:{TEXT};
                padding:10px; border:none; font-weight:700;
            }}
            QTableWidget::item {{
                padding:9px; color:{TEXT};
            }}
        """)
        self.body.addWidget(table)

        buttons = QHBoxLayout()
        create = make_button("Create Report", "primary", 44)
        csv = make_button("Export CSV", "secondary", 44)
        js = make_button("Export JSON", "secondary", 44)

        create.clicked.connect(
            lambda: QMessageBox.information(
                self, "Create Report",
                "Mission report generation is ready for the reporting pipeline."
            )
        )
        csv.clicked.connect(self.export_csv)
        js.clicked.connect(self.export_json)

        buttons.addWidget(create)
        buttons.addWidget(csv)
        buttons.addWidget(js)
        buttons.addStretch(1)
        self.body.addLayout(buttons)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV Report", "", "CSV Files (*.csv)"
        )
        if path:
            QMessageBox.information(self, "Export CSV", f"Output:\n{path}")

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON Report", "", "JSON Files (*.json)"
        )
        if path:
            QMessageBox.information(self, "Export JSON", f"Output:\n{path}")


class DatasetPage(PageShell):
    def __init__(self):
        super().__init__(
            "Training Data",
            "Dataset Library",
            "Manage sonar imagery and annotation datasets used by MarineVision."
        )

        card = QFrame()
        card.setMinimumHeight(240)
        card.setStyleSheet("background:transparent; border:none;")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 25, 28, 25)
        lay.setSpacing(12)

        lay.addWidget(label("DATASET LIBRARY", 11, "#7779A1", True))
        lay.addWidget(label("Marine Debris Sonar Dataset", 19, TEXT, True))
        lay.addWidget(label(
            "Side-scan sonar images prepared for multi-class debris and anomaly detection.",
            13, MUTED
        ))

        progress = QProgressBar()
        progress.setValue(78)
        progress.setTextVisible(True)
        progress.setFormat("Dataset readiness  ·  %p%")
        progress.setFixedHeight(24)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background:#ECEBF2; border:none; border-radius:6px;
                color:{TEXT}; text-align:center;
            }}
            QProgressBar::chunk {{ background:{PURPLE}; border-radius:6px; }}
        """)
        lay.addWidget(progress)

        import_btn = make_button("Import Dataset", "primary", 44)
        import_btn.clicked.connect(self.import_dataset)
        lay.addWidget(import_btn, 0, Qt.AlignLeft)

        self.body.addWidget(card)

    def import_dataset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Dataset", "",
            "Dataset Files (*.zip *.csv *.json *.txt);;All Files (*)"
        )
        if path:
            QMessageBox.information(
                self, "Dataset Imported",
                f"Selected dataset:\n{path}"
            )


class ConfigPage(PageShell):
    def __init__(self):
        super().__init__(
            "System Preferences",
            "Configuration",
            "Configure inference, compute device and reporting preferences."
        )

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background:transparent; border:none; }}
            QComboBox, QLineEdit {{
                background:#FAFAFC; border:1px solid {BORDER};
                border-radius:6px; padding:8px 10px; color:{TEXT};
            }}
            QCheckBox {{ color:{TEXT}; }}
        """)
        grid = QGridLayout(card)
        grid.setContentsMargins(28, 26, 28, 26)
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(18)

        grid.addWidget(label("MODEL", 11, "#7779A1", True), 0, 0)
        grid.addWidget(label("COMPUTE", 11, "#7779A1", True), 0, 1)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["YOLOv8 Marine Debris", "YOLOv8 Anomaly"])
        self.model_combo.setMinimumHeight(40)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["Auto", "CPU", "CUDA / GPU"])
        self.device_combo.setMinimumHeight(40)

        grid.addWidget(self.model_combo, 1, 0)
        grid.addWidget(self.device_combo, 1, 1)

        grid.addWidget(label("CONFIDENCE THRESHOLD", 11, "#7779A1", True), 2, 0)
        grid.addWidget(label("REPORT FORMAT", 11, "#7779A1", True), 2, 1)

        self.threshold_edit = QLineEdit("0.50")
        self.threshold_edit.setMinimumHeight(40)

        self.output_combo = QComboBox()
        self.output_combo.addItems(["CSV + JSON", "CSV", "JSON"])
        self.output_combo.setMinimumHeight(40)

        grid.addWidget(self.threshold_edit, 3, 0)
        grid.addWidget(self.output_combo, 3, 1)

        self.save_btn = make_button("Save Configuration", "primary", 44)
        self.save_btn.clicked.connect(self.save)
        grid.addWidget(self.save_btn, 4, 0, 1, 2, Qt.AlignLeft)

        self.body.addWidget(card)

    def save(self):
        QMessageBox.information(
            self, "Configuration Saved",
            f"Model: {self.model_combo.currentText()}\n"
            f"Device: {self.device_combo.currentText()}\n"
            f"Confidence: {self.threshold_edit.text()}\n"
            f"Report: {self.output_combo.currentText()}"
        )


class MarineVisionWindow(QMainWindow):
    """Main desktop shell with a collapsible left navigation rail."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarineVision")
        self.resize(1280, 860)
        self.setMinimumSize(1100, 720)
        self.sidebar_expanded = True

        central = QWidget()
        central.setStyleSheet(f"background:{BG};")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- LEFT SIDEBAR ----------------
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(190)
        self.sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background:{NAVY};
                border-right:1px solid #262454;
            }}
        """)
        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(10, 14, 10, 14)
        sl.setSpacing(6)

        # Functional desktop control instead of duplicate branding.
        self.collapse_btn = QPushButton("☰  Collapse")
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setFixedHeight(40)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background:transparent; color:#BDBBD9; border:none;
                border-radius:7px; text-align:left; padding:0 12px;
                font-size:11px; font-weight:600;
            }
            QPushButton:hover { background:rgba(255,255,255,14); color:white; }
        """)
        self.collapse_btn.clicked.connect(self.toggle_sidebar)
        sl.addWidget(self.collapse_btn)
        sl.addSpacing(10)

        self.nav_buttons = {}
        nav_items = [
            ("home", "⌂", "Home"),
            ("detect", "◎", "Analyze"),
            ("map", "⌖", "Map"),
            ("reports", "▤", "Reports"),
            ("dataset", "▧", "Dataset"),
            ("config", "⚙", "Config"),
        ]
        for key, icon, text in nav_items:
            b = QPushButton(f"{icon}   {text}")
            b.setProperty("nav_key", key)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(44)
            b.setToolTip(text)
            b.setStyleSheet("""
                QPushButton {
                    background:transparent; color:#BDBBD9; border:none;
                    border-radius:7px; text-align:left; padding:0 12px;
                    font-size:13px; font-weight:600;
                }
                QPushButton:hover { color:white; background:rgba(255,255,255,14); }
                QPushButton[active="true"] {
                    color:white; background:#302C75;
                    border-left:3px solid #F58A27;
                    padding-left:9px;
                }
            """)
            b.clicked.connect(lambda checked=False, k=key: self.go(k))
            self.nav_buttons[key] = b
            sl.addWidget(b)

        sl.addStretch(1)
        root.addWidget(self.sidebar)

        # ---------------- WORKSPACE ----------------
        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # Compact desktop toolbar: page context + useful controls.
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(64)
        self.toolbar.setStyleSheet(f"""
            QFrame#desktopToolbar {{
                background:white;
                border-bottom:1px solid {BORDER};
            }}
        """)
        self.toolbar.setObjectName("desktopToolbar")
        tl = QHBoxLayout(self.toolbar)
        tl.setContentsMargins(22, 10, 22, 10)
        tl.setSpacing(8)

        self.page_title = label("Home", 16, TEXT, True)
        tl.addWidget(self.page_title)
        tl.addSpacing(18)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search missions, files or detections…")
        self.search.setFixedHeight(38)
        self.search.setMinimumWidth(280)
        self.search.setStyleSheet(f"""
            QLineEdit {{
                background:{BG}; border:1px solid {BORDER}; border-radius:7px;
                padding:0 12px; color:{TEXT};
            }}
            QLineEdit:focus {{ border-color:#B8B5DE; background:white; }}
        """)
        tl.addWidget(self.search)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Missions", "Completed", "In Progress", "Training"])
        self.filter_combo.setFixedHeight(38)
        self.filter_combo.setMinimumWidth(125)
        tl.addWidget(self.filter_combo)

        tl.addStretch(1)

        self.refresh_btn = QPushButton("↻  Refresh")
        self.refresh_btn.setFixedHeight(38)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{ background:white; color:{TEXT}; border:1px solid {BORDER};
                border-radius:7px; padding:0 13px; font-weight:600; }}
            QPushButton:hover {{ background:{PURPLE_LIGHT}; }}
        """)
        self.refresh_btn.clicked.connect(self.refresh_current_page)
        tl.addWidget(self.refresh_btn)

        self.analyze_toolbar_btn = QPushButton("+  New Analysis")
        self.analyze_toolbar_btn.setFixedHeight(38)
        self.analyze_toolbar_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_toolbar_btn.setStyleSheet(f"""
            QPushButton {{ background:{PURPLE}; color:white; border:none;
                border-radius:7px; padding:0 14px; font-weight:700; }}
            QPushButton:hover {{ background:{NAVY_3}; }}
        """)
        self.analyze_toolbar_btn.clicked.connect(lambda: self.go("detect"))
        tl.addWidget(self.analyze_toolbar_btn)

        workspace_layout.addWidget(self.toolbar)

        # ---------------- PAGES ----------------
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background:transparent;")
        workspace_layout.addWidget(self.pages, 1)

        root.addWidget(workspace, 1)

        self.page_map = {}
        pages = [
            ("home", HomePage(self.go)),
            ("detect", AnalyzePage()),
            ("map", MapPage()),
            ("reports", ReportsPage()),
            ("dataset", DatasetPage()),
            ("config", ConfigPage()),
        ]
        for key, page in pages:
            self.page_map[key] = self.pages.count()
            self.pages.addWidget(page)

        self.go("home")

    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar.setFixedWidth(64 if not self.sidebar_expanded else 190)
        for key, button in self.nav_buttons.items():
            text = button.property("nav_text") or {
                "home":"Home", "detect":"Analyze", "map":"Map",
                "reports":"Reports", "dataset":"Dataset", "config":"Config"
            }[key]
            icon = {"home":"⌂", "detect":"◎", "map":"⌖", "reports":"▤", "dataset":"▧", "config":"⚙"}[key]
            button.setText(f"{icon}   {text}" if self.sidebar_expanded else icon)
            button.setStyleSheet(button.styleSheet().replace(
                "text-align:left; padding:0 12px;", 
                "text-align:center; padding:0;" if not self.sidebar_expanded else "text-align:left; padding:0 12px;"
            ).replace(
                "padding-left:9px;", "padding-left:9px;" if self.sidebar_expanded else "padding-left:0;"
            ))
        self.collapse_btn.setText("☰  Collapse" if self.sidebar_expanded else "☰")
        self.collapse_btn.setStyleSheet(self.collapse_btn.styleSheet().replace(
            "text-align:left; padding:0 12px;",
            "text-align:center; padding:0;" if not self.sidebar_expanded else "text-align:left; padding:0 12px;"
        ))

    def go(self, key):
        if key not in self.page_map:
            return
        self.pages.setCurrentIndex(self.page_map[key])
        titles = {
            "home": "Home", "detect": "Analyze", "map": "Map",
            "reports": "Reports", "dataset": "Dataset", "config": "Config"
        }
        self.page_title.setText(titles.get(key, "MarineVision"))

        for name, button in self.nav_buttons.items():
            button.setProperty("active", name == key)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def refresh_current_page(self):
        # Re-apply the current page so the toolbar action remains useful
        # without introducing page-specific destructive behaviour.
        current = self.pages.currentIndex()
        self.pages.widget(current).update()

def apply_app_style(app):
    app.setStyle("Fusion")
    app.setFont(QFont(FONT_FAMILY, 10))
    app.setStyleSheet(f"""
        QWidget {{
            font-family:"{FONT_FAMILY}", "Segoe UI", Arial, sans-serif;
            color:{TEXT};
        }}
        QScrollArea {{
            border:none;
            background:{BG};
        }}
        QScrollBar:vertical {{
            width:8px;
            background:transparent;
        }}
        QScrollBar::handle:vertical {{
            background:#C9C7D0;
            border-radius:4px;
            min-height:30px;
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height:0;
        }}
        QToolTip {{
            background:#181741;
            color:white;
            border:1px solid #39366F;
            padding:6px;
        }}
    """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MarineVision")
    apply_app_style(app)

    window = MarineVisionWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
