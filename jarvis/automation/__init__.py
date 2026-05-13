"""Automation package initialization."""

from .system_control import (
    AutomationManager,
    SystemController,
    FileController,
    WebController,
    InputController
)

__all__ = [
    "AutomationManager",
    "SystemController",
    "FileController", 
    "WebController",
    "InputController"
]
