import os
import sys
custom_temp = os.path.join(os.getcwd(), "my_temp")
os.makedirs(custom_temp, exist_ok=True)
os.environ["TEMP"] = custom_temp
os.environ["TMP"] = custom_temp

import shutil
import uuid
import time
from pathlib import Path
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton, QPlainTextEdit,
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QVBoxLayout, QFrame,
    QFileDialog, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont,  QColor, QTextCursor, QTextCharFormat

from Functions import preprocess_and_syllabify, synthesize_speech
from db import populate_syllable_db, get_syllable_audio_path
from utils import resource_path


def safe_import(module_name, package_name=None):
    """Safely import optional dependencies"""
    try:
        if package_name:
            return __import__(module_name, fromlist=[package_name])
        return __import__(module_name)
    except ImportError:
        return None

pydub = safe_import('pydub')
PyPDF2 = safe_import('PyPDF2')
docx = safe_import('docx')

HAS_PYDUB = pydub is not None
HAS_PDF = PyPDF2 is not None
HAS_DOCX = docx is not None

# === Constants ===
DEFAULT_FONT_FAMILY = "Sylfaen"
DEFAULT_FONT_SIZE = 12
TITLE_FONT_FAMILY = "Arial"
TITLE_FONT_SIZE = 16
TITLE_FONT_WEIGHT = QFont.Weight.Bold
INPUT_LABEL_FONT_FAMILY = TITLE_FONT_FAMILY
INPUT_LABEL_FONT_SIZE = 12
INPUT_LABEL_FONT_WEIGHT = QFont.Weight.Bold
STATUS_BAR_HEIGHT = 25
AUDIO_FILE_NAME = "georgian_audio.wav"
AUDIO_FORMAT = "wav"
SAMPLE_TEXT = """
საქართველო არის ქვეყანა კავკასიაში.
თბილისი არის საქართველოს დედაქალაქი.
ქართული ენა უნიკალურია.
"""

Georgian_Alphabet = ["აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ"]

GEORGIAN_KEYBOARD_MAP = {
    'q': 'ქ', 'w': 'წ', 'e': 'ე', 'r': 'რ', 't': 'ტ', 'y': 'ყ', 
    'u': 'უ', 'i': 'ი', 'o': 'ო', 'p': 'პ', 'a': 'ა', 's': 'ს', 
    'd': 'დ', 'f': 'ფ', 'g': 'გ', 'h': 'ჰ', 'j': 'ჯ', 'k': 'კ', 
    'l': 'ლ', 'z': 'ზ', 'x': 'ხ', 'c': 'ც', 'v': 'ვ', 'b': 'ბ', 
    'n': 'ნ', 'm': 'მ'
}
GEORGIAN_KEYBOARD_MAP_SHIFT = {
    't': 'თ', 'w': 'ჭ', 'r': 'ღ', 'c': 'ჩ', 'j': 'ჟ'
    }

GEORGIAN_KEYBOARD_LAYOUTS = {
    'normal': [
        ['ქ', 'წ', 'ე', 'რ', 'ტ', 'ყ', 'უ', 'ი', 'ო', 'პ'],
        ['ა', 'ს', 'დ', 'ფ', 'გ', 'ჰ', 'ჯ', 'კ', 'ლ'],
        ['ზ', 'ხ', 'ც', 'ვ', 'ბ', 'ნ', 'მ']
    ],
    'shift': [
        ['ქ', 'ჭ', 'ე', 'ღ', 'თ', 'ყ', 'უ', 'ი', 'ო', 'პ'],
        ['ა', 'შ', 'დ', 'ფ', 'გ', 'ჰ', 'ჯ', 'კ', 'ლ'],
        ['ზ', 'ხ', 'ჩ', 'ვ', 'ბ', 'ნ', 'მ']
    ]
}

STRINGS = {
    "title": "ქართული ტექსტიდან მეტყველებაში გარდაქმნა",
    "input_label": "ტექსტის შეყვანა",
    "georgian_mode": "ქართული რეჟიმი",
    "font": "ფონტი:",
    "file_ops": "ოპერაციები",
    "load_file": "ატვირთე ფაილი",
    "clear_text": "წაშალე ტექსტი",
    "input_tools": "ტექსტის შეყვანა",
    "keyboard": "კლავიატურა",
    "sample_text": "ტექსტის ნიმუში",
    "audio_gen": "აუდიოს გენერაცია",
    "generate_audio": "🎵 აუდიოს გენერაცია",
    "play_audio": "▶️ აუდიოს გაშვება",
    "save_audio": "💾 აუდიოს შენახვა",
    "missing_deps": "Missing Dependencies:",
    "pydub_missing": "pydub not installed",
    "pdf_missing": "PyPDF2 not installed",
    "docx_missing": "python-docx not installed",
    "status_ready": "მზადაა",
    "status_georgian_on": "Georgian mode: ON",
    "status_georgian_off": "Georgian mode: OFF",
    "status_font_changed": "Font changed to {font}",
    "status_loaded": "ჩაიტვირთა: {file}",
    "status_text_cleared": "ტექსტი წაშლილია",
    "status_sample_inserted": "Sample text inserted",
    "status_db": "⏳ მიმდინარეობს syllable DB-ს შექმნა...",
    "status_preprocess": "🔍 წინასწარი დამუშავება...",
    "status_missing_syllables": "⚠️ მონაცემთა ბაზაში არ არსებობს მარცვლები",
    "status_audio_gen": "🎛️ აუდიოს გენერაცია...",
    "status_audio_success": "✅ აუდიო წარმატებით შეიქმნა!",
    "status_audio_error": "❌ აუდიოს გენერაციისას მოხდა შეცდომა",
    "status_playing": "▶️ მიმდინარეობს აუდიოს გაშვება...",
    "status_play_done": "▶️ გაშვება დასრულდა",
    "status_play_error": "❌ გაშვების შეცდომა",
    "status_audio_saved": "აუდიო შენახულია: {file}",
    "status_audio_saved_success": "აუდიო წარმატებით შენახულია!",
    "status_permission_error": "Permission denied: Unable to save file. Please choose a different location.",
    "warning_enter_text": "გთხოვთ შეიყვანოთ ტექსტი",
    "warning_generate_audio": "გთხოვთ, ჯერ დააგენერიროთ აუდიო",
    "warning_missing_syllables": "არ მოიპოვება შემდეგი მარცვლები:\n{syllables}",
    "warning_clear_text": "გსურთ ტექსტის წაშლა?",
    "success": "წარმატება",
    "error": "შეცდომა",
    "missing_dependency": "Missing Dependency",
    "info": "Info",
    "confirm": "დადასტურება",
    "save_audio_file": "Save Audio File",
    "open_file": "Open File",
    "wav_files": "WAV files (*.wav)",
    "all_files": "All files (*)",
    "virtual_keyboard": "ქართული კლავიატურა54",
    "shortcut_keyboard": "⌨️ კლავიატურა (Ctrl+K)",
}

class AudioWorker(QThread):
    """Worker thread for audio operations to prevent UI freezing"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, operation, audio_file=None):
        super().__init__()
        self.operation = operation
        self.audio_file = audio_file
        
    def run(self):
        try:
            if self.operation == 'play' and self.audio_file:
                self._play_audio()
            self.finished.emit(True, "Operation completed successfully")
        except Exception as e:
            import traceback
            self.finished.emit(False, f"{e}\n{traceback.format_exc()}")
    
    def _play_audio(self):
        self.progress.emit("▶️ მიმდინარეობს დაკვრა...")
        try:
            if sys.platform == "win32":
                # Use Windows built-in player (start command)
                subprocess.run(f'start "" "{self.audio_file}"', shell=True)
            else:
                # For Linux/macOS, try aplay/afplay
                subprocess.run(f'aplay "{self.audio_file}"', shell=True)
        except Exception as e:
            import traceback
            self.finished.emit(False, f"Audio playback error for file {self.audio_file}: {e}\n{traceback.format_exc()}")

class GeorgianTextEdit(QPlainTextEdit):
    """Custom text edit with Georgian input and context menu"""
    
    def __init__(self):
        super().__init__()
        self.setFont(QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setUndoRedoEnabled(True)
        self.georgian_mode = False
        self.georgian_map = GEORGIAN_KEYBOARD_MAP
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)


    
    def toggle_georgian(self):
        """Toggle Georgian input mode"""
        self.georgian_mode = not self.georgian_mode
        return self.georgian_mode
    
    def set_font(self, font_family, size=12):
        """Set font for text editor"""
        self.setFont(QFont(font_family, size))
    
    def keyPressEvent(self, event):
        """Handle key press events for Georgian input"""
        if self.georgian_mode and event.text():
            key = event.text().lower()
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                if key in GEORGIAN_KEYBOARD_MAP_SHIFT:
                    cursor = self.textCursor()
                    cursor.insertText(GEORGIAN_KEYBOARD_MAP_SHIFT[key])
                    return
            elif key in self.georgian_map:
                cursor = self.textCursor()
                cursor.insertText(self.georgian_map[key])
                return
        super().keyPressEvent(event)
    
    def show_context_menu(self, pos):
        """Show context menu with Georgian toggle option"""
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        
        toggle_text = "Disable Georgian" if self.georgian_mode else "Enable Georgian"
        toggle_action = QAction(toggle_text, self)
        toggle_action.triggered.connect(self.toggle_georgian)
        menu.addAction(toggle_action)
        
        menu.exec(self.mapToGlobal(pos))


class GeorgianKeyboardDialog(QDialog):
    """Virtual Georgian Keyboard Dialog"""
    
    def __init__(self, parent, text_edit):
        super().__init__(parent)
        self.text_edit = text_edit
        self.setWindowTitle("Georgian Keyboard")
        self.setFixedSize(700, 240)
        self.shift_on = False
        self.buttons = []
        # Use centralized layouts
        self.layouts = GEORGIAN_KEYBOARD_LAYOUTS
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the keyboard UI"""
        main_layout = QVBoxLayout(self)
        
        # Create keyboard rows
        current_layout = self.layouts['normal']
        for row_chars in current_layout:
            row_layout = QHBoxLayout()
            button_row = []
            
            for char in row_chars:
                btn = QPushButton(char)
                btn.setFont(QFont("Sylfaen", 14))
                btn.setFixedSize(40, 40)
                btn.clicked.connect(lambda checked, c=char: self.insert_char(c))
                row_layout.addWidget(btn)
                button_row.append(btn)
            
            self.buttons.append(button_row)
            main_layout.addLayout(row_layout)
        
        # Bottom controls
        self.create_bottom_controls(main_layout)
    
    def create_bottom_controls(self, main_layout):
        """Create bottom control buttons"""
        bottom_layout = QHBoxLayout()
        
        # Shift button
        self.shift_btn = QPushButton("Shift")
        self.shift_btn.setFixedSize(60, 30)
        self.shift_btn.clicked.connect(self.toggle_shift)
        bottom_layout.addWidget(self.shift_btn)
        
        # Space button
        space_btn = QPushButton("Space")
        space_btn.setFixedSize(70, 30)
        space_btn.clicked.connect(lambda: self.insert_char(' '))
        bottom_layout.addWidget(space_btn)
        
        # Punctuation buttons
        punctuation = ['.', ',', '!', '?', ';', ':', '-', '(', ')']
        for char in punctuation:
            btn = QPushButton(char)
            btn.setFixedSize(30, 30)
            btn.clicked.connect(lambda checked, c=char: self.insert_char(c))
            bottom_layout.addWidget(btn)
        
        # Enter button
        enter_btn = QPushButton("Enter")
        enter_btn.setFixedSize(60, 30)
        enter_btn.clicked.connect(lambda: self.insert_char('\n'))
        bottom_layout.addWidget(enter_btn)
        
        main_layout.addLayout(bottom_layout)
    
    def insert_char(self, char):
        """Insert character into text editor"""
        cursor = self.text_edit.textCursor()
        cursor.insertText(char)
        self.text_edit.setFocus()
    
    def toggle_shift(self):
        """Toggle shift mode and update keyboard layout"""
        self.shift_on = not self.shift_on
        self.update_keyboard_layout()
    
    def update_keyboard_layout(self):
        """Update keyboard layout based on shift state"""
        layout_name = 'shift' if self.shift_on else 'normal'
        current_layout = self.layouts[layout_name]
        
        for row_idx, row_chars in enumerate(current_layout):
            for col_idx, char in enumerate(row_chars):
                if row_idx < len(self.buttons) and col_idx < len(self.buttons[row_idx]):
                    btn = self.buttons[row_idx][col_idx]
                    btn.setText(char)
                    # Reconnect with new character
                    btn.clicked.disconnect()
                    btn.clicked.connect(lambda checked, c=char: self.insert_char(c))


class ModernGeorgianTTS(QMainWindow):
    """Main application window for Georgian TTS"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Georgian TTS - ქართული TTS")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)
        
        # Use user's temp directory for audio files
        self.audio_file = os.path.join(os.getcwd(), f"georgian_tts_{uuid.uuid4().hex}.wav")
        
        # Audio worker thread
        self.audio_worker = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title
        title_label = self.create_title_label()
        main_layout.addWidget(title_label, 0, 0, 1, 2)

        # Create panels
        left_panel = self.create_text_input_panel()
        right_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1, 0)
        main_layout.addWidget(right_panel, 1, 1)

        # Status bar
        self.status_label = self.create_status_bar()
        main_layout.addWidget(self.status_label, 2, 0, 1, 2)
    
    def create_title_label(self):
        label = QLabel(STRINGS["title"])
        label.setFont(QFont(TITLE_FONT_FAMILY, TITLE_FONT_SIZE, TITLE_FONT_WEIGHT))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def create_status_bar(self):
        label = QLabel(STRINGS["status_ready"])
        label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedHeight(STATUS_BAR_HEIGHT)
        return label
    
    def create_text_input_panel(self):
        """Create the text input panel"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        # Input label
        input_label = self.create_input_label()
        layout.addWidget(input_label)

        # Text editor
        self.text_edit = self.create_text_editor()
        layout.addWidget(self.text_edit)

        # Controls
        controls_layout = self.create_controls_layout()
        layout.addLayout(controls_layout)

        return frame

    def create_input_label(self):
        label = QLabel(STRINGS["input_label"])
        label.setFont(QFont(INPUT_LABEL_FONT_FAMILY, INPUT_LABEL_FONT_SIZE, INPUT_LABEL_FONT_WEIGHT))
        return label

    def create_text_editor(self):
        return GeorgianTextEdit()

    def create_controls_layout(self):
        controls_layout = QHBoxLayout()

        # Georgian mode checkbox
        self.mode_checkbox = QCheckBox(STRINGS["georgian_mode"])
        self.mode_checkbox.stateChanged.connect(self.toggle_georgian_mode)
        controls_layout.addWidget(self.mode_checkbox)

        controls_layout.addSpacing(20)

        # Font selector
        controls_layout.addWidget(QLabel(STRINGS["font"]))
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Sylfaen", "BPG Arial", "BPG Nino Mtavruli", 
            "DejaVu Sans", "Arial Unicode MS", "Noto Sans Georgian"
        ])
        self.font_combo.currentTextChanged.connect(self.change_font)
        self.font_combo.setFixedWidth(150)
        controls_layout.addWidget(self.font_combo)

        # Add keyboard shortcut info label
        shortcut_label = QLabel(STRINGS["shortcut_keyboard"])
        shortcut_label.setStyleSheet("color: #555; font-size: 10px;")
        controls_layout.addWidget(shortcut_label)

        controls_layout.addStretch()

        # Add keyboard shortcut for virtual keyboard
        self.text_edit.shortcut_keyboard = QAction(self)
        self.text_edit.shortcut_keyboard.setShortcut("Ctrl+K")
        self.text_edit.shortcut_keyboard.triggered.connect(self.show_keyboard)
        self.addAction(self.text_edit.shortcut_keyboard)

        return controls_layout
    
    def create_control_panel(self):
        """Create the control panel"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        # Remove all prosody controls

        layout.addSpacing(15)

        # File operations
        self.add_section(layout, STRINGS["file_ops"], [
            (STRINGS["load_file"], self.load_file),
            (STRINGS["clear_text"], self.clear_text)
        ])

        layout.addSpacing(15)

        # Input tools
        self.add_section(layout, STRINGS["input_tools"], [
            (STRINGS["keyboard"], self.show_keyboard),
            (STRINGS["sample_text"], self.insert_sample)
        ])

        layout.addSpacing(15)

        # Audio generation
        audio_buttons = [
            (STRINGS["save_audio"], self.save_audio),
            (STRINGS["generate_audio"], self.generate_audio)
        ]
        if HAS_PYDUB:
            audio_buttons.insert(-1, (STRINGS["play_audio"], self.play_audio))
        self.add_section(layout, STRINGS["audio_gen"], audio_buttons)

        # Show missing dependencies
        self.add_missing_deps_info(layout)

        layout.addStretch()
        return frame

    def add_section(self, parent_layout, title, buttons):
        label = self.create_section_label(title)
        parent_layout.addWidget(label)
        button_layout = self.create_button_layout(buttons)
        parent_layout.addLayout(button_layout)

    def create_section_label(self, title):
        label = QLabel(title)
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        return label

    def create_button_layout(self, buttons):
        button_layout = QVBoxLayout()
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setFixedWidth(150)
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)
        return button_layout

    def add_missing_deps_info(self, layout):
        missing_deps = []
        if not HAS_PYDUB:
            missing_deps.append(STRINGS["pydub_missing"])
        if not HAS_PDF:
            missing_deps.append(STRINGS["pdf_missing"])
        if not HAS_DOCX:
            missing_deps.append(STRINGS["docx_missing"])
        if missing_deps:
            layout.addSpacing(15)
            deps_label = QLabel(STRINGS["missing_deps"])
            deps_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            deps_label.setStyleSheet("color: red;")
            layout.addWidget(deps_label)
            for dep in missing_deps:
                dep_label = QLabel(f"• {dep}")
                dep_label.setStyleSheet("color: red; font-size: 9px;")
                layout.addWidget(dep_label)
    
    def toggle_georgian_mode(self, state):
        """Toggle Georgian input mode"""
        mode = self.text_edit.toggle_georgian()
        self.status_label.setText(STRINGS["status_georgian_on"] if mode else STRINGS["status_georgian_off"])
    
    def change_font(self, font_name):
        """Change text editor font"""
        self.text_edit.set_font(font_name)
        self.status_label.setText(STRINGS["status_font_changed"].format(font=font_name))
    
    def load_file(self):
        """Load text from file"""
        file_types = []
        if HAS_PDF or HAS_DOCX:
            file_types.append(STRINGS["all_files"])
        file_path, _ = QFileDialog.getOpenFileName(
            self, STRINGS["open_file"], "", ";;".join(file_types)
        )
        if not file_path:
            return
        try:
            content = self.read_file_content(file_path)
            self.text_edit.setPlainText(content)
            self.status_label.setText(STRINGS["status_loaded"].format(file=os.path.basename(file_path)))
        except ValueError as ve:
            QMessageBox.critical(self, STRINGS["error"], f"Could not load file:\n{str(ve)}")
        except ImportError as ie:
            QMessageBox.critical(self, STRINGS["missing_dependency"], f"{str(ie)}\nPlease install the required package.")
        except Exception as e:
            QMessageBox.critical(self, STRINGS["error"], f"Could not load file:\n{str(e)}")

    def read_file_content(self, file_path):
        """Read content from different file types"""
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Could not read text file: {e}")
        elif file_ext == '.pdf':
            if not HAS_PDF or PyPDF2 is None:
                raise ImportError("PyPDF2 is required to open PDF files.")
            try:
                reader = PyPDF2.PdfReader(file_path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                raise ValueError(f"Could not read PDF file: {e}")
        elif file_ext == '.docx':
            if not HAS_DOCX or docx is None:
                raise ImportError("python-docx is required to open DOCX files.")
            try:
                doc = docx.Document(file_path)
                return "\n".join(para.text for para in doc.paragraphs)
            except Exception as e:
                raise ValueError(f"Could not read DOCX file: {e}")
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def clear_text(self):
        """Clear all text after confirmation"""
        reply = QMessageBox.question(
            self, STRINGS["confirm"], STRINGS["warning_clear_text"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.text_edit.clear()
            self.status_label.setText(STRINGS["status_text_cleared"])
    
    def show_keyboard(self):
        """Show virtual Georgian keyboard"""
        keyboard_dialog = GeorgianKeyboardDialog(self, self.text_edit)
        keyboard_dialog.exec()
    
    def insert_sample(self):
        """Insert sample Georgian text"""
        self.text_edit.insertPlainText(SAMPLE_TEXT)
        self.status_label.setText(STRINGS["status_sample_inserted"])
    
    def generate_audio(self):
        """Generate audio from text"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, STRINGS["warning_enter_text"], STRINGS["warning_enter_text"])
            return
        for char in text:
            if char.isalpha():
                if char not in Georgian_Alphabet[0]:
                    QMessageBox.warning(self, STRINGS["warning_enter_text"], STRINGS["warning_enter_text"])
                    return

        
        try:
            self.status_label.setText(STRINGS["status_db"])
            QApplication.processEvents()
            populate_syllable_db()
            self.status_label.setText(STRINGS["status_preprocess"])
            QApplication.processEvents()
            # Use preprocess_and_syllabify and synthesize_speech as in the current Functions.py
            syllables = preprocess_and_syllabify(text)
            # Check for missing syllables before synthesis
            from db import get_syllable_audio_path
            missing = set()
            for syl in syllables:
                if syl == "<s>" or syl == "<eos>":
                    continue
                if not get_syllable_audio_path(syl):
                    missing.add(syl)
            if missing:
                missing_str = ", ".join(sorted(missing))
                QMessageBox.warning(self, STRINGS["warning_missing_syllables"],
                                    STRINGS["warning_missing_syllables"].format(syllables=missing_str))
                return
                        
            audio = synthesize_speech(syllables)
            audio.export(self.audio_file, format="wav")
            self.status_label.setText(STRINGS["status_audio_success"])
            QMessageBox.information(self, STRINGS["success"], STRINGS["status_audio_success"])
        except Exception as e:
            self.status_label.setText(STRINGS["status_audio_error"])
            QMessageBox.critical(self, STRINGS["error"], f"{STRINGS['status_audio_error']}\n{str(e)}")
    
    def play_audio(self):
        """Play generated audio"""
        if not os.path.exists(self.audio_file):
            QMessageBox.warning(self, STRINGS["warning_generate_audio"], STRINGS["warning_generate_audio"])
            return
        if self.audio_worker and self.audio_worker.isRunning():
            QMessageBox.information(self, STRINGS["info"], STRINGS["status_playing"])
            return
        self.audio_worker = AudioWorker('play', self.audio_file)
        self.audio_worker.finished.connect(self.on_audio_finished)
        self.audio_worker.progress.connect(self.status_label.setText)
        self.status_label.setText(STRINGS["status_playing"])
        self.audio_worker.start()
    
    def on_audio_finished(self, success, message):
        """Handle audio operation completion"""
        if success:
            self.status_label.setText(STRINGS["status_play_done"])
        else:
            self.status_label.setText(STRINGS["status_play_error"])
            QMessageBox.critical(self, STRINGS["error"], f"{STRINGS['status_play_error']}\n{message}")
    
    def save_audio(self):
        """Save generated audio to file"""
        if not os.path.exists(self.audio_file):
            QMessageBox.warning(self, STRINGS["warning_generate_audio"], STRINGS["warning_generate_audio"])
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, STRINGS["save_audio_file"], AUDIO_FILE_NAME, 
            STRINGS["wav_files"]
        )
        if not file_path:
            return
        try:
            self.copy_file_safely(self.audio_file, file_path)
            filename = os.path.basename(file_path)
            self.status_label.setText(STRINGS["status_audio_saved"].format(file=filename))
            QMessageBox.information(self, STRINGS["success"], STRINGS["status_audio_saved_success"])
        except PermissionError:
            QMessageBox.critical(self, STRINGS["error"], STRINGS["status_permission_error"])
        except Exception as e:
            QMessageBox.critical(self, STRINGS["error"], f"{STRINGS['status_audio_saved']}\n{str(e)}")
    
    def copy_file_safely(self, source, destination):
        """Safely copy file with proper error handling"""
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.copy2(source, destination)
                return
                
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise e
    
    def closeEvent(self, event):
        """Clean up when closing the application"""
        if self.audio_worker and self.audio_worker.isRunning():
            self.audio_worker.terminate()
            self.audio_worker.wait()
        
        if os.path.exists(self.audio_file):
            try:
                os.remove(self.audio_file)
            except OSError:
                pass
        
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = ModernGeorgianTTS()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()