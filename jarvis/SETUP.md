# Setup Instructions for J.A.R.V.I.S.

## Quick Start Guide

### 1. Prerequisites Check

Ensure you have:
- Python 3.12 or higher (`python --version`)
- pip package manager
- Microphone connected and working
- OpenRouter API key (get from https://openrouter.ai/)

### 2. Installation Steps

#### Step 1: Navigate to jarvis directory
```bash
cd /workspace/jarvis
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** Some packages may require additional system dependencies:

**Windows:**
- Microsoft Visual C++ Build Tools (for some packages)
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev ffmpeg libespeak-dev
```

**Mac:**
```bash
brew install portaudio espeak ffmpeg
```

#### Step 4: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API key
# Use any text editor: nano, vim, notepad, etc.
```

Add your OpenRouter API key to `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```

#### Step 5: Run Jarvis
```bash
python main.py
```

### 3. First Run Checklist

- [ ] Microphone permissions granted
- [ ] API key is valid and has credits
- [ ] No firewall blocking connections
- [ ] Audio output device working

### 4. Testing Commands

Once running, try these commands:

1. **Wake word test**: Say "Jarvis"
2. **Simple command**: "Jarvis what time is it"
3. **App control**: "Jarvis open Chrome"
4. **System control**: "Jarvis volume up"

### 5. Troubleshooting Common Issues

#### Issue: "No module named 'X'"
**Solution:** Ensure virtual environment is activated and run:
```bash
pip install -r requirements.txt --force-reinstall
```

#### Issue: "No microphone detected"
**Solution:** 
```bash
# List audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Set default input device (replace X with device number)
export SOUNDDEVICE_DEFAULT_INPUT_DEVICE=X  # Linux/Mac
set SOUNDDEVICE_DEFAULT_INPUT_DEVICE=X     # Windows
```

#### Issue: "API Error 401"
**Solution:** Check your OPENROUTER_API_KEY in .env file

#### Issue: TTS not producing sound
**Solution:**
- Check system volume
- Verify audio output device
- Try: `pip install simpleaudio` for better playback

#### Issue: High CPU usage
**Solution:** Edit `.env` and change:
```
WHISPER_MODEL=tiny.en
```

### 6. Optional: Enable UI

To use the futuristic HUD interface:

```bash
# Ensure PyQt6 is installed
pip install PyQt6

# Run with UI flag (modify main.py to enable)
python main.py --ui
```

### 7. Performance Optimization

For best performance on different hardware:

**Low-end systems:**
```env
WHISPER_MODEL=tiny.en
DEBUG=false
```

**High-end systems with GPU:**
```env
WHISPER_MODEL=large-v3
# Ensure CUDA is available for GPU acceleration
```

### 8. Uninstallation

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment folder
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# Remove downloaded models (~/.cache/huggingface)
rm -rf ~/.cache/huggingface
```

---

## Getting Help

If you encounter issues:
1. Check logs in `logs/` directory
2. Run with `DEBUG=true` in `.env` for verbose output
3. Verify all dependencies are installed correctly

Enjoy your AI assistant!
