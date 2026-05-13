"""
Voice Output Module
Text-to-Speech using edge-tts with streaming and interrupt support.
"""

import asyncio
import io
import os
from typing import Optional, AsyncGenerator
import tempfile
import wave

import edge_tts
from pydub import AudioSegment
from pydub.playback import play as pydub_play

from config.settings import Config


class TextToSpeech:
    """
    Text-to-Speech engine using edge-tts.
    Supports streaming generation and interruptible playback.
    """
    
    def __init__(self, voice: str = Config.TTS_VOICE):
        self.voice = voice
        self.rate = Config.TTS_RATE
        self.pitch = Config.TTS_PITCH
        
        # Playback state
        self._is_speaking = False
        self._current_player: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # Temp directory for audio files
        self.temp_dir = tempfile.gettempdir() / "jarvis_tts"  # type: ignore
        os.makedirs(self.temp_dir, exist_ok=True)
    
    @property
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking
    
    async def generate_audio(self, text: str) -> Optional[bytes]:
        """
        Generate audio from text using edge-tts.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio bytes or None on failure
        """
        try:
            communicate = edge_tts.Communicate(
                text,
                self.voice,
                rate=self.rate,
                pitch=self.pitch
            )
            
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            
            if len(audio_data) > 0:
                return bytes(audio_data)
            return None
            
        except Exception as e:
            print(f"[TTS ERROR] Generation failed: {e}")
            return None
    
    async def speak(self, text: str, interrupt: bool = True) -> None:
        """
        Speak text with optional interrupt support.
        
        Args:
            text: Text to speak
            interrupt: If True, stop any current speech before starting
        """
        if interrupt:
            await self.stop()
        
        self._is_speaking = True
        self._stop_event.clear()
        
        try:
            # Generate audio
            audio_data = await self.generate_audio(text)
            
            if not audio_data:
                self._is_speaking = False
                return
            
            # Convert to wav for playback
            wav_path = os.path.join(self.temp_dir, f"tts_{hash(text)}.wav")
            
            # edge-tts returns MP3 format, convert to wav
            mp3_path = wav_path.replace(".wav", ".mp3")
            
            with open(mp3_path, "wb") as f:
                f.write(audio_data)
            
            # Load and play audio
            audio = AudioSegment.from_mp3(mp3_path)
            
            # Play in background task
            self._current_player = asyncio.create_task(
                self._play_audio(audio, wav_path, mp3_path)
            )
            await self._current_player
            
        except Exception as e:
            print(f"[TTS ERROR] Playback failed: {e}")
        finally:
            self._is_speaking = False
    
    async def _play_audio(self, audio: AudioSegment, wav_path: str, 
                          mp3_path: str) -> None:
        """Play audio with interrupt support."""
        try:
            # Use simpleaudio or pyaudio for non-blocking playback
            import simpleaudio as sa
            
            # Export to wav for simpleaudio
            wav_bytes = io.BytesIO()
            audio.export(wav_bytes, format="wav")
            wav_bytes.seek(0)
            
            # Load wav data
            import wave
            with wave.open(wav_bytes, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                sample_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
            
            # Create audio object
            play_obj = sa.play_buffer(frames, n_channels, sample_width, sample_rate)
            
            # Wait for completion or stop event
            while play_obj.is_playing():
                if self._stop_event.is_set():
                    play_obj.stop()
                    break
                await asyncio.sleep(0.1)
            
        except ImportError:
            # Fallback to blocking playback
            print("[TTS] simpleaudio not available, using fallback")
            if not self._stop_event.is_set():
                pydub_play(audio)
        except Exception as e:
            print(f"[TTS ERROR] Playback error: {e}")
        finally:
            # Cleanup temp files
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                mp3_file = wav_path.replace(".wav", ".mp3")
                if os.path.exists(mp3_file):
                    os.remove(mp3_file)
            except:
                pass
    
    async def stop(self) -> None:
        """Stop current speech immediately."""
        if self._is_speaking:
            self._stop_event.set()
            
            if self._current_player and not self._current_player.done():
                self._current_player.cancel()
                try:
                    await self._current_player
                except asyncio.CancelledError:
                    pass
            
            self._is_speaking = False
            print("[TTS] Speech interrupted")
    
    async def speak_streaming(self, text_chunks: AsyncGenerator[str, None]) -> None:
        """
        Speak text as it streams in from LLM.
        
        Args:
            text_chunks: Async generator yielding text chunks
        """
        await self.stop()
        
        full_text = []
        self._is_speaking = True
        self._stop_event.clear()
        
        try:
            # Collect chunks and speak periodically
            buffer = []
            async for chunk in text_chunks:
                if self._stop_event.is_set():
                    break
                    
                buffer.append(chunk)
                
                # Speak when we have enough text (sentence boundary)
                if len(''.join(buffer)) > 50 and ('.' in chunk or ',' in chunk):
                    text_to_speak = ''.join(buffer)
                    full_text.append(text_to_speak)
                    
                    # Generate and speak this segment
                    audio_data = await self.generate_audio(text_to_speak)
                    if audio_data and not self._stop_event.is_set():
                        await self._play_segment(audio_data)
                    
                    buffer = []
            
            # Speak remaining text
            if buffer:
                text_to_speak = ''.join(buffer)
                full_text.append(text_to_speak)
                
                if not self._stop_event.is_set():
                    audio_data = await self.generate_audio(text_to_speak)
                    if audio_data:
                        await self._play_segment(audio_data)
                        
        except Exception as e:
            print(f"[TTS ERROR] Streaming speech failed: {e}")
        finally:
            self._is_speaking = False
    
    async def _play_segment(self, audio_data: bytes) -> None:
        """Play a single audio segment."""
        try:
            import simpleaudio as sa
            
            wav_bytes = io.BytesIO(audio_data)
            # Note: edge-tts returns MP3, need proper conversion
            # For now, use file-based approach
            temp_mp3 = os.path.join(self.temp_dir, f"segment_{id(audio_data)}.mp3")
            with open(temp_mp3, "wb") as f:
                f.write(audio_data)
            
            audio = AudioSegment.from_mp3(temp_mp3)
            wav_bytes = io.BytesIO()
            audio.export(wav_bytes, format="wav")
            wav_bytes.seek(0)
            
            import wave
            with wave.open(wav_bytes, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                sample_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
            
            play_obj = sa.play_buffer(frames, n_channels, sample_width, sample_rate)
            
            while play_obj.is_playing():
                if self._stop_event.is_set():
                    play_obj.stop()
                    break
                await asyncio.sleep(0.1)
            
            os.remove(temp_mp3)
            
        except Exception as e:
            print(f"[TTS ERROR] Segment playback failed: {e}")
