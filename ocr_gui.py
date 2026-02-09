import sys
import os
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QFileDialog, QSpinBox, QTextEdit, QFrame, 
                               QGraphicsDropShadowEffect, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QPoint
from PySide6.QtGui import QColor, QPalette, QBrush, QLinearGradient, QFont, QIcon, QPainter, QTextCursor

# Import OCR Logic
try:
    from ocr_script import ocr_pdf
except ImportError:
    pass

class WorkerThread(QThread):
    progress_signal = Signal(str)
    log_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()
    
    def __init__(self, source_dir, output_dir, zoom, psm, lang, tess_path):
        super().__init__()
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.zoom = zoom
        self.psm = psm
        self.lang = lang
        self.tess_path = tess_path
        self.is_running = True

    def run(self):
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            
            pdf_files = [f for f in os.listdir(self.source_dir) if f.lower().endswith('.pdf')]
            total_files = len(pdf_files)
            self.log_signal.emit(f"Found {total_files} PDF files.")
            
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            history_file = os.path.join(script_dir, "processed_log.txt")
            
            processed_files = set()
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    processed_files = set(f.read().splitlines())
            
            for i, filename in enumerate(pdf_files):
                if not self.is_running:
                    self.log_signal.emit("Process stopped by user.")
                    break
                
                if filename in processed_files:
                    self.log_signal.emit(f"Skipping {filename} (Already processed).")
                    continue
                
                self.log_signal.emit(f"Processing: {filename}...")
                
                try:
                    pdf_path = os.path.join(self.source_dir, filename)
                    
                    def on_page_progress(current, total):
                        if not self.is_running:
                            raise Exception("Stopped by user")
                        self.progress_signal.emit(f"[{filename}] Page {current}/{total}")
                    
                    ocr_pdf(pdf_path, output_dir=self.output_dir, progress_callback=on_page_progress, 
                            zoom=self.zoom, psm=self.psm, lang=self.lang, tesseract_cmd=self.tess_path)
                    
                    with open(history_file, "a", encoding="utf-8") as f:
                        f.write(filename + "\n")
                    
                    self.log_signal.emit(f"Completed: {filename}")
                    
                except Exception as e:
                    self.log_signal.emit(f"Error processing {filename}: {e}")
                    if "Stopped by user" in str(e):
                        break
            
            self.log_signal.emit("All tasks finished.")
            
        except Exception as e:
            self.log_signal.emit(f"Critical Error: {e}")
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False

class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            GlassFrame {
                background-color: rgba(255, 255, 255, 100); 
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 150);
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Glass OCR Tool")
        self.resize(800, 700)
        
        # Transparent background optimization
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Style
        self.setup_style()

        # UI Components
        self.setup_ui()
        
        # Worker
        self.worker = None

        # Load Settings
        self.load_settings()

        # Check Tesseract
        self.check_tesseract()

    def check_tesseract(self):
        tess = self.tess_edit.text()
        if not tess or not os.path.exists(tess):
            # Try to find again in case it wasn't in settings
            found = False
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.join(os.getenv('LOCALAPPDATA'), r"Programs\Tesseract-OCR\tesseract.exe") 
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    self.tess_edit.setText(p)
                    found = True
                    break
            
            if not found:
                 QMessageBox.warning(self, "Tesseract Not Found", 
                                    "Tesseract OCR could not be found automatically.\n"
                                    "Please set the path to 'tesseract.exe' manually in the settings.\n\n"
                                    "If you haven't installed it, please download it from GitHub.")

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def load_settings(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                if "source_dir" in settings and os.path.exists(settings["source_dir"]):
                    self.source_dir.setText(settings["source_dir"])
                if "output_dir" in settings: # Output dir might not create yet, but we can set text
                    self.output_dir.setText(settings["output_dir"])
                if "zoom" in settings:
                    self.zoom_spin.setValue(int(settings["zoom"]))
                if "psm" in settings:
                    self.psm_spin.setValue(int(settings["psm"]))
                if "lang" in settings:
                    self.lang_edit.setText(settings["lang"])
                if "tess_path" in settings and os.path.exists(settings["tess_path"]):
                    self.tess_edit.setText(settings["tess_path"])
                    
                self.log("Settings loaded.")
            except Exception as e:
                self.log(f"Failed to load settings: {e}")

    def save_settings(self):
        settings = {
            "source_dir": self.source_dir.text(),
            "output_dir": self.output_dir.text(),
            "zoom": self.zoom_spin.value(),
            "psm": self.psm_spin.value(),
            "lang": self.lang_edit.text(),
            "tess_path": self.tess_edit.text()
        }
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def paintEvent(self, event):
        # Draw the gradient background
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        # Beautiful pastel gradient
        gradient.setColorAt(0.0, QColor("#a18cd1"))
        gradient.setColorAt(1.0, QColor("#fbc2eb"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)

    def setup_style(self):
        # Global Stylesheet for child widgets
        self.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', 'Meiryo UI', sans-serif;
                color: #333;
                font-size: 14px;
                background: transparent;
            }
            QLineEdit, QSpinBox {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(255, 255, 255, 200);
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
                color: #333;
            }
            QLineEdit:focus, QSpinBox:focus {
                background-color: rgba(255, 255, 255, 230);
                border: 1px solid #a18cd1;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 150);
                border: 1px solid rgba(255, 255, 255, 200);
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                color: #555;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 220);
                color: #333;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 100);
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 120);
                border-radius: 10px;
                border: none;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)

    def setup_ui(self):
        # Header Layout (Title + Buttons)
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Vertical JP OCR Tool")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label, stretch=1)
        
        # Header Buttons Frame
        btn_frame = GlassFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn_manual = QPushButton("Manual")
        self.btn_manual.setFixedWidth(80)
        self.btn_manual.clicked.connect(self.show_manual)
        btn_layout.addWidget(self.btn_manual)
        
        self.btn_about = QPushButton("About")
        self.btn_about.setFixedWidth(80)
        self.btn_about.clicked.connect(self.show_about)
        btn_layout.addWidget(self.btn_about)
        
        header_layout.addWidget(btn_frame)
        
        self.main_layout.addLayout(header_layout)

        # 1. Source Directory Frame
        self.create_path_selector("Source Directory (PDFs):", "source_dir", os.path.expanduser("~"))

        # 2. Output Directory Frame
        self.create_path_selector("Output Directory:", "output_dir", os.getcwd())

        # 3. Settings Frame
        settings_frame = GlassFrame()
        settings_layout = QHBoxLayout(settings_frame)
        
        # Zoom
        settings_layout.addWidget(QLabel("Zoom:"))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(1, 10)
        self.zoom_spin.setValue(3)
        settings_layout.addWidget(self.zoom_spin)
        
        # PSM
        settings_layout.addWidget(QLabel("PSM:"))
        self.psm_spin = QSpinBox()
        self.psm_spin.setRange(1, 13)
        self.psm_spin.setValue(5)
        settings_layout.addWidget(self.psm_spin)
        
        # Lang
        settings_layout.addWidget(QLabel("Lang:"))
        self.lang_edit = QLineEdit("jpn_vert")
        settings_layout.addWidget(self.lang_edit)
        
        self.main_layout.addWidget(settings_frame)

        # 4. Tesseract Path
        self.setup_tesseract_path()
        
        # 5. Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("START PROCESSING")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 255, 200, 180);
                color: #005500;
            }
            QPushButton:hover {
                background-color: rgba(220, 255, 220, 220);
            }
        """)
        self.btn_start.clicked.connect(self.start_processing)
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 200, 200, 180);
                color: #550000;
            }
            QPushButton:hover {
                background-color: rgba(255, 220, 220, 220);
            }
        """)
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        self.main_layout.addLayout(btn_layout)

        # 6. Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_label)

        # 7. Logs Area
        logs_layout = QHBoxLayout()
        
        # General Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("General Logs...")
        
        # Page Log
        self.page_log_text = QTextEdit()
        self.page_log_text.setReadOnly(True)
        self.page_log_text.setPlaceholderText("Page Progress...")
        
        logs_layout.addWidget(self.log_text)
        logs_layout.addWidget(self.page_log_text)
        
        self.main_layout.addLayout(logs_layout)

    def create_path_selector(self, label_text, var_name, default_val):
        frame = GlassFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        layout.addWidget(QLabel(label_text))
        
        line_edit = QLineEdit(default_val)
        setattr(self, var_name, line_edit) # Dynamically set attribute
        layout.addWidget(line_edit)
        
        btn = QPushButton("Browse")
        btn.clicked.connect(lambda: self.browse_dir(line_edit))
        layout.addWidget(btn)
        
        self.main_layout.addWidget(frame)

    def setup_tesseract_path(self):
        frame = GlassFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        layout.addWidget(QLabel("Tesseract Path:"))
        
        default_tess = ""
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.getenv('LOCALAPPDATA'), r"Programs\Tesseract-OCR\tesseract.exe") 
        ]
        for p in possible_paths:
            if os.path.exists(p):
                default_tess = p
                break
                
        self.tess_edit = QLineEdit(default_tess)
        layout.addWidget(self.tess_edit)
        
        btn = QPushButton("Browse")
        btn.clicked.connect(self.browse_file)
        layout.addWidget(btn)
        
        self.main_layout.addWidget(frame)

    def browse_dir(self, line_edit):
        d = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if d:
            line_edit.setText(d)

    def browse_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Executable", "", "Executable (*.exe);;All Files (*.*)")
        if f:
            self.tess_edit.setText(f)

    def log(self, message):
        self.log_text.append(message)
        # Scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def log_page(self, message):
        self.page_log_text.append(message)
        cursor = self.page_log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.page_log_text.setTextCursor(cursor)

    def start_processing(self):
        if self.worker is not None and self.worker.isRunning():
            return

        source = self.source_dir.text()
        output = self.output_dir.text()
        
        self.worker = WorkerThread(
            source, output, 
            self.zoom_spin.value(), 
            self.psm_spin.value(), 
            self.lang_edit.text(),
            self.tess_edit.text()
        )
        
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.log_page)
        self.worker.error_signal.connect(self.show_error)
        self.worker.finished_signal.connect(self.on_process_finished)
        
        self.worker.start()
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("Processing...")
        self.status_label.setStyleSheet("color: white; font-weight: bold;")

    def stop_processing(self):
        if self.worker:
            self.worker.stop()
            self.log("Stopping process... please wait.")
            self.status_label.setText("Stopping...")

    def show_error(self, message):
        QMessageBox.critical(self, "Error", f"An error occurred:\n{message}")

    def show_about(self):
        QMessageBox.about(self, "About GlassOCR",
                          "<h3>GlassOCR v1.0.0</h3>"
                          "<p>A simple yet beautiful OCR tool for Japanese vertical text.</p>"
                          "<p><b>Author:</b> Antigravity</p>"
                          "<p><b>Libraries:</b> PySide6, PyMuPDF, pytesseract</p>"
                          "<p>Licensed under MIT License.</p>")

    def show_manual(self):
        # Locate README.md
        # If frozen (exe), it's in a temporary folder or same dir
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        readme_path = os.path.join(base_path, "README.md")
        
        content = "README.md not found."
        if os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"Error reading README: {e}"
        
        # Show in a dialog
        dialog = QMainWindow(self)
        dialog.setWindowTitle("Manual")
        dialog.resize(600, 500)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(content)
        dialog.setCentralWidget(text_edit)
        dialog.show()

    def on_process_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: white;")
        self.worker = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: Load a font if needed, but we rely on system fonts for now
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
