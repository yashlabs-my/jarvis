"""
Test script for Jarvis components.
Run this to verify all modules import correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test config
    try:
        from config.settings import Config
        print("✓ config.settings - OK")
        tests_passed += 1
    except Exception as e:
        print(f"✗ config.settings - FAILED: {e}")
        tests_failed += 1
    
    # Test LLM
    try:
        from llm.openrouter_client import OpenRouterLLM, Message
        print("✓ llm.openrouter_client - OK")
        tests_passed += 1
    except Exception as e:
        print(f"✗ llm.openrouter_client - FAILED: {e}")
        tests_failed += 1
    
    # Test Voice
    try:
        from voice.speech_recognition import SpeechRecognizer
        from voice.text_to_speech import TextToSpeech
        print("✓ voice modules - OK")
        tests_passed += 1
    except Exception as e:
        print(f"✗ voice modules - FAILED: {e}")
        tests_failed += 1
    
    # Test Memory
    try:
        from memory.memory_manager import MemoryManager
        print("✓ memory.memory_manager - OK")
        tests_passed += 1
    except Exception as e:
        print(f"✗ memory.memory_manager - FAILED: {e}")
        tests_failed += 1
    
    # Test Automation
    try:
        from automation.system_control import (
            AutomationManager,
            SystemController,
            FileController,
            WebController,
            InputController
        )
        print("✓ automation modules - OK")
        tests_passed += 1
    except Exception as e:
        print(f"✗ automation modules - FAILED: {e}")
        tests_failed += 1
    
    # Test Core
    try:
        from core.jarvis import Jarvis, CommandClassifier
        print("✓ core.jarvis - OK")
        tests_passed += 1
    except Exception as e:
        print(f"✗ core.jarvis - FAILED: {e}")
        tests_failed += 1
    
    # Test Utils
    try:
        from utils.helpers import setup_logger, sanitize_input
        print("✓ utils.helpers - OK")
        tests_passed += 1
    except Exception as e:
        print(f"✗ utils.helpers - FAILED: {e}")
        tests_failed += 1
    
    # Test UI (optional - may fail if PyQt6 not installed)
    try:
        from ui.hud_interface import JarvisHUD
        print("✓ ui.hud_interface - OK")
        tests_passed += 1
    except ImportError as e:
        print(f"⚠ ui.hud_interface - PyQt6 not installed (optional)")
    except Exception as e:
        print(f"✗ ui.hud_interface - FAILED: {e}")
        tests_failed += 1
    
    print("=" * 50)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    
    return tests_failed == 0


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    print("=" * 50)
    
    from config.settings import Config
    
    # Check required config
    if Config.OPENROUTER_API_KEY:
        key_preview = Config.OPENROUTER_API_KEY[:10] + "..." if len(Config.OPENROUTER_API_KEY) > 10 else Config.OPENROUTER_API_KEY
        print(f"✓ API Key set: {key_preview}")
    else:
        print("⚠ API Key not set (will need to configure .env)")
    
    print(f"✓ Model: {Config.OPENROUTER_MODEL}")
    print(f"✓ Wake word: {Config.WAKE_WORD}")
    print(f"✓ TTS Voice: {Config.TTS_VOICE}")
    print(f"✓ Debug mode: {Config.DEBUG}")
    
    return True


def test_command_classifier():
    """Test command classification."""
    print("\nTesting command classifier...")
    print("=" * 50)
    
    from core.jarvis import CommandClassifier
    
    classifier = CommandClassifier()
    
    test_cases = [
        ("Jarvis open Chrome", "open_app"),
        ("Jarvis volume up", "volume_up"),
        ("Jarvis search for cats", "web_search"),
        ("Jarvis open YouTube", "open_site"),
        ("Jarvis what is the weather", "conversation"),
        ("Jarvis take a screenshot", "screenshot"),
    ]
    
    for text, expected_type in test_cases:
        result = classifier.classify(text)
        status = "✓" if result["action_type"] == expected_type else "✗"
        print(f"{status} '{text}' -> {result['action_type']} (expected: {expected_type})")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("  J.A.R.V.I.S. Component Tests")
    print("=" * 50 + "\n")
    
    all_passed = True
    
    # Run tests
    if not test_imports():
        all_passed = False
    
    test_config()
    test_command_classifier()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("All critical tests passed! ✓")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your OpenRouter API key")
        print("3. Run: python main.py")
    else:
        print("Some tests failed. Please check errors above.")
    print("=" * 50 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
