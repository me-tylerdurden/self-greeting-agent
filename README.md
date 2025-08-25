# 🤖 Self Greeting Agent

A macOS startup agent that greets you with a coding-related message every time you log in.  
Powered by [Ollama](https://ollama.ai/) (CodeLlama model by default) + Python.

## Features
- Runs automatically at login
- Uses Ollama to generate greetings
- Falls back to preset greetings
- Shows macOS notifications
- Logs all greetings to `~/Library/Logs/startup_agent.log`

## Installation
1. Clone this repo:
   ```bash
   git clone https://github.com/YOURUSERNAME/self-greeting-agent.git
   cd self-greeting-agent

