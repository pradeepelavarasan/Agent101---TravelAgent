import os
import sys

# Ensure the root project directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import re

# Import the agent logic
from backend.agent import run_travel_agent_stream

app = FastAPI(title="AI Travel Agent API")

# Add CORS middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    query: str = ""

# Mount static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.post("/init_session")
async def init_session_endpoint(request: ChatRequest):
    from backend.agent import init_session_log
    init_session_log(request.session_id)
    return {"status": "created"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        
    return StreamingResponse(
        run_travel_agent_stream(session_id, request.query), 
        media_type="application/x-ndjson"
    )

@app.get("/sessions")
async def get_sessions():
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    if not os.path.exists(log_dir):
        return {"sessions": []}
        
    files = [f for f in os.listdir(log_dir) if f.startswith("session_") and f.endswith(".log")]
    files.sort(reverse=True) # Newest first
    
    sessions = []
    for f in files:
        session_id = f.replace("session_", "").replace(".log", "")
        # Parse timestamp: YYYYMMDD_HHMMSS
        try:
            dt = f"{session_id[:4]}-{session_id[4:6]}-{session_id[6:8]} {session_id[9:11]}:{session_id[11:13]}:{session_id[13:15]}"
        except:
            dt = session_id
        sessions.append({"id": session_id, "timestamp": dt})
        
    return {"sessions": sessions}

@app.get("/sessions/{session_id}")
async def get_session_details(session_id: str):
    log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', f"session_{session_id}.log"))
    if not os.path.exists(log_file):
        return {"error": "Session not found"}
        
    with open(log_file, "r") as f:
        content = f.read()
        
    # Simple state machine parser for the log format
    turns = []
    current_turn = None
    
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("User Query:"):
            if current_turn:
                turns.append(current_turn)
            current_turn = {
                "query": line.replace("User Query:", "").strip(),
                "iterations": [],
                "response": None
            }
        elif line == "[ Thought ]" and current_turn:
            # Capture thought until next blank line or bracket
            thought = []
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("[") and not lines[i].strip().startswith("=="):
                thought.append(lines[i].strip())
                i += 1
            current_turn["iterations"].append({"type": "thought", "content": " ".join(thought)})
            continue # Already incremented i
        elif line == "[ Action ]" and current_turn:
            action = []
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("[") and not lines[i].strip().startswith("=="):
                action.append(lines[i].strip())
                i += 1
            current_turn["iterations"].append({"type": "action", "content": " ".join(action)})
            continue
        elif line == "AGENT RESPONSE" and current_turn:
            # Next line is usually ==, then the actual response
            response_text = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("=="):
                i += 1
            while i < len(lines) and not lines[i].strip().startswith("==") and not lines[i].strip().startswith("TRAVEL AGENT PROCESSING"):
                if lines[i].strip():
                    response_text.append(lines[i].strip())
                i += 1
            current_turn["response"] = "\n".join(response_text)
            continue
            
        i += 1
        
    if current_turn:
        turns.append(current_turn)
        
    return {"session_id": session_id, "turns": turns}

# Serve index.html at root
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount the rest of the static files
app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
