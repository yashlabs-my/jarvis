"""
Voice Input Module
Real-time speech recognition using faster-whisper with streaming support.
"""

import asyncio
import threading
import queue
from typing import Optional, Callable, AsyncGenerator
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config.settings import Config


class SpeechRecognizer:
    """
    Real-time speech recognizer using faster-whisper.
    Supports streaming audio input and low-latency transcription.
    """
    
    def __init__(self, model_size: str = Config.WHISPER_MODEL):
        self.model_size = model_size
        self.sample_rate = Config.SAMPLE_RATE
        self.channels = Config.AUDIO_CHANNELS
        self.chunk_size = Config.AUDIO_CHUNK_SIZE
        
        # Load whisper model (runs on CPU by default, GPU if available)
        self.model: Optional[WhisperModel] = None
        self._model_loaded = False
        
        # Audio recording state
        self.is_recording = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.recording_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_transcription: Optional[Callable[[str], None]] = None
        
    def load_model(self) -> bool:
        """Load the whisper model."""
        try:
            print(f"[STT] Loading whisper model: {self.model_size}")
            # Compute type: default lets whisper choose best available
            self.model = WhisperModel(self.model_size, compute_type="default")
            self._model_loaded = True
            print("[STT] Model loaded successfully")
            return True
        except Exception as e:
            print(f"[STT ERROR] Failed to load model: {e}")
            return False
    
    def _audio_callback(self, indata: np.ndarray, frames: int, 
                        time_info: dict, status: sd.CallbackFlags) -> None:
        """Callback for audio stream - queues audio chunks."""
        if self.is_recording:
            self.audio_queue.put(indata.copy())
    
    def start_recording(self) -> None:
        """Start recording audio from microphone."""
        if not self._model_loaded:
            print("[STT ERROR] Model not loaded")
            return
        
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        self.recording_thread = threading.Thread(
            target=self._run_audio_stream,
            daemon=True
        )
        self.recording_thread.start()
        print("[STT] Recording started")
    
    def stop_recording(self) -> None:
        """Stop recording audio."""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        print("[STT] Recording stopped")
    
    def _run_audio_stream(self) -> None:
        """Run audio stream in separate thread."""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                blocksize=self.chunk_size
            ) as stream:
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            print(f"[STT ERROR] Audio stream error: {e}")
    
    async def transcribe_stream(self) -> AsyncGenerator[str, None]:
        """
        Continuously transcribe audio stream.
        Yields transcription results as they become available.
        """
        if not self._model_loaded:
            if not self.load_model():
                return
        
        audio_buffer = []
        silence_threshold = 0.01
        silence_duration = 0.5  # seconds
        silence_count = 0
        
        while self.is_recording:
            try:
                # Get audio chunk with timeout
                try:
                    chunk = self.audio_queue.get(timeout=0.1)
                    audio_buffer.append(chunk)
                    
                    # Check for silence
                    rms = np.sqrt(np.mean(chunk ** 2))
                    if rms < silence_threshold:
                        silence_count += 1
                    else:
                        silence_count = 0
                    
                    # Transcribe after silence (end of utterance)
                    if silence_count > int(silence_duration * 10) and len(audio_buffer) > 0:
                        audio_data = np.concatenate(audio_buffer, axis=0)
                        audio_buffer = []
                        silence_count = 0
                        
                        # Transcribe
                        result = await asyncio.to_thread(
                            self._transcribe_audio,
                            audio_data.flatten()
                        )
                        
                        if result and result.strip():
                            yield result
                            
                except queue.Empty:
                    continue
                    
            except Exception as e:
                print(f"[STT ERROR] Transcription error: {e}")
                continue
    
    def _transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data using whisper."""
        if not self.model or len(audio_data) == 0:
            return ""
        
        try:
            segments, info = self.model.transcribe(
                audio_data,
                language="en",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            text = " ".join([segment.text for segment in segments]).strip()
            return text
        except Exception as e:
            print(f"[STT ERROR] Transcription failed: {e}")
            return ""
    
    async def listen_once(self, timeout: float = 10.0) -> str:
        """
        Listen for a single utterance and return transcription.
        
        Args:
            timeout: Maximum time to wait for speech
            
        Returns:
            Transcribed text or empty string
        """
        self.start_recording()
        
        try:
            async with asyncio.timeout(timeout):
                async for text in self.transcribe_stream():
                    if text:
                        self.stop_recording()
                        return text
        except asyncio.TimeoutError:
            self.stop_recording()
            return ""
        
        self.stop_recording()
        return ""
    
    def detect_wake_word(self, text: str) -> bool:
        """
        Check if text contains wake word.
        
        Args:
            text: Transcribed text
            
        Returns:
            True if wake word detected
        """
        return Config.WAKE_WORD.lower() in text.lower()
