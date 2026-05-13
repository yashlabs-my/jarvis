# J.A.R.V.I.S. - AI Voice Assistant

![Jarvis](https://img.shields.io/badge/JARVIS-AI%20Assistant-red)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

**Just A Rather Very Intelligent System** - A cinematic, real-time AI voice assistant inspired by Iron Man's JARVIS.

## Features

### 🎤 Voice Interaction
- **Wake Word Detection**: Continuously listens for "Jarvis" activation
- **Real-time Speech Recognition**: Powered by faster-whisper for low-latency transcription
- **Natural Voice Output**: Edge TTS with futuristic male voice
- **Interrupt Handling**: Instantly stops speaking when you interrupt

### 🖥️ PC Control
- **Application Management**: Open/close apps (Chrome, VSCode, Spotify, etc.)
- **System Control**: Volume, shutdown, restart, sleep
- **File Operations**: Search files, open folders, create directories
- **Web Actions**: Google search, open websites, YouTube
- **Input Automation**: Keyboard typing, hotkeys, mouse control, screenshots

### 🧠 Intelligence
- **OpenRouter LLM Integration**: GPT-4o-mini or any OpenRouter model
- **Conversation Memory**: SQLite-based persistent memory
- **Command Classification**: Smart routing between actions and conversation
- **Context Awareness**: Time-aware responses

### 🎨 Futuristic UI (Optional)
- **Animated Arc Reactor**: Visual listening/speaking indicator
- **Transcript Display**: Real-time conversation log
- **System Status**: CPU, memory, network monitoring
- **Iron Man Theme**: Dark red/black aesthetic

## Installation

### Prerequisites
- Python 3.12+
- Microphone access
- OpenRouter API key

### Setup Steps

1. **Clone or navigate to the jarvis directory:**
```bash
cd jarvis
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenRouter API key
nano .env  # or use your preferred editor
```

5. **Run Jarvis:**
```bash
python main.py
```

## Usage

### Voice Commands

Once running, say **"Jarvis"** followed by your command:

#### Applications
- "Jarvis open Chrome"
- "Jarvis launch VSCode"
- "Jarvis close Spotify"
- "Jarvis open Discord"

#### System Control
- "Jarvis volume up"
- "Jarvis volume down"
- "Jarvis set volume to 50"
- "Jarvis take screenshot"
- "Jarvis go to sleep"

#### Files
- "Jarvis open downloads"
- "Jarvis create folder projects"
- "Jarvis find report"

#### Web
- "Jarvis search for Python tutorials"
- "Jarvis open YouTube"
- "Jarvis go to GitHub"

#### Input
- "Jarvis type Hello World"
- "Jarvis press enter"
- "Jarvis scroll up"

#### Conversation
- "Jarvis what time is it?"
- "Jarvis tell me a joke"
- "Jarvis what can you do?"

### Configuration

Edit `.env` to customize:

```env
# API Configuration
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Voice Settings
TTS_VOICE=en-US-AndrewMultilingualNeural
TTS_RATE=+20%
TTS_PITCH=+10Hz

# Wake Word Sensitivity (0.0-1.0)
WAKE_WORD_SENSITIVITY=0.7

# Debug Mode
DEBUG=false
```

## Project Structure

```
jarvis/
├── core/           # Main orchestrator and command classification
│   └── jarvis.py
├── voice/          # Speech recognition and TTS
│   ├── speech_recognition.py
│   └── text_to_speech.py
├── llm/            # OpenRouter LLM integration
│   └── openrouter_client.py
├── memory/         # SQLite-based memory storage
│   └── memory_manager.py
├── automation/     # PC control modules
│   └── system_control.py
├── ui/             # PyQt6 HUD interface
│   └── hud_interface.py
├── utils/          # Helper utilities
│   └── helpers.py
├── config/         # Configuration management
│   └── settings.py
├── main.py         # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Advanced Features

### Memory System
- Conversations are stored in SQLite database
- Preferences persist across sessions
- Command history logging
- Searchable conversation history

### Command Classification
- Regex-based pattern matching for instant command recognition
- Falls back to LLM for complex queries
- Extensible pattern system

### Interrupt System
- Detects user speech during TTS playback
- Immediately stops speaking
- Processes new input without delay

## Troubleshooting

### Microphone Issues
```bash
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Set default device if needed
export SOUNDDEVICE_DEFAULT_INPUT_DEVICE=<device_id>
```

### TTS Not Working
- Ensure internet connection (edge-tts requires online)
- Check audio output device
- Try different voice in config

### LLM Errors
- Verify OPENROUTER_API_KEY is correct
- Check API quota/limits
- Review error logs in `logs/` directory

### High CPU Usage
- Use smaller whisper model: change `WHISPER_MODEL` to `tiny.en`
- Reduce audio chunk size in config

## Performance Tips

1. **Faster Wake Detection**: Use `tiny.en` whisper model
2. **Better Accuracy**: Use `large-v3` whisper model (requires more resources)
3. **Lower Latency**: Run on GPU with CUDA support
4. **Quiet Environment**: Improves speech recognition accuracy

## Security Notes

- API keys stored only in environment variables
- Shutdown/restart commands require confirmation
- Dangerous shell commands are sanitized
- No data sent except to OpenRouter API

## Future Enhancements

- [ ] Local wake word detection (Porcupine/OwlNet)
- [ ] Multi-language support
- [ ] Plugin architecture for extensibility
- [ ] Home automation integration
- [ ] Calendar and email integration
- [ ] Custom voice training
- [ ] Offline LLM mode (Ollama/Llama.cpp)
- [ ] Mobile companion app
- [ ] Multi-user profiles

## Credits

Inspired by Iron Man's JARVIS from Marvel Studios.

Built with:
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- [edge-tts](https://github.com/rany2/edge-tts)
- [OpenRouter](https://openrouter.ai/)
- [PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [pyautogui](https://pyautogui.readthedocs.io/)

## License

MIT License - See LICENSE file for details.

---

*"Sometimes you gotta run before you can walk."* - Tony Stark
