"""
Core Module
Main Jarvis orchestrator that coordinates all components.
"""

import asyncio
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

from config.settings import Config
from llm.openrouter_client import OpenRouterLLM
from voice.speech_recognition import SpeechRecognizer
from voice.text_to_speech import TextToSpeech
from memory.memory_manager import MemoryManager
from automation.system_control import AutomationManager


class CommandClassifier:
    """
    Classifies user input into command types.
    Determines if input should trigger system actions or LLM conversation.
    """
    
    # Command patterns mapped to action types
    COMMAND_PATTERNS = {
        "open_app": [
            r"open\s+(chrome|firefox|edge|vscode|notepad|calculator|terminal|spotify|discord|slack)",
            r"launch\s+(chrome|firefox|edge|vscode|notepad|calculator|terminal|spotify|discord|slack)",
            r"start\s+(chrome|firefox|edge|vscode|notepad|calculator|terminal|spotify|discord|slack)",
        ],
        "close_app": [
            r"close\s+(chrome|firefox|edge|vscode|notepad|spotify|discord|slack)",
            r"quit\s+(chrome|firefox|edge|vscode|notepad|spotify|discord|slack)",
            r"exit\s+(chrome|firefox|edge|vscode|notepad|spotify|discord|slack)",
        ],
        "volume_up": [r"volume\s+up", r"turn\s+up\s+volume", r"increase\s+volume", r"louder"],
        "volume_down": [r"volume\s+down", r"turn\s+down\s+volume", r"decrease\s+volume", r"quieter"],
        "set_volume": [r"set\s+volume\s+to\s+(\d+)", r"volume\s+(\d+)"],
        "shutdown": [r"shutdown", r"shut\s+down", r"power\s+off"],
        "restart": [r"restart", r"reboot"],
        "sleep": [r"sleep", r"go\s+to\s+sleep", r"suspend"],
        "screenshot": [r"take\s+screenshot", r"capture\s+screen", r"screenshot"],
        "open_folder": [
            r"open\s+(documents|downloads|desktop|pictures|music|videos)",
            r"show\s+(documents|downloads|desktop|pictures|music|videos)",
        ],
        "create_folder": [r"create\s+folder\s+(\w+)", r"new\s+folder\s+(\w+)"],
        "search_files": [r"find\s+(.+)", r"search\s+for\s+(.+)"],
        "web_search": [r"search\s+(?:for\s+)?(.+)", r"google\s+(.+)"],
        "open_site": [
            r"open\s+(youtube|google|github|reddit|twitter|netflix|amazon)",
            r"go\s+to\s+(youtube|google|github|reddit|twitter|netflix|amazon)",
            r"visit\s+(youtube|google|github|reddit|twitter|netflix|amazon)",
        ],
        "open_url": [r"open\s+(https?://\S+)", r"browse\s+(https?://\S+)"],
        "type_text": [r"type\s+(.+)", r"write\s+(.+)"],
        "press_key": [r"press\s+(\w+)", r"hit\s+(\w+)"],
        "hotkey": [r"press\s+(\w+)\s*\+\s*(\w+)", r"hotkey\s+(\w+)\s+(\w+)"],
        "mouse_move": [r"move\s+mouse\s+to\s+(\d+)\s*,?\s*(\d+)"],
        "click": [r"(left|right|middle)\s*click", r"click\s+(left|right|middle)"],
        "scroll": [r"scroll\s+(up|down)"],
    }
    
    def __init__(self):
        self._compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for action_type, patterns in self.COMMAND_PATTERNS.items():
            self._compiled_patterns[action_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify input text into command type.
        
        Args:
            text: User input text
            
        Returns:
            Dict with action_type and parameters
        """
        text = text.lower().strip()
        
        for action_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    groups = match.groups()
                    return {
                        "action_type": action_type,
                        "params": list(groups) if groups else [],
                        "matched_pattern": pattern.pattern,
                    }
        
        # No command matched - treat as conversation
        return {
            "action_type": "conversation",
            "params": [text],
            "matched_pattern": None,
        }


class Jarvis:
    """
    Main Jarvis AI Assistant class.
    Orchestrates all components for real-time voice interaction.
    """
    
    def __init__(self):
        self.config = Config
        
        # Initialize components
        self.llm = OpenRouterLLM()
        self.stt = SpeechRecognizer()
        self.tts = TextToSpeech()
        self.memory = MemoryManager()
        self.automation = AutomationManager()
        self.classifier = CommandClassifier()
        
        # State
        self.is_running = False
        self.is_listening = False
        self.is_speaking = False
        self.pending_interruption = False
        
        # Event for interrupt handling
        self._interrupt_event = asyncio.Event()
        
        # Task references
        self._listen_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful
        """
        print("[JARVIS] Initializing...")
        
        # Validate configuration
        if not self.config.validate():
            return False
        
        # Initialize memory
        await self.memory.initialize()
        
        # Load STT model
        if not self.stt.load_model():
            print("[JARVIS] Failed to load speech recognition model")
            return False
        
        # Load preferences
        prefs = await self.memory.get_all_preferences()
        print(f"[JARVIS] Loaded {len(prefs)} preferences")
        
        print("[JARVIS] Initialization complete")
        return True
    
    async def start(self) -> None:
        """Start the main assistant loop."""
        if not await self.initialize():
            print("[JARVIS] Initialization failed. Exiting.")
            return
        
        self.is_running = True
        print("[JARVIS] Ready. Say 'Jarvis' to activate.")
        
        # Start continuous listening
        await self._run_wake_word_listener()
    
    async def stop(self) -> None:
        """Stop the assistant gracefully."""
        print("[JARVIS] Shutting down...")
        self.is_running = False
        self.is_listening = False
        
        # Stop any ongoing speech
        await self.tts.stop()
        
        # Cancel tasks
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
        if self._process_task and not self._process_task.done():
            self._process_task.cancel()
        
        # Close connections
        await self.memory.close()
        
        print("[JARVIS] Goodbye, sir.")
    
    async def _run_wake_word_listener(self) -> None:
        """Run wake word detection in continuous loop."""
        self.stt.start_recording()
        
        try:
            while self.is_running:
                # Listen for speech
                async for transcription in self.stt.transcribe_stream():
                    if not self.is_running:
                        break
                    
                    # Check for wake word
                    if self.stt.detect_wake_word(transcription):
                        print(f"[JARVIS] Wake word detected: '{transcription}'")
                        
                        # Extract command after wake word
                        command = self._extract_command(transcription)
                        
                        # Process the command
                        await self._process_command(command)
                    
                    # Check for interruption during speech
                    elif self.is_speaking:
                        print("[JARVIS] Interruption detected")
                        await self.tts.stop()
                        self.pending_interruption = True
                        
        except asyncio.CancelledError:
            pass
        finally:
            self.stt.stop_recording()
    
    def _extract_command(self, text: str) -> str:
        """
        Extract command text after wake word.
        
        Args:
            text: Full transcription including wake word
            
        Returns:
            Command text without wake word
        """
        # Remove wake word and clean up
        pattern = re.compile(rf"\b{Config.WAKE_WORD}\b\s*", re.IGNORECASE)
        command = pattern.sub("", text).strip()
        return command
    
    async def _process_command(self, command: str) -> None:
        """
        Process a user command.
        
        Args:
            command: Command text (wake word removed)
        """
        if not command:
            # Just wake word with no command
            response = "Yes, sir?"
            await self._speak_response(response)
            return
        
        print(f"[JARVIS] Processing command: '{command}'")
        
        # Classify the command
        classification = self.classifier.classify(command)
        action_type = classification["action_type"]
        params = classification["params"]
        
        print(f"[JARVIS] Classified as: {action_type}")
        
        # Execute based on type
        if action_type != "conversation":
            # Execute system command
            success, result = await self._execute_system_command(
                action_type, params
            )
            
            # Log command execution
            await self.memory.log_command(command, str(result), success)
            
            # Generate appropriate response
            response = self._generate_command_response(
                action_type, success, result
            )
        else:
            # Send to LLM for conversation
            response = await self._get_llm_response(command)
        
        # Save to memory
        await self.memory.save_message("user", command)
        await self.memory.save_message("assistant", response)
        
        # Speak response
        await self._speak_response(response)
    
    async def _execute_system_command(
        self, action_type: str, params: List[str]
    ) -> tuple[bool, Any]:
        """
        Execute a system command.
        
        Args:
            action_type: Type of action to execute
            params: Action parameters
            
        Returns:
            (success, result) tuple
        """
        try:
            if action_type == "open_app":
                return self.automation.execute_command("open", params[0])
            
            elif action_type == "close_app":
                return self.automation.execute_command("close", params[0])
            
            elif action_type == "volume_up":
                return self.automation.execute_command("volume", "up")
            
            elif action_type == "volume_down":
                return self.automation.execute_command("volume", "down")
            
            elif action_type == "set_volume":
                level = int(params[0]) if params[0].isdigit() else 50
                return self.automation.execute_command("set_volume", level)
            
            elif action_type == "shutdown":
                return self.automation.execute_command("shutdown")
            
            elif action_type == "restart":
                return self.automation.execute_command("restart")
            
            elif action_type == "sleep":
                return self.automation.execute_command("sleep")
            
            elif action_type == "screenshot":
                return self.automation.execute_command("screenshot")
            
            elif action_type == "open_folder":
                return self.automation.execute_command("open_folder", params[0])
            
            elif action_type == "create_folder":
                return self.automation.execute_command("create_folder", params[0])
            
            elif action_type == "search_files":
                return self.automation.execute_command("search_files", params[0])
            
            elif action_type == "web_search":
                return self.automation.execute_command("search", params[0])
            
            elif action_type == "open_site":
                return self.automation.execute_command("open_site", params[0])
            
            elif action_type == "open_url":
                return self.automation.execute_command("open_url", params[0])
            
            elif action_type == "type_text":
                return self.automation.execute_command("type", params[0])
            
            elif action_type == "press_key":
                return self.automation.execute_command("press_key", params[0])
            
            elif action_type == "scroll":
                direction = params[0].lower()
                amount = 100 if direction == "up" else -100
                return self.automation.execute_command("scroll", amount)
            
            else:
                return False, f"Unknown action: {action_type}"
                
        except Exception as e:
            return False, str(e)
    
    def _generate_command_response(
        self, action_type: str, success: bool, result: Any
    ) -> str:
        """
        Generate natural language response for command execution.
        
        Args:
            action_type: Type of action executed
            success: Whether execution succeeded
            result: Execution result
            
        Returns:
            Response text
        """
        if not success:
            return f"Command failed: {result}"
        
        responses = {
            "open_app": f"Opening {result.split()[0] if isinstance(result, str) else 'application'} now, sir.",
            "close_app": f"{result}",
            "volume_up": "Volume increased.",
            "volume_down": "Volume decreased.",
            "set_volume": result,
            "shutdown": "Preparing shutdown sequence. Confirm?",
            "restart": "Preparing restart. Confirm?",
            "sleep": "Entering sleep mode.",
            "screenshot": result,
            "open_folder": result,
            "create_folder": result,
            "search_files": f"Found {len(result) if isinstance(result, list) else 0} files.",
            "web_search": f"Searching the web for you.",
            "open_site": "Opening website.",
            "open_url": "Opening URL.",
            "type_text": "Text entered.",
            "press_key": "Key pressed.",
            "scroll": result,
        }
        
        return responses.get(action_type, str(result))
    
    async def _get_llm_response(self, message: str) -> str:
        """
        Get response from LLM for conversational input.
        
        Args:
            message: User message
            
        Returns:
            LLM response text
        """
        # Add context about current time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context_message = f"[Current time: {timestamp}]\n\nUser: {message}"
        
        full_response = ""
        try:
            async for chunk in self.llm.chat(context_message, stream=True):
                full_response += chunk
                
                # Check for interruption
                if self.pending_interruption:
                    self.pending_interruption = False
                    break
        except Exception as e:
            print(f"[JARVIS] LLM error: {e}")
            full_response = "I encountered an error processing your request."
        
        return full_response.strip()
    
    async def _speak_response(self, response: str) -> None:
        """
        Speak a response with interrupt support.
        
        Args:
            response: Text to speak
        """
        if not response:
            return
        
        self.is_speaking = True
        
        try:
            await self.tts.speak(response, interrupt=True)
        finally:
            self.is_speaking = False
            self.pending_interruption = False
    
    async def handle_interruption(self) -> None:
        """Handle user interruption during speech."""
        if self.is_speaking:
            await self.tts.stop()
            self.pending_interruption = True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of Jarvis."""
        return {
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "is_speaking": self.is_speaking,
            "pending_interruption": self.pending_interruption,
            "llm_model": self.llm.model,
            "tts_voice": self.tts.voice,
        }
