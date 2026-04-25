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

# Serve index.html at root
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount the rest of the static files
app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
