"""
UI Module
Futuristic HUD interface using PyQt6 with Iron Man style theme.
"""

import sys
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QGraphicsDropShadowEffect, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QRadialGradient


class AnimatedCircle(QFrame):
    """Animated circular indicator for listening/speaking state."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self.setMinimumSize(150, 150)
        
        # Animation properties
        self.pulse_radius = 75
        self.pulse_alpha = 100
        self.pulse_direction = 1  # 1 = expanding, -1 = contracting
        
        # Colors (Iron Man arc reactor style)
        self.center_color = QColor(0, 200, 255)  # Cyan/blue
        self.outer_color = QColor(255, 50, 50)   # Red
        
        # State
        self.is_active = False
        self.state = "idle"  # idle, listening, speaking
        
        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(30)  # ~33 FPS
    
    def _update_animation(self) -> None:
        """Update animation frame."""
        if self.is_active:
            self.pulse_radius += self.pulse_direction * 2
            self.pulse_alpha += self.pulse_direction * 5
            
            if self.pulse_radius >= 85 or self.pulse_radius <= 70:
                self.pulse_direction *= -1
            if self.pulse_alpha >= 200 or self.pulse_alpha <= 50:
                self.pulse_direction *= -1
        
        self.update()
    
    def set_state(self, state: str) -> None:
        """
        Set visual state.
        
        Args:
            state: 'idle', 'listening', or 'speaking'
        """
        self.state = state
        self.is_active = state in ["listening", "speaking"]
        
        if state == "listening":
            self.center_color = QColor(0, 255, 100)  # Green
        elif state == "speaking":
            self.center_color = QColor(255, 100, 50)  # Orange/red
        else:
            self.center_color = QColor(0, 200, 255)  # Cyan
        
        self.update()
    
    def paintEvent(self, event) -> None:
        """Custom paint for animated circle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Outer glow ring
        if self.is_active:
            gradient = QRadialGradient(center_x, center_y, self.pulse_radius)
            gradient.setColorAt(0, QColor(self.center_color.red(), 
                                         self.center_color.green(),
                                         self.center_color.blue(),
                                         self.pulse_alpha))
            gradient.setColorAt(1, QColor(self.center_color.red(), 
                                         self.center_color.green(),
                                         self.center_color.blue(), 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center_x - int(self.pulse_radius),
                              center_y - int(self.pulse_radius),
                              int(self.pulse_radius * 2),
                              int(self.pulse_radius * 2))
        
        # Center circle
        gradient = QRadialGradient(center_x, center_y, 60)
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.5, self.center_color)
        gradient.setColorAt(1, QColor(0, 50, 80))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - 60, center_y - 60, 120, 120)
        
        # Inner ring
        painter.setPen(QPen(self.center_color, 3))
        painter.setBrush(Qt.PenStyle.NoBrush)
        painter.drawEllipse(center_x - 45, center_y - 45, 90, 90)


class StatusLabel(QLabel):
    """Styled label for status text."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.setStyleSheet("""
            QLabel {
                color: #00C8FF;
                padding: 10px;
                background-color: rgba(0, 20, 40, 0.8);
                border: 1px solid #005577;
                border-radius: 5px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 200, 255, 150))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)


class TranscriptDisplay(QFrame):
    """Display area for conversation transcript."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 10, 20, 0.9);
                border: 1px solid #003344;
                border-radius: 8px;
            }
        """)
        self.setFixedHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.label = QLabel("Transcript will appear here...")
        self.label.setFont(QFont("Consolas", 11))
        self.label.setStyleSheet("color: #00FFAA; padding: 5px;")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(self.label)
    
    def update_transcript(self, text: str, is_user: bool = False) -> None:
        """Update displayed transcript."""
        prefix = "USER: " if is_user else "JARVIS: "
        color = "#FF8844" if is_user else "#00C8FF"
        
        self.label.setText(f'<span style="color: {color}; font-weight: bold;">{prefix}</span>{text}')


class SystemStatusPanel(QFrame):
    """Panel showing system status information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 15, 30, 0.8);
                border: 1px solid #004455;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("SYSTEM STATUS")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #FF4444;")
        layout.addWidget(title)
        
        # Status items
        self.status_items: Dict[str, QLabel] = {}
        
        for item in ["CPU", "Memory", "Network", "API"]:
            row = QHBoxLayout()
            
            name_label = QLabel(f"{item}:")
            name_label.setStyleSheet("color: #888888; font-size: 11px;")
            row.addWidget(name_label)
            
            value_label = QLabel("OK")
            value_label.setStyleSheet("color: #00FF88; font-size: 11px;")
            row.addWidget(value_label)
            row.addStretch()
            
            self.status_items[item.lower()] = value_label
            layout.addLayout(row)
    
    def update_status(self, component: str, status: str) -> None:
        """Update status for a component."""
        if component.lower() in self.status_items:
            label = self.status_items[component.lower()]
            label.setText(status)
            
            # Color code status
            if status.upper() == "OK":
                label.setStyleSheet("color: #00FF88; font-size: 11px;")
            elif status.upper() == "BUSY":
                label.setStyleSheet("color: #FFAA00; font-size: 11px;")
            else:
                label.setStyleSheet("color: #FF4444; font-size: 11px;")


class JarvisHUD(QMainWindow):
    """
    Main HUD window for Jarvis AI Assistant.
    Futuristic Iron Man inspired interface.
    """
    
    # Signals for thread-safe updates
    state_changed = pyqtSignal(str)
    transcript_update = pyqtSignal(str, bool)
    status_update = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("JARVIS - AI Assistant")
        self.setMinimumSize(500, 700)
        self.setMaximumSize(600, 800)
        
        # Apply dark theme
        self._apply_theme()
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self.state_changed.connect(self._on_state_changed)
        self.transcript_update.connect(self._on_transcript_update)
        self.status_update.connect(self._on_status_update)
    
    def _apply_theme(self) -> None:
        """Apply Iron Man style dark theme."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000510;
            }
        """)
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 5, 16))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 200, 255))
        self.setPalette(palette)
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title = QLabel("J.A.R.V.I.S.")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #FF4444, stop:0.5 #FF8800, stop:1 #FF4444);
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Just A Rather Very Intelligent System")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #666666; padding-bottom: 10px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Animated indicator
        self.indicator = AnimatedCircle()
        self.indicator.set_state("idle")
        main_layout.addWidget(self.indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.status_label = StatusLabel("Ready and listening")
        main_layout.addWidget(self.status_label)
        
        # Transcript display
        self.transcript = TranscriptDisplay()
        main_layout.addWidget(self.transcript)
        
        # System status panel
        self.system_status = SystemStatusPanel()
        main_layout.addWidget(self.system_status)
        
        # Footer
        footer = QLabel("Voice commands active • Say 'Jarvis' to activate")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: #444444; padding-top: 10px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)
    
    def set_state(self, state: str) -> None:
        """
        Set UI state (thread-safe).
        
        Args:
            state: 'idle', 'listening', or 'speaking'
        """
        self.state_changed.emit(state)
    
    def _on_state_changed(self, state: str) -> None:
        """Handle state change."""
        self.indicator.set_state(state)
        
        status_texts = {
            "idle": "Ready and listening",
            "listening": "Listening...",
            "speaking": "Speaking..."
        }
        self.status_label.setText(status_texts.get(state, state))
    
    def update_transcript(self, text: str, is_user: bool = False) -> None:
        """Update transcript display (thread-safe)."""
        self.transcript_update.emit(text, is_user)
    
    def _on_transcript_update(self, text: str, is_user: bool) -> None:
        """Handle transcript update."""
        self.transcript.update_transcript(text, is_user)
    
    def update_status(self, component: str, status: str) -> None:
        """Update system status (thread-safe)."""
        self.status_update.emit(component, status)
    
    def _on_status_update(self, component: str, status: str) -> None:
        """Handle status update."""
        self.system_status.update_status(component, status)
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        print("[UI] HUD window closing")
        event.accept()


def run_ui(jarvis_instance=None) -> JarvisHUD:
    """
    Run the HUD UI in a separate thread/process.
    
    Args:
        jarvis_instance: Optional reference to main Jarvis instance
        
    Returns:
        JarvisHUD instance
    """
    app = QApplication(sys.argv)
    
    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))
    
    window = JarvisHUD()
    window.show()
    
    return window


if __name__ == "__main__":
    # Test the UI standalone
    window = run_ui()
    sys.exit(app.exec())
