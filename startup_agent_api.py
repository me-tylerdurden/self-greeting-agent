#!/usr/bin/env python3
"""
Startup Agent API - Now other programs can talk to your agent!
Run this to create a web API that others can interact with

Installation: pip install fastapi uvicorn requests
Usage: python3 startup_agent_api.py
API will be available at: http://localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import requests
import json
from datetime import datetime
import random
import subprocess
from typing import Dict, Any
import uvicorn

class TalkableStartupAgent:
    def __init__(self):
        self.model = "codellama"
        self.base_url = "http://localhost:11434/api/generate"
        self.conversation_history = []
        
    def check_ollama_running(self):
        """Check if Ollama is running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_ollama_if_needed(self):
        """Start Ollama if not running"""
        if not self.check_ollama_running():
            try:
                subprocess.Popen(["/Applications/Ollama.app/Contents/Resources/ollama", "serve"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time
                time.sleep(3)
            except Exception as e:
                print(f"Could not start Ollama: {e}")
    
    def get_greeting(self, user_name="friend"):
        """Get personalized greeting"""
        current_time = datetime.now()
        hour = current_time.hour
        
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        fallback_greetings = [
            f"{time_greeting} {user_name}! Ready to code something awesome today?",
            f"{time_greeting}! Your AI coding assistant is here and ready to help!",
            f"Hello {user_name}! {time_greeting}. Let's build something amazing together!",
            f"{time_greeting}! Hope you're ready for another productive coding session!",
        ]
        
        try:
            self.start_ollama_if_needed()
            
            if self.check_ollama_running():
                prompt = f"""Generate a brief, friendly greeting for a programmer named {user_name} who just started their laptop. 
                Current time: {time_greeting.lower()}
                Make it encouraging and coding-related. Keep it under 50 words."""
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.8, "max_tokens": 100}
                }
                
                response = requests.post(self.base_url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    return response.json()["response"].strip()
                    
        except Exception as e:
            print(f"Error getting AI greeting: {e}")
            
        return random.choice(fallback_greetings)
    
    def chat(self, message: str, user_name: str = "friend"):
        """Chat with the agent"""
        try:
            self.start_ollama_if_needed()
            
            if not self.check_ollama_running():
                return "Sorry, I'm having trouble connecting to my AI brain right now. Try again in a moment!"
            
            # Add context about being a startup agent
            system_context = f"""You are Saurabh's personal startup agent and coding assistant. 
            You live on his MacBook and help with programming tasks. 
            Be friendly, encouraging, and focus on coding/tech topics.
            User's name: {user_name}
            
            Previous conversation:
            """ + "\n".join(self.conversation_history[-6:])  # Last 6 messages for context
            
            full_prompt = f"{system_context}\n\nUser: {message}\nAssistant:"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.7, "max_tokens": 200}
            }
            
            response = requests.post(self.base_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                ai_response = response.json()["response"].strip()
                
                # Store conversation history
                self.conversation_history.append(f"User: {message}")
                self.conversation_history.append(f"Assistant: {ai_response}")
                
                # Keep only last 10 exchanges
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                return ai_response
            else:
                return "Sorry, I'm having trouble thinking right now. Try again!"
                
        except Exception as e:
            return f"Oops! Something went wrong: {str(e)}"
    
    def get_status(self):
        """Get agent status"""
        ollama_status = "Running" if self.check_ollama_running() else "Not running"
        return {
            "agent_status": "Online",
            "ollama_status": ollama_status,
            "model": self.model,
            "conversation_length": len(self.conversation_history),
            "last_active": datetime.now().isoformat()
        }

# Create FastAPI app
app = FastAPI(
    title="Saurabh's Startup Agent API",
    description="Talk to Saurabh's personal MacBook startup agent!",
    version="1.0.0"
)

# Initialize agent
agent = TalkableStartupAgent()

@app.get("/")
async def home():
    """Welcome page with API documentation"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Saurabh's Startup Agent API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; max-width: 800px; }
            h1 { color: #333; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { background: #007bff; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
            .test-form { margin: 20px 0; padding: 20px; background: #e3f2fd; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Saurabh's Startup Agent API</h1>
            <p>Welcome! This API lets you talk to Saurabh's personal startup agent that runs on his MacBook.</p>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <span class="method">GET</span> <code>/greeting</code>
                <p>Get a personalized startup greeting</p>
                <p>Optional: <code>?name=YourName</code></p>
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <code>/chat</code>
                <p>Chat with the agent</p>
                <p>Body: <code>{"message": "Hello!", "user_name": "YourName"}</code></p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <code>/status</code>
                <p>Check agent status and health</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <code>/docs</code>
                <p>Interactive API documentation (Swagger UI)</p>
            </div>
            
            <div class="test-form">
                <h3>🧪 Test the API:</h3>
                <p><strong>Get Greeting:</strong> <a href="/greeting?name=TestUser" target="_blank">Click here</a></p>
                <p><strong>Check Status:</strong> <a href="/status" target="_blank">Click here</a></p>
                <p><strong>Interactive Docs:</strong> <a href="/docs" target="_blank">Click here</a></p>
            </div>
            
            <h3>Example Usage:</h3>
            <pre><code># Python
import requests

# Get greeting
response = requests.get("http://localhost:8000/greeting?name=Alice")
print(response.json())

# Chat
response = requests.post("http://localhost:8000/chat", 
    json={"message": "Help me debug this Python code", "user_name": "Alice"})
print(response.json())

# JavaScript
fetch('http://localhost:8000/greeting?name=Bob')
    .then(response => response.json())
    .then(data => console.log(data));
</code></pre>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/greeting")
async def get_greeting(name: str = "friend"):
    """Get a personalized greeting from the startup agent"""
    try:
        greeting = agent.get_greeting(name)
        return {
            "greeting": greeting,
            "user_name": name,
            "timestamp": datetime.now().isoformat(),
            "agent": "Saurabh's Startup Agent"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_agent(request: Dict[str, Any]):
    """Chat with the startup agent"""
    try:
        message = request.get("message", "")
        user_name = request.get("user_name", "friend")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        response = agent.chat(message, user_name)
        
        return {
            "response": response,
            "user_message": message,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat(),
            "agent": "Saurabh's Startup Agent"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_agent_status():
    """Get the current status of the agent"""
    try:
        status = agent.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_conversation_history():
    """Get recent conversation history"""
    return {
        "history": agent.conversation_history[-10:],  # Last 10 messages
        "total_messages": len(agent.conversation_history)
    }

if __name__ == "__main__":
    print("🤖 Starting Saurabh's Startup Agent API...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 Docs available at: http://localhost:8000/docs")
    print("🏠 Home page: http://localhost:8000")
    print("\n" + "="*50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
