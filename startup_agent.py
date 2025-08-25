#!/Users/saurabhsingh/.venvs/startup_agent/bin/python
"""
Startup CodeLlama Agent - Greets you when laptop starts.
Designed to run at login via launchd. Uses your venv Python as set in the shebang.
"""

# --- Debug: log which Python is running (add BEFORE other imports) ---
import sys
import datetime
import pathlib

LOG_DIR = pathlib.Path("/Users/saurabhsingh/Library/Logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "startup_agent.log"
ERR_FILE = LOG_DIR / "startup_agent_error.log"
with open(LOG_FILE, "a") as f:
    f.write(f"[{datetime.datetime.now()}] Using Python: {sys.executable}\n")

# --- Imports ---
import requests
import json
import tkinter as tk
from tkinter import messagebox
import subprocess
from datetime import datetime as dt
import time
import random


class StartupAgent:
    def __init__(self):
        self.model = "codellama"
        self.base_url = "http://localhost:11434/api/generate"
        self.ollama_bin = "/Applications/Ollama.app/Contents/Resources/ollama"

    # ---------- logging helpers ----------
    def log(self, msg: str):
        try:
            with open(LOG_FILE, "a") as f:
                f.write(f"[{datetime.datetime.now()}] {msg}\n")
        except Exception:
            pass

    def log_err(self, msg: str):
        try:
            with open(ERR_FILE, "a") as f:
                f.write(f"[{datetime.datetime.now()}] {msg}\n")
        except Exception:
            pass

    # ---------- ollama helpers ----------
    def check_ollama_running(self) -> bool:
        """Return True if Ollama API responds."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            ok = r.status_code == 200
            if ok:
                self.log("Ollama is running.")
            return ok
        except Exception as e:
            self.log(f"Ollama not running yet: {e}")
            return False

    def start_ollama_if_needed(self):
        """
        Start Ollama if not running and wait until API is ready (max ~30s).
        """
        if not self.check_ollama_running():
            try:
                subprocess.Popen(
                    [self.ollama_bin, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.log("Started Ollama serve.")
            except Exception as e:
                self.log_err(f"Could not start Ollama: {e}")
                return

        # Wait up to 30s for API readiness
        deadline = time.time() + 30
        while time.time() < deadline:
            if self.check_ollama_running():
                return
            time.sleep(1)
        self.log_err("Ollama did not become ready within timeout.")

    # ---------- greeting generation ----------
    def _fallback_prompts(self, time_greeting: str):
        return [
            f"{time_greeting} Saurabh! Ready to ship some code today?",
            f"{time_greeting}! Your coding buddy is online. Any bugs to squash?",
            f"Hello Saurabh — {time_greeting}. Let’s build something amazing!",
            f"{time_greeting}! Time to stack commits and sip chai ☕.",
            f"Hey! {time_greeting} Saurabh. What shall we code first?",
        ]

    def get_greeting(self) -> str:
        """Get a short, friendly greeting. Uses Ollama if available, else fallback."""
        now = dt.now()
        hour = now.hour
        if hour < 12:
            tg = "Good morning"
        elif hour < 17:
            tg = "Good afternoon"
        else:
            tg = "Good evening"

        prompts = self._fallback_prompts(tg)

        try:
            self.start_ollama_if_needed()
            if self.check_ollama_running():
                prompt = (
                    "Write one short greeting (<=20 words) for a programmer named "
                    "Saurabh who just started their laptop. It must mention coding and "
                    f"the time of day: {tg.lower()}. Keep it crisp."
                )
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.6,   # balanced creativity
                        "max_tokens": 40      # ~<=20 words
                    },
                }
                self.log("Requesting greeting from Ollama...")
                r = requests.post(self.base_url, json=payload, timeout=20)
                if r.status_code == 200:
                    text = r.json().get("response", "").strip()
                    # safety trims
                    text = text.replace("\n", " ").strip()
                    if len(text.split()) > 20:
                        text = " ".join(text.split()[:20])
                    self.log("Got greeting from Ollama.")
                    return text or random.choice(prompts)
                else:
                    self.log_err(f"Ollama HTTP {r.status_code}; using fallback.")
                    return random.choice(prompts)
            else:
                self.log("Ollama unavailable; using fallback.")
                return random.choice(prompts)
        except Exception as e:
            self.log_err(f"Error getting AI greeting: {e}")
            return random.choice(prompts)

    # ---------- UIs ----------
    def show_popup_greeting(self):
        """Show greeting in a Tkinter popup (better for manual runs)."""
        try:
            greeting = self.get_greeting()
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("🤖 Your Coding Assistant", greeting)
            root.destroy()
        except Exception as e:
            self.log_err(f"Popup failed: {e}")
            self.show_terminal_greeting()

    def show_terminal_greeting(self):
        """Show greeting in the terminal."""
        greeting = self.get_greeting()
        bar = "=" * 60
        print(bar)
        print("🤖 CODELLAMA STARTUP AGENT")
        print(bar)
        print(f"\n{greeting}\n")
        print("💡 Quick Commands:")
        print("   • ollama run codellama    - Start coding chat")
        print("   • ollama run tinyllama    - Quick assistant")
        print("   • code .                  - Open VS Code")
        print(bar)

    def show_notification(self):
        """Prefer this for launchd at login (more reliable than Tkinter)."""
        greeting = self.get_greeting()

        # Sanitize for AppleScript: escape backslashes and quotes, and flatten newlines
        safe = (
            greeting.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", " ")
        )

        self.log(f"Greeting text: {greeting}")
        try:
            script = f'display notification "{safe}" with title "🤖 CodeLlama Agent" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], check=False)
            self.log("Displayed macOS notification.")
        except Exception as e:
            self.log_err(f"Notification failed: {e}")
            # Fallback to terminal if notification fails
            self.show_terminal_greeting()


def main():
    agent = StartupAgent()
    # For launchd login runs, notifications are the most reliable:
    agent.show_notification()
    # For manual testing, you can swap to:
    # agent.show_popup_greeting()
    # agent.show_terminal_greeting()


if __name__ == "__main__":
    main()

