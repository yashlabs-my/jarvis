"""
Jarvis AI Assistant - Main Entry Point
Real-time voice assistant inspired by Iron Man's JARVIS.
"""

import asyncio
import signal
import sys
from typing import Optional

# Add project root to path
sys.path.insert(0, str(__file__).parent)

from config.settings import Config
from core.jarvis import Jarvis
from utils.helpers import setup_logger


class JarvisApplication:
    """
    Main application class that manages the Jarvis lifecycle.
    Handles startup, shutdown, and signal handling.
    """
    
    def __init__(self, use_ui: bool = False):
        self.use_ui = use_ui
        self.jarvis: Optional[Jarvis] = None
        self.logger = setup_logger("jarvis_main")
        self._shutdown_event = asyncio.Event()
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup OS signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            # Unix-like systems
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        else:
            # Windows - handle Ctrl+C differently
            pass
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        print(f"\n[JARVIS] Received signal {signum}, shutting down...")
        self._shutdown_event.set()
    
    async def run(self) -> None:
        """Run the main application loop."""
        try:
            print("=" * 60)
            print("  J.A.R.V.I.S. - Just A Rather Very Intelligent System")
            print("  Advanced AI Voice Assistant")
            print("=" * 60)
            print()
            
            # Initialize Jarvis
            self.jarvis = Jarvis()
            
            if not await self.jarvis.initialize():
                print("[ERROR] Failed to initialize Jarvis")
                return
            
            print()
            print("[JARVIS] Starting voice interface...")
            print("[JARVIS] Press Ctrl+C to stop")
            print()
            
            # Start the main listening loop
            # This runs until interrupted
            await self.jarvis.start()
            
        except KeyboardInterrupt:
            print("\n[JARVIS] Interrupted by user")
        except Exception as e:
            self.logger.exception(f"Application error: {e}")
            print(f"[ERROR] {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        print("\n[JARVIS] Shutting down...")
        
        if self.jarvis:
            await self.jarvis.stop()
        
        print("[JARVIS] Shutdown complete")


async def main_async() -> None:
    """Async main entry point."""
    app = JarvisApplication(use_ui=False)
    await app.run()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nGoodbye, sir.")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
