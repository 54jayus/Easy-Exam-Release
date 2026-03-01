import os
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal, QSize, QEvent, QUrl, QMimeData
from PyQt5.QtGui import QCursor, QIcon, QPixmap, QPainter, QColor, QPainterPath, QKeySequence, QTextDocument, QImage, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QComboBox,
    QGroupBox,
    QScrollArea,
    QScroller,
    QSizePolicy,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
    QSizeGrip,
)

from ..ai.assistant_engine import AssistantEngine
from ..ai.assistant_worker import AssistantWorker

# 1. SVG Icons & Styles Helper
# ==================================================================================

class SvgIcon:
    """Helper to create QIcon from SVG path data"""
    
    # Path data constants
    PATH_SEND = "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"
    PATH_ATTACH = "M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5a2.5 2.5 0 0 1 5 0v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5a2.5 2.5 0 0 0 5 0V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"
    PATH_CLOSE = "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
    PATH_MINIMIZE = "M19 13H5v-2h14v2z"
    PATH_FLOAT = "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-5.04-6.71l-2.75 2.75 1.16 1.16 2.75-2.75v1.86h1.64v-4.66h-4.66v1.64h1.86z"
    PATH_RESTORE = "M12 8l-6 6 1.41 1.41L12 10.83l4.59 4.58L18 14z"
    PATH_TRASH = "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"
    PATH_CLEAR_X = "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
    PATH_ROBOT = "M21.05 13.56c-.53-1.07-1.39-1.92-2.46-2.46l.01-.01c.71-.24 1.34-.69 1.8-1.28.46-.59.66-1.33.56-2.07-.15-1.14-1.07-2.06-2.21-2.21-.74-.1-1.48.1-2.07.56-.59.46-1.04 1.09-1.28 1.8l-.01-.01C14.85 7.34 14 6.48 12.93 5.95l1.6-2.77c.1-.17.04-.4-.13-.5l-.87-.5c-.17-.1-.4-.04-.5.13L11.39 5.2c-.46-.07-.93-.1-1.39-.1s-.93.04-1.39.1L6.97 2.31c-.1-.17-.33-.23-.5-.13l-.87.5c-.17.1-.23.33-.13.5l1.6 2.77c-1.07.53-1.92 1.39-2.46 2.46l-.01.01c-.71.24-1.34.69-1.8 1.28-.46.59-.66 1.33-.56 2.07.15 1.14 1.07 2.06 2.21 2.21.74.1 1.48-.1 2.07-.56.59-.46 1.04-1.09 1.28-1.8l.01.01c.53 1.07 1.39 1.92 2.46 2.46-.24.71-.69 1.34-1.28 1.8-.59.46-1.33.66-2.07.56-1.14-.15-2.06-1.07-2.21-2.21-.1-.74.1-1.48.56-2.07.46-.59 1.09-1.04 1.8-1.28l-.01-.01c-.53-1.07-1.39-1.92-2.46-2.46l-1.6 2.77c-.1.17-.33.23-.5.13l-.87-.5c-.17-.1-.23-.33-.13-.5l1.6-2.77c-1.07-.53-1.92-1.39-2.46-2.46C2.25 14.34 1 12.18 1 10c0-2.18 1.25-4.34 3.39-5.11l-.01.01c-.24-.71-.69-1.34-1.28-1.8-.59-.46-1.33-.66-2.07-.56-1.14.15-2.06 1.07-2.21 2.21-.1.74.1 1.48.56 2.07.46.59 1.09 1.04 1.8 1.28l-.01.01c.53 1.07 1.39 1.92 2.46 2.46l1.6-2.77c.1-.17.33-.23.5-.13l.87.5c.17.1.23.33.13.5l-1.6 2.77c1.07.53 1.92 1.39 2.46 2.46l.01-.01c.71-.24 1.34-.69 1.8-1.28.46-.59.66-1.33.56-2.07-.15-1.14-1.07-2.06-2.21-2.21-.74-.1-1.48.1-2.07.56-.59.46-1.04 1.09-1.28 1.8l-.01.01c-.53-1.07-1.39-1.92-2.46-2.46.24-.71.69-1.34 1.28-1.8.59-.46 1.33-.66 2.07-.56 1.14.15 2.06 1.07 2.21 2.21.1.74-.1 1.48-.56 2.07-.46.59-1.09 1.04-1.8 1.28l.01.01c.53 1.07 1.39 1.92 2.46 2.46l1.6-2.77c.1-.17.33-.23.5-.13l.87.5c.17.1.23.33.13.5L21.05 13.56z"
    PATH_BRAIN = "M12 2L14 8L22 12L14 16L12 22L10 16L2 12L10 8Z"  # 4-pointed star
    PATH_USER = "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
    PATH_SPARKLES = "M9 21c0-5.52-4.48-10-10-10 5.52 0 10-4.48 10-10 0 5.52 4.48 10 10 10-5.52 0-10 4.48-10 10zm-1.25-6.75c.75 2.06 1.25 4.75 1.25 4.75s.5-2.69 1.25-4.75c2.06-.75 4.75-1.25 4.75-1.25s-2.69-.5-4.75-1.25C9.75 9.69 9.25 7 9.25 7s-.5 2.69-1.25 4.75c-2.06.75-4.75 1.25-4.75 1.25s2.69.5 4.75 1.25z"
    PATH_EXCEL = "M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" # Simplified Doc
    PATH_PDF = "M20 2H8c-1.1 0-2 .9-2 2v12H20V2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v.5zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"
    PATH_IMAGE = "M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"

    @staticmethod
    def icon(path_data, color="#5F6368", size=24):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        
        # Simple SVG path parser (supports M, L, H, V, Z, C, S, A etc. roughly)
        # But for Qt's QPainterPath, we better use a simpler approach if we don't want a full parser.
        # Actually, let's assume the path data is standard SVG and Qt can't parse it directly without QSvgRenderer.
        # To avoid adding QtSvg dependency (which might be missing), we will use a workaround:
        # We'll use a simple unicode char fallback OR rely on the fact that most simple icons 
        # can be drawn with text if we had a font, but here we don't.
        # 
        # WAIT: PyQt5.QtGui.QPainterPath does NOT parse SVG string directly. 
        # For "Minimal Dependency", we should use QSvgRenderer if available, OR just draw simple shapes.
        # Let's try to import QSvgRenderer. If not, fallback to text.
        
        try:
            from PyQt5.QtSvg import QSvgRenderer
            from PyQt5.QtCore import QByteArray
            svg_content = f'<svg viewBox="0 0 24 24" fill="{color}"><path d="{path_data}"/></svg>'
            renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
            renderer.render(painter)
        except ImportError:
            # Fallback: Draw a circle
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 4, size-8, size-8)
            
        painter.end()
        return QIcon(pixmap)

# ==================================================================================
# 2. UI Components
# ==================================================================================

class ModernTitleBar(QWidget):
    """Custom frameless title bar with drag support"""
    def __init__(self, parent, title="AI 助手", on_close=None, on_minimize=None, on_settings=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self._parent = parent
        self._drag_pos = None
        self._on_minimize = on_minimize
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        
        # Logo
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(SvgIcon.icon(SvgIcon.PATH_BRAIN, "#3B82F6", 24).pixmap(24, 24))
        layout.addWidget(self.icon_lbl)
        
        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #1F2937;")
        layout.addWidget(self.title_lbl)
        
        layout.addStretch()
        
        # Controls
        # Settings Button
        self.btn_settings = QToolButton()
        # Use a simple gear icon path if available, otherwise reuse another or draw dots
        PATH_SETTINGS = "M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.06-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.06,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"
        self.btn_settings.setIcon(SvgIcon.icon(PATH_SETTINGS, "#6B7280", 18))
        self.btn_settings.setToolTip("API 设置")
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setStyleSheet("QToolButton { border: none; background: transparent; border-radius: 4px; } QToolButton:hover { background: #E5E7EB; }")
        if on_settings:
            self.btn_settings.clicked.connect(on_settings)
        layout.addWidget(self.btn_settings)

        self.btn_min = QToolButton()
        self.btn_min.setIcon(SvgIcon.icon(SvgIcon.PATH_FLOAT, "#6B7280", 18))
        self.btn_min.setToolTip("切换浮窗")
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.setStyleSheet("QToolButton { border: none; background: transparent; border-radius: 4px; } QToolButton:hover { background: #E5E7EB; }")
        if on_minimize:
            self.btn_min.clicked.connect(on_minimize)
        layout.addWidget(self.btn_min)
        
        self.btn_close = QToolButton()
        self.btn_close.setIcon(SvgIcon.icon(SvgIcon.PATH_CLOSE, "#6B7280", 18))
        self.btn_close.setToolTip("关闭")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("QToolButton { border: none; background: transparent; border-radius: 4px; } QToolButton:hover { background: #EF4444; }")
        if on_close:
            self.btn_close.clicked.connect(on_close)
        layout.addWidget(self.btn_close)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self._on_minimize:
            self._on_minimize()
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self._parent.move(event.globalPos() - self._drag_pos)
            event.accept()

class ChatBubble(QFrame):
    """Modern chat bubble with asymmetric border radius and avatar"""
    def __init__(self, text, is_user=False, ts_text=None, attachments=None):
        super().__init__()
        self._text = text
        self.is_user = is_user
        self._ts_text = ts_text or ""
        self._attachments = attachments or []
        
        # Main layout: Row (Avatar + Bubble)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 6, 0, 6)
        main_layout.setSpacing(10)
        
        # Avatar
        self.avatar = QLabel()
        self.avatar.setFixedSize(32, 32)
        self.avatar.setStyleSheet("border-radius: 16px; background-color: #F3F4F6;")
        self.avatar.setAlignment(Qt.AlignCenter)
        
        # Bubble Container
        self.bubble_frame = QFrame()
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(14, 10, 14, 8)
        bubble_layout.setSpacing(8) # Increased spacing for attachments
        
        # Attachments Display (New)
        if self._attachments:
            att_layout = QHBoxLayout()
            att_layout.setSpacing(8)
            att_layout.setAlignment(Qt.AlignLeft)
            
            for path in self._attachments:
                # Reuse AttachmentChip logic but static (no close button needed)
                # Or create a simpler view. 
                # Let's use AttachmentChip but we need to hide close button or ignore it.
                # Actually, AttachmentChip is designed for the input.
                # Let's create a "ReadOnlyAttachmentChip" or just modify AttachmentChip to accept read_only flag.
                # For now, let's just use AttachmentChip but ensure the close button (which we just added) is hidden or handled.
                # Wait, I added the close button as a child widget in __init__.
                # I can hide it.
                
                chip = AttachmentChip(path)
                chip.close_btn.hide() # Hide the X button
                if is_user:
                    chip.set_theme(is_dark_bg=True)
                att_layout.addWidget(chip)
                
            att_layout.addStretch()
            bubble_layout.addLayout(att_layout)
        
        if self._text:
            self.lbl = QLabel(text)
            self.lbl.setWordWrap(True)
            self.lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            font = self.lbl.font()
            font.setPointSize(10)
            self.lbl.setFont(font)
            bubble_layout.addWidget(self.lbl)
        
        if self._ts_text:
            ts = QLabel(self._ts_text)
            ts.setStyleSheet("color: rgba(255,255,255,0.7);" if is_user else "color: #9CA3AF;")
            ts_font = ts.font()
            ts_font.setPointSize(8)
            ts.setFont(ts_font)
            ts.setAlignment(Qt.AlignRight)
            bubble_layout.addWidget(ts)
        
        if is_user:
            # User: [Stretch] [Bubble] [Avatar]
            self.avatar.setPixmap(SvgIcon.icon(SvgIcon.PATH_USER, "#6B7280", 20).pixmap(20, 20))
            
            self.bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: #2563EB;
                    border-radius: 12px;
                    border-top-right-radius: 2px;
                }
            """)
            if hasattr(self, 'lbl'):
                self.lbl.setStyleSheet("color: #FFFFFF;")
            
            main_layout.addStretch()
            main_layout.addWidget(self.bubble_frame)
            main_layout.addWidget(self.avatar, 0, Qt.AlignTop)
            
        else:
            # Bot: [Avatar] [Bubble] [Stretch]
            self.avatar.setPixmap(SvgIcon.icon(SvgIcon.PATH_BRAIN, "#2563EB", 20).pixmap(20, 20))
            self.avatar.setStyleSheet("border-radius: 16px; background-color: #EFF6FF;")
            
            self.bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: none;
                    border-radius: 12px;
                    border-top-left-radius: 2px;
                }
            """)
            if hasattr(self, 'lbl'):
                self.lbl.setStyleSheet("color: #1F2937;")
            
            # Subtler shadow
            shadow = QGraphicsDropShadowEffect(self.bubble_frame)
            shadow.setBlurRadius(12)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 20)) # Increased opacity for visibility on white
            self.bubble_frame.setGraphicsEffect(shadow)
            
            main_layout.addWidget(self.avatar, 0, Qt.AlignTop)
            main_layout.addWidget(self.bubble_frame)
            main_layout.addStretch()
            
        self.setToolTip("")

    # Removed mouseDoubleClickEvent to disable copy on double click

class TypingIndicator(QFrame):
    """Bouncing dots loading animation"""
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(10)
        
        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet("border-radius: 16px; background-color: #EFF6FF;")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setPixmap(SvgIcon.icon(SvgIcon.PATH_BRAIN, "#2563EB", 20).pixmap(20, 20))
        layout.addWidget(avatar, 0, Qt.AlignTop)
        
        # Bubble
        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 12px;
                border-top-left-radius: 2px;
            }
        """)
        # Shadow for typing indicator
        shadow = QGraphicsDropShadowEffect(bubble)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 20))
        bubble.setGraphicsEffect(shadow)

        b_layout = QHBoxLayout(bubble)
        b_layout.setContentsMargins(12, 10, 12, 10)
        b_layout.setSpacing(4)
        
        self.dots = []
        for _ in range(3):
            dot = QLabel("•")
            dot.setStyleSheet("color: #9CA3AF; font-size: 24px; line-height: 10px;")
            b_layout.addWidget(dot)
            self.dots.append(dot)
            
        layout.addWidget(bubble)
        layout.addStretch()
        
        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(300)
        self.step = 0
        
    def _animate(self):
        self.step = (self.step + 1) % 4
        for i, dot in enumerate(self.dots):
            if i == self.step:
                dot.setStyleSheet("color: #3B82F6; font-size: 24px; font-weight: bold;")
            else:
                dot.setStyleSheet("color: #9CA3AF; font-size: 24px;")

class AttachmentChip(QFrame):
    """Small chip for attachment file"""
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.setFixedSize(80, 80)
        self.setStyleSheet("""
            AttachmentChip {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(4)
        
        # Determine icon/thumbnail
        ext = os.path.splitext(path)[1].lower()
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            # Image Thumbnail
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.icon_lbl.setPixmap(pix)
            else:
                self.icon_lbl.setPixmap(SvgIcon.icon(SvgIcon.PATH_IMAGE, "#6B7280", 40).pixmap(40, 40))
        elif ext in ['.xlsx', '.xls', '.csv']:
            self.icon_lbl.setPixmap(SvgIcon.icon(SvgIcon.PATH_EXCEL, "#10B981", 40).pixmap(40, 40))
        elif ext in ['.pdf']:
            self.icon_lbl.setPixmap(SvgIcon.icon(SvgIcon.PATH_PDF, "#EF4444", 40).pixmap(40, 40))
        else:
            self.icon_lbl.setPixmap(SvgIcon.icon(SvgIcon.PATH_ATTACH, "#6B7280", 40).pixmap(40, 40))
            
        layout.addWidget(self.icon_lbl)
        
        name = os.path.basename(path)
        if len(name) > 8:
            name = name[:4] + "..." + name[-3:]
            
        lbl = QLabel(name)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #374151; font-size: 11px;")
        layout.addWidget(lbl)
        
        # We need to paint the Close button onto the chip, 
        # so it appears in the pixmap.
        # But a child widget like QToolButton might not render perfectly 
        # if we just use chip.render(pixmap) unless we force show it.
        # Let's add a visible close label/button
        
        self.close_btn = QLabel(self)
        self.close_btn.setFixedSize(16, 16)
        # Draw a simple X circle
        pm = QPixmap(16, 16)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(200, 200, 200, 200)) # Semi-transparent gray
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 16, 16)
        p.setPen(QColor("#FFFFFF"))
        p.drawLine(5, 5, 11, 11)
        p.drawLine(11, 5, 5, 11)
        p.end()
        self.close_btn.setPixmap(pm)
        self.close_btn.move(60, 4) # Top right corner

    def set_theme(self, is_dark_bg=False):
        if is_dark_bg:
            self.setStyleSheet("""
                AttachmentChip {
                    background-color: transparent;
                    border: none;
                }
                AttachmentChip:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                }
            """)
            # Find all child labels and set color to white
            for child in self.findChildren(QLabel):
                # Don't change close button if it has its own style, but here it's fine
                # Close button is drawn with pixmap, so color style doesn't affect it directly except font
                # But we have name label and icon label.
                # Icon label uses pixmap, so font color doesn't matter.
                # Name label matters.
                if child is not self.close_btn and child is not self.icon_lbl:
                     child.setStyleSheet("color: #FFFFFF; font-size: 11px;")
        else:
            self.setStyleSheet("""
                AttachmentChip {
                    background-color: #FFFFFF;
                    border-radius: 8px;
                    border: 1px solid #E5E7EB;
                }
                AttachmentChip:hover {
                    background-color: #F9FAFB;
                    border-color: #D1D5DB;
                }
            """)
            for child in self.findChildren(QLabel):
                if child is not self.close_btn and child is not self.icon_lbl:
                     child.setStyleSheet("color: #374151; font-size: 11px;")

# ==================================================================================
# 3. Main Dialog
# ==================================================================================

class ChatInputEdit(QTextEdit):
    """Custom TextEdit to handle Drag&Drop and Paste correctly"""
    submit_requested = pyqtSignal()
    attachments_received = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True) # Enable mouse tracking for hover effects

    def mouseMoveEvent(self, e):
        # 1. Get cursor at mouse position
        cursor = self.cursorForPosition(e.pos())
        
        # 2. Check if we are hovering over an image
        fmt = cursor.charFormat()
        if fmt.isImageFormat():
            img_fmt = fmt.toImageFormat()
            path = img_fmt.name()
            if path and os.path.exists(path):
                # We are over an attachment
                
                # Check if over the "Close" button area (Top Right ~20x20)
                # We need the rect of the image in viewport coordinates
                rect = self.cursorRect(cursor)
                
                # Check relative position
                rel_pos = e.pos() - rect.topLeft()
                
                # Assuming chip size is ~80x80, close button is at (60, 4) size 16x16
                # Let's give it a slightly larger hit area
                if 55 <= rel_pos.x() <= 80 and 0 <= rel_pos.y() <= 25:
                    self.viewport().setCursor(Qt.PointingHandCursor)
                    self.setToolTip("点击删除")
                else:
                    self.viewport().setCursor(Qt.ArrowCursor)
                    self.setToolTip(os.path.basename(path)) # Show filename
            else:
                self.viewport().setCursor(Qt.IBeamCursor)
                self.setToolTip("")
        else:
            self.viewport().setCursor(Qt.IBeamCursor)
            self.setToolTip("")
            
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            cursor = self.cursorForPosition(e.pos())
            fmt = cursor.charFormat()
            if fmt.isImageFormat():
                img_fmt = fmt.toImageFormat()
                path = img_fmt.name()
                if path and os.path.exists(path):
                    rect = self.cursorRect(cursor)
                    rel_pos = e.pos() - rect.topLeft()
                    
                    # Hit test for close button
                    if 55 <= rel_pos.x() <= 80 and 0 <= rel_pos.y() <= 25:
                        # Delete the attachment
                        # We need to select it and remove it
                        # The cursor returned by cursorForPosition is typically 'between' characters or at the character.
                        # To delete the image, we need to select the image character.
                        # It seems cursor is at the position of the character.
                        
                        # Let's verify cursor position logic. 
                        # If we click ON the image, cursorForPosition gives us the position.
                        # We can select the character to the right (or left depending on exact hit).
                        # Actually, let's just select the range of this image.
                        
                        # cursor position is just an index.
                        # We need to find where this image is.
                        # Actually, cursorForPosition returns a cursor *at* the position.
                        # If we are over the image, the cursor position might be *after* the image character if we are on the right half?
                        # No, let's use the cursor we got.
                        
                        # Trick: Select 1 character at this cursor's position?
                        # Or check if cursor is strictly at the start of the image?
                        
                        # Better way:
                        # Iterate to find the image range? No, slow.
                        
                        # Let's try:
                        c = self.cursorForPosition(e.pos())
                        # If we are "inside" the image char (conceptually), 
                        # cursor.position() usually returns the position *between* characters.
                        # But `cursorRect(c)` returns the rect of the character *following* the cursor?
                        # Wait, `cursorRect(cursor)`: "Returns the rectangle ... of the character *at* the cursor."
                        
                        # If we click on the image, we want to remove *that* image.
                        # Let's try to select the character *at* the cursor.
                        c.setPosition(c.position())
                        c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                        if c.charFormat().isImageFormat() and c.charFormat().toImageFormat().name() == path:
                            c.removeSelectedText()
                            self.setToolTip("")
                            self.viewport().setCursor(Qt.ArrowCursor)
                            return
                        
                        # If that didn't work (maybe cursor was at end of image), try Left
                        c = self.cursorForPosition(e.pos())
                        c.setPosition(c.position())
                        c.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
                        if c.charFormat().isImageFormat() and c.charFormat().toImageFormat().name() == path:
                            c.removeSelectedText()
                            self.setToolTip("")
                            self.viewport().setCursor(Qt.ArrowCursor)
                            return

        super().mouseReleaseEvent(e)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            paths = []
            for url in e.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    paths.append(path)
            
            if paths:
                self.attachments_received.emit(paths)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not (e.modifiers() & Qt.ShiftModifier):
            self.submit_requested.emit()
        else:
            super().keyPressEvent(e)
            
    def insertFromMimeData(self, source):
        if source.hasUrls():
            paths = []
            for url in source.urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    paths.append(path)
            if paths:
                self.attachments_received.emit(paths)
                return

        if source.hasImage():
            img = source.imageData()
            qimg = None
            if isinstance(img, QImage):
                qimg = img
            elif isinstance(img, QPixmap):
                qimg = img.toImage()
            
            if qimg and not qimg.isNull():
                import tempfile
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                tmp_path = os.path.join(tempfile.gettempdir(), f"paste_{ts}.png")
                qimg.save(tmp_path, "PNG")
                self.attachments_received.emit([tmp_path])
                return

        super().insertFromMimeData(source)

class AiAssistantDialog(QDialog):
    request_send = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.Tool) # Tool makes it float nicely
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(600, 760) # Increased size to accommodate larger margins for shadow
        self.setAcceptDrops(True) # Enable Drag & Drop
        
        self._engine = AssistantEngine()
        self._thread = None
        self._history = []
        self._attachments = []
        self._is_compact = False
        self._normal_geo = None
        self._typing_indicator = None
        self._worker = None
        
        # Main layout container (needed for shadow effect on window)
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }
        """)
        
        # Shadow for the whole window
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20) # Slightly reduced blur to ensure it fits in margins
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        # Margins must be > blur radius + offset to prevent clipping/artifacts on layered windows
        main_layout.setContentsMargins(24, 24, 24, 24) 
        main_layout.addWidget(self.container)
        
        # Resize Grip
        self.grip = QSizeGrip(self)
        self.grip.resize(16, 16)
        
        # Toast timer
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(lambda: self.toast_lbl.hide())
        
        self._build_ui()
        self.request_send.connect(self._start_request)
        
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._on_app_quit)

    def resizeEvent(self, event):
        rect = self.rect()
        self.grip.move(rect.right() - 24, rect.bottom() - 24)
        super().resizeEvent(event)

    def _build_ui(self):
        # Global Scrollbar Style
        scrollbar_style = """
            QScrollBar:vertical {
                border: none;
                background: #F3F4F6;
                width: 6px;
                margin: 0px 0px 0px 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9CA3AF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #F3F4F6;
                height: 6px;
                margin: 0px 0px 0px 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background: #D1D5DB;
                min-width: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #9CA3AF;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Title Bar
        self.title_bar = ModernTitleBar(self, on_close=self.close, on_minimize=self.toggle_compact, on_settings=self.open_settings)
        layout.addWidget(self.title_bar)
        
        # 2. Chat Area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QFrame.NoFrame)
        self.chat_area.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }} {scrollbar_style}")
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(20, 14, 20, 14)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch(1) # Push content down (or up?) - Standard is push up.
        # Actually standard chat pushes up. So add stretch at top.
        # But we want empty state centered.
        
        self.chat_area.setWidget(self.chat_widget)
        layout.addWidget(self.chat_area, 1)
        
        # Empty State (Initial)
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setSpacing(12)
        empty_icon = QLabel()
        empty_icon.setPixmap(SvgIcon.icon(SvgIcon.PATH_SPARKLES, "#9CA3AF", 48).pixmap(48, 48))
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_title = QLabel("有什么可以帮你的？")
        empty_title.setAlignment(Qt.AlignCenter)
        empty_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #374151;")
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel("你可以直接提问，也可以添加 Excel / PDF / 图片 作为附件。")
        empty_desc.setAlignment(Qt.AlignCenter)
        empty_desc.setStyleSheet("color: #6B7280; font-size: 12px;")
        empty_layout.addWidget(empty_desc)
        
        # Quick prompts
        prompts = [
            ("教师模板必填项", "教师信息模板有哪些必填列？"),
            ("导入失败排查", "导入失败提示“无法导入文件”怎么办？"),
            ("打印入口在哪里", "准考证打印入口在哪里？")
        ]
        
        prompt_row = QHBoxLayout()
        prompt_row.addStretch()
        for label, text in prompts:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px;
                    padding: 6px 16px; color: #4B5563; font-size: 12px;
                }
                QPushButton:hover { background: #F3F4F6; border-color: #D1D5DB; }
            """)
            btn.clicked.connect(lambda _, t=text: self.use_quick_prompt(t))
            prompt_row.addWidget(btn)
        prompt_row.addStretch()
        empty_layout.addLayout(prompt_row)
        
        # Insert empty widget into chat layout temporarily? 
        # Better: Overlay it or just put it in the layout.
        # We will use a separate container in the chat layout for empty state.
        self.chat_layout.insertWidget(0, self.empty_widget)
        
        # 3. Input Area (Floating Card Style)
        self.input_container = QWidget()
        input_layout = QVBoxLayout(self.input_container)
        input_layout.setContentsMargins(16, 10, 16, 16)
        
        # Toast Label (Overlay)
        self.toast_lbl = QLabel(self)
        self.toast_lbl.setStyleSheet("""
            background-color: #1F2937; color: white; padding: 6px 12px; border-radius: 6px; font-size: 12px;
        """)
        self.toast_lbl.hide()
        
        # Input Card
        self.input_card = QFrame()
        self.input_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)
        # Lighter shadow
        input_shadow = QGraphicsDropShadowEffect(self.input_card)
        input_shadow.setBlurRadius(12)
        input_shadow.setOffset(0, 2)
        input_shadow.setColor(QColor(0, 0, 0, 8))
        self.input_card.setGraphicsEffect(input_shadow)
        
        card_layout = QVBoxLayout(self.input_card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        
        # Text Edit
        self.input_edit = ChatInputEdit()
        self.input_edit.setPlaceholderText("输入消息... (Enter 发送)")
        self.input_edit.setFixedHeight(120) # Increased height for inline images
        self.input_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_edit.setStyleSheet(f"QTextEdit {{ border: none; background: transparent; font-size: 14px; color: #1F2937; }} {scrollbar_style}")
        self.input_edit.textChanged.connect(self._on_input_changed)
        self.input_edit.submit_requested.connect(self.on_send_clicked)
        self.input_edit.attachments_received.connect(self._add_attachment_paths)
        card_layout.addWidget(self.input_edit)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 4, 0, 0)
        toolbar.setSpacing(8)
        
        self.btn_attach = QToolButton()
        self.btn_attach.setIcon(SvgIcon.icon(SvgIcon.PATH_ATTACH, "#6B7280", 20))
        self.btn_attach.setToolTip("添加附件")
        self.btn_attach.setCursor(Qt.PointingHandCursor)
        self.btn_attach.setStyleSheet("""
            QToolButton { border:none; background:transparent; padding: 4px; border-radius: 4px; }
            QToolButton:hover { background: #F3F4F6; }
        """)
        self.btn_attach.clicked.connect(self.add_attachments)
        toolbar.addWidget(self.btn_attach)
        
        toolbar.addStretch()
        
        self.btn_clear = QToolButton()
        self.btn_clear.setIcon(SvgIcon.icon(SvgIcon.PATH_TRASH, "#9CA3AF", 18))
        self.btn_clear.setToolTip("清空会话")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QToolButton { border:none; background:transparent; padding: 4px; border-radius: 4px; }
            QToolButton:hover { background: #F3F4F6; }
        """)
        self.btn_clear.clicked.connect(self.clear_conversation)
        toolbar.addWidget(self.btn_clear)
        
        self.btn_send = QPushButton()
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setFixedSize(32, 32)
        self.btn_send.setIcon(SvgIcon.icon(SvgIcon.PATH_SEND, "#FFFFFF", 16))
        self.btn_send.setIconSize(QSize(16, 16))
        self.btn_send.setEnabled(False)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; border: none; border-radius: 16px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #E5E7EB; }
        """)
        self.btn_send.clicked.connect(self.on_send_clicked)
        toolbar.addWidget(self.btn_send)
        
        card_layout.addLayout(toolbar)
        
        input_layout.addWidget(self.input_card)
        layout.addWidget(self.input_container)

    # ================= Logic =================
    
    def open_settings(self):
        from .api_setting_dialog import ApiSettingDialog
        dialog = ApiSettingDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Settings updated, we should reload the client
            # AssistantEngine initializes client in __init__, so we can either re-init engine or client
            if self._engine:
                # ZhipuChatClient loads key in __init__
                from ..ai.zhipu_client import ZhipuChatClient
                self._engine.client = ZhipuChatClient()
                self.show_toast("API 设置已更新")

    def show_toast(self, text, duration=2000):
        self.toast_lbl.setText(text)
        self.toast_lbl.adjustSize()
        # Center toast at bottom
        w = self.width()
        h = self.height()
        tw = self.toast_lbl.width()
        th = self.toast_lbl.height()
        self.toast_lbl.move((w - tw) // 2, h - th - 100)
        self.toast_lbl.show()
        self.toast_lbl.raise_()
        self.toast_timer.start(duration)

    def toggle_compact(self):
        main_layout = self.layout()
        shadow = self.container.graphicsEffect()

        if self._is_compact:
            # Restore
            self._is_compact = False
            self.title_bar.btn_min.setIcon(SvgIcon.icon(SvgIcon.PATH_FLOAT, "#6B7280", 18))
            self.title_bar.title_lbl.setText("AI 助手")
            
            self.chat_area.show()
            self.input_container.show()
            self.input_card.show()
            self.grip.show()
            
            # Restore container style
            self.container.setStyleSheet("""
                #container {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 16px;
                }
            """)
            
            # Restore margins and shadow
            main_layout.setContentsMargins(24, 24, 24, 24)
            if shadow:
                shadow.setBlurRadius(20)

            # Unlock height
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            
            self.resize(600, 760)
            if self._normal_geo:
                self.move(self._normal_geo.topLeft())
        else:
            # Minimize
            self._normal_geo = self.geometry()
            self._is_compact = True
            self.title_bar.btn_min.setIcon(SvgIcon.icon(SvgIcon.PATH_RESTORE, "#6B7280", 18))
            self.title_bar.title_lbl.setText("有什么可以帮你的？")
            
            self.chat_area.hide()
            self.input_container.hide()
            self.input_card.hide()
            self.grip.hide()
            
            # Compact style - Blue border and more rounded with hover effect
            self.container.setStyleSheet("""
                #container {
                    background-color: #FFFFFF;
                    border: 1px solid #3B82F6;
                    border-radius: 24px;
                }
                #container:hover {
                    background-color: #F8FAFC;
                    border: 1px solid #2563EB;
                }
            """)
            
            # Tighter margins for compact mode
            main_layout.setContentsMargins(10, 10, 10, 10)
            if shadow:
                shadow.setBlurRadius(10)

            # Force fixed height to prevent expansion
            # 48 (Title) + 20 (Margins) = 68
            self.setFixedHeight(68)
            self.resize(320, 68)
            self._move_next_to_button()

    def _move_next_to_button(self):
        """Move the float window next to the AI Assistant button in the main window"""
        parent = self.parent()
        target_btn = None
        
        # Try to find the button
        if parent and hasattr(parent, 'ai_assistant_btn'):
            target_btn = parent.ai_assistant_btn
        
        if target_btn and target_btn.isVisible():
            # Calculate position
            # Get button global position
            btn_pos = target_btn.mapToGlobal(target_btn.rect().bottomRight())
            
            # Align top-right of dialog to bottom-right of button
            # Add some margin
            x = btn_pos.x() - self.width() + 10 # Shift right slightly to align better with edge
            y = btn_pos.y() + 10 # 10px vertical spacing
            
            # Ensure it's on screen
            screen = QApplication.primaryScreen().availableGeometry()
            if x + self.width() > screen.right():
                x = screen.right() - self.width() - 10
            
            self.move(x, y)
        else:
            # Fallback to corner
            self._move_to_corner()

    def _move_to_corner(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - 320, screen.bottom() - 80)

    def _find_main_window(self):
        w = self.parent()
        while w is not None:
            if hasattr(w, "stacked_widget") and hasattr(w, "function_buttons"):
                return w
            w = w.parent()
        for w in QApplication.topLevelWidgets():
            if hasattr(w, "stacked_widget") and hasattr(w, "function_buttons"):
                return w
        return None

    def _build_ui_context_text(self):
        main = self._find_main_window()
        if main is None:
            return ""

        current_task = ""
        if hasattr(main, "current_task_label") and main.current_task_label is not None:
            current_task = (main.current_task_label.text() or "").strip()

        nav_items = []
        current_nav = ""
        for btn in getattr(main, "function_buttons", []) or []:
            try:
                text = (btn.text() or "").strip()
                if text:
                    nav_items.append(text)
                    if getattr(btn, "isChecked", lambda: False)():
                        current_nav = text
            except Exception:
                continue

        page_widget = None
        if hasattr(main, "stacked_widget") and main.stacked_widget is not None:
            try:
                page_widget = main.stacked_widget.currentWidget()
            except Exception:
                page_widget = None

        tabs = []
        selected_tree_items = []
        combos = []
        group_titles = []
        action_buttons = []

        root = page_widget or main

        for tab in root.findChildren(QTabWidget):
            if not tab.isVisible():
                continue
            idx = tab.currentIndex()
            if idx >= 0:
                t = (tab.tabText(idx) or "").strip()
                if t and t not in tabs:
                    tabs.append(t)
            if len(tabs) >= 3:
                break

        for tree in root.findChildren(QTreeWidget):
            if not tree.isVisible():
                continue
            item = tree.currentItem()
            if item is None:
                continue
            t = (item.text(0) or "").strip()
            if t and t not in selected_tree_items:
                selected_tree_items.append(t)
            if len(selected_tree_items) >= 2:
                break

        for cb in root.findChildren(QComboBox):
            if not cb.isVisible():
                continue
            t = (cb.currentText() or "").strip()
            if not t:
                continue
            name = (cb.objectName() or "").strip() or "下拉框"
            pair = f"{name}={t}"
            if pair not in combos:
                combos.append(pair)
            if len(combos) >= 4:
                break

        for gb in root.findChildren(QGroupBox):
            if not gb.isVisible():
                continue
            t = (gb.title() or "").strip()
            if t and t not in group_titles:
                group_titles.append(t)
            if len(group_titles) >= 4:
                break

        exclude = set(nav_items)
        exclude.add("AI助手")
        for btn in root.findChildren(QPushButton):
            if not btn.isVisible():
                continue
            t = (btn.text() or "").strip()
            if not t or t in exclude:
                continue
            if t not in action_buttons:
                action_buttons.append(t)
            if len(action_buttons) >= 12:
                break

        lines = []
        title = (main.windowTitle() or "").strip()
        if title:
            lines.append(f"窗口标题：{title}")
        if nav_items:
            nav = " / ".join(nav_items)
            lines.append(f"顶部导航：{nav}")
        if current_task:
            lines.append(f"{current_task}")
        elif current_nav:
            lines.append(f"当前模块：{current_nav}")
        if tabs:
            lines.append("当前子页：" + " / ".join(tabs))
        if group_titles:
            lines.append("可见区域：" + " / ".join(group_titles))
        if selected_tree_items:
            lines.append("当前选中：" + " / ".join(selected_tree_items))
        if combos:
            lines.append("当前筛选：" + "；".join(combos))
        if action_buttons:
            lines.append("可操作按钮：" + "、".join(action_buttons))

        text = "\n".join(lines).strip()
        if len(text) > 1200:
            text = text[:1200] + "…"
        return text

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                if self._is_valid_file(path):
                    paths.append(path)
                else:
                    self.show_toast(f"不支持的文件格式: {os.path.basename(path)}")
        
        if paths:
            self._add_attachment_paths(paths)
        event.acceptProposedAction()

    def _is_valid_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ['.xlsx', '.xls', '.csv', '.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif']

    def use_quick_prompt(self, text):
        self.input_edit.setPlainText(text)
        cursor = self.input_edit.textCursor()
        cursor.movePosition(cursor.End)
        self.input_edit.setTextCursor(cursor)
        self.input_edit.setFocus()

    def add_attachments(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择附件", "", "支持的文件 (*.xlsx *.xls *.csv *.pdf *.png *.jpg *.jpeg *.bmp *.gif)")
        self._add_attachment_paths(paths)

    def create_chip_pixmap(self, path):
        # Render the AttachmentChip widget to a pixmap
        chip = AttachmentChip(path)
        # Ensure layout happens
        chip.adjustSize()
        # Create pixmap
        pixmap = QPixmap(chip.size())
        pixmap.fill(Qt.transparent)
        chip.render(pixmap)
        return pixmap

    def _add_attachment_paths(self, paths):
        added = False
        cursor = self.input_edit.textCursor()
        
        for p in paths:
            if not self._is_valid_file(p):
                self.show_toast(f"不支持的文件格式: {os.path.basename(p)}")
                continue
            
            # Inline Image Insertion
            pixmap = self.create_chip_pixmap(p)
            
            # Register image resource so QTextEdit knows it
            # We use the file path as the resource name
            doc = self.input_edit.document()
            doc.addResource(QTextDocument.ImageResource, QUrl(p), pixmap)
            
            # Insert image
            cursor.insertImage(pixmap.toImage(), p)
            cursor.insertText(" ") # Add space after
            
            added = True
        
        if added:
            self.input_edit.setFocus()
        self._on_input_changed()

    def clear_conversation(self):
        if self._thread is not None:
            self.show_toast("正在生成回复，稍后再清空")
            return

        if self._typing_indicator:
            self._typing_indicator.deleteLater()
            self._typing_indicator = None

        empty = self.empty_widget
        if empty is not None:
            empty.hide()

        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            w = item.widget()
            if w is None:
                continue
            if w is empty:
                continue
            w.deleteLater()

        if empty is not None:
            self.chat_layout.addWidget(empty)
        self.chat_layout.addStretch(1)

        self.empty_widget.show()
        self._history = []
        # Clear inline attachments
        self.input_edit.clear()
        self._on_input_changed()

    def _on_input_changed(self):
        self._update_send_state()

    def _update_send_state(self):
        # Allow send if text is not empty or has inline images
        # We need to check if document has content
        has_content = not self.input_edit.document().isEmpty()
        self.btn_send.setEnabled(has_content)

    def on_send_clicked(self):
        # Extract text and attachments from document
        doc = self.input_edit.document()
        html = self.input_edit.toHtml()
        plain_text = self.input_edit.toPlainText().strip()
        
        # We need to find all images
        # Since we used paths as resource names, we can iterate image formats
        attachments = []
        
        block = doc.begin()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    if frag.charFormat().isImageFormat():
                        img_fmt = frag.charFormat().toImageFormat()
                        path = img_fmt.name()
                        if path and os.path.exists(path):
                            attachments.append(path)
                it += 1
            block = block.next()
            
        # If no text (only replacement chars) and no attachments, return
        if not plain_text and not attachments:
            return
            
        self.empty_widget.hide()
        
        # Add user bubble
        # For display, we can just use the HTML content if we want rich text bubble
        # BUT ChatBubble expects plain text currently.
        # Let's clean the replacement characters from plain_text for display
        display_text = plain_text.replace("\ufffc", "").strip()
        if not display_text and attachments:
            display_text = "" # Don't show text if only attachments
            
        ts = datetime.now().strftime("%H:%M")
        bubble = ChatBubble(display_text, is_user=True, ts_text=ts, attachments=attachments)
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Add to history
        self._history.append({"role": "user", "text": display_text}) # Should we store attachments in history?
        # The history sent to AI usually just needs text descriptions of attachments or the text.
        # For display history, we might need more, but _history is mainly for context.
        # If we just send text, it's fine.
        
        self.input_edit.clear()
        
        # Start Request
        self.set_busy(True)
        self.request_send.emit(display_text, attachments)

    def set_busy(self, busy):
        self.btn_send.setEnabled(not busy)
        self.input_edit.setEnabled(not busy)
        self.btn_attach.setEnabled(not busy)
        self.btn_clear.setEnabled(not busy)
        
        if busy:
            if not self._typing_indicator:
                self._typing_indicator = TypingIndicator()
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._typing_indicator)
                QTimer.singleShot(100, lambda: self.chat_area.verticalScrollBar().setValue(
                    self.chat_area.verticalScrollBar().maximum()))
        else:
            if self._typing_indicator:
                self._typing_indicator.deleteLater()
                self._typing_indicator = None

    def _start_request(self, text, attachments):
        # Check API Key first
        api_key = os.getenv("ZAI_API_KEY") or os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            # Try load from file as fallback, similar to client logic, but here just check simple env
            # Actually, let the client handle it, but if client fails, we catch it in worker.
            # But to be safe and give immediate feedback:
            from ..ai.zhipu_client import load_api_key
            if not load_api_key():
                self.on_fail("未检测到 API Key，请配置环境变量 ZAI_API_KEY 或 apikey.txt")
                self.set_busy(False)
                return

        if self._thread:
            return
        
        ui_context_text = self._build_ui_context_text()
        history = self._get_history()
        worker = AssistantWorker(self._engine, text, attachments, history, ui_context_text=ui_context_text)
        self._worker = worker
        self._thread = QThread(self)
        worker.moveToThread(self._thread)
        
        worker.finished.connect(self.on_reply)
        worker.failed.connect(self.on_fail)
        worker.finished.connect(self._thread.quit)
        worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.started.connect(worker.run)
        
        self._thread.start()

    def on_reply(self, text):
        # Clear typing indicator
        if self._typing_indicator:
            self._typing_indicator.deleteLater()
            self._typing_indicator = None
            
        ts = datetime.now().strftime("%H:%M")
        bubble = ChatBubble(text, is_user=False, ts_text=ts)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._history.append({"role": "assistant", "text": text})
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()))
        self.set_busy(False)

    def on_fail(self, err):
        # Clear typing indicator
        if self._typing_indicator:
            self._typing_indicator.deleteLater()
            self._typing_indicator = None
            
        self.on_reply(f"Error: {err}")

    def _cleanup_thread(self):
        if self._thread:
            self._thread.deleteLater()
            self._thread = None
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        self.set_busy(False)

    def _get_history(self):
        # Simplified history getter
        return [{"role": h["role"], "text": h["text"]} for h in self._history[-10:]]

    def _on_app_quit(self):
        if self._thread:
            self._thread.quit()
            self._thread.wait(1000)
