import os
import json
import requests
import time
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# Load .env (checking current dir and parent dir)
load_dotenv()
load_dotenv("../.env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if not GEMINI_API_KEY:
    print("[!] Warning: GEMINI_API_KEY not found in environment.")

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    client = None
    print(f"[!] Error initializing Gemini Client: {e}")

# ============================================================
# 1. The 4 Live Tools
# ============================================================

def get_weather(city: str) -> str:
    """Live weather via wttr.in"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        res = requests.get(url, timeout=10)
        data = res.json()
        current = data['current_condition'][0]
        return json.dumps({
            "temp": f"{current['temp_C']}°C",
            "desc": current['weatherDesc'][0]['value'],
            "humidity": f"{current['humidity']}%"
        })
    except: return "Weather data currently unavailable."

def convert_currency(amount: float, to_currency: str = "USD", from_currency: str = "INR") -> str:
    """Exchange rates via Frankfurter API"""
    try:
        url = f"https://api.frankfurter.dev/v1/latest?from={from_currency}&to={to_currency}"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if to_currency not in data['rates']:
            return json.dumps({"error": f"Currency code '{to_currency}' not supported."})
            
        rate = data['rates'][to_currency]
        converted = amount * rate
        return json.dumps({
            "original": f"{from_currency} {amount}",
            "converted": f"{to_currency} {converted:.2f}",
            "rate": rate
        })
    except Exception as e:
        return f"Currency conversion unavailable: {str(e)}"

def get_holidays(country_code: str = "IN", year: int = 2026) -> str:
    """Public holiday lookup via Nager.Date"""
    try:
        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
        res = requests.get(url, timeout=10)
        holidays = res.json()
        return json.dumps(holidays[:5]) 
    except: return "Holiday data unavailable."

def get_local_time(timezone: str = "Asia/Kolkata") -> str:
    """Real-time timezone checking via TimeAPI"""
    try:
        url = f"https://www.timeapi.io/api/Time/current/zone?timeZone={timezone}"
        res = requests.get(url, timeout=10)
        return json.dumps(res.json())
    except: return "Local time unavailable."

TOOL_REGISTRY = {
    "get_weather": get_weather,
    "convert_currency": convert_currency,
    "get_holidays": get_holidays,
    "get_local_time": get_local_time
}

# ============================================================
# 2. System Prompt & Memory
# ============================================================

system_prompt = """You are a professional AI Travel Agent. You help users plan every aspect of their trip.
You have access to 4 LIVE tools for data that you cannot know from your training.

TOOLS AVAILABLE:
1. get_weather(city: str)
2. convert_currency(amount: float, to_currency: str, from_currency: str='INR')
3. get_holidays(country_code: str, year: int=2026)
4. get_local_time(timezone: str) -> Use zone like 'Asia/Kolkata' or 'Europe/London'

RESPONSE FORMAT (JSON ONLY):
- If you need a tool: {"thought": "I need to check the current exchange rate...", "tool_name": "...", "tool_arguments": {...}}
- If you have the answer: {"thought": "I have all the live data.", "answer": "..."}

Rules:
- ALWAYS use tools for weather, currency, holidays, and local time.
- You already know general facts about countries and landmarks, so use your internal knowledge for those.
- Every response MUST include a "thought" field.
- ONLY respond with valid JSON.
"""

SESSION_MEMORY = {}

# ============================================================
# 3. Agent Execution Logic (Generator for Streaming)
# ============================================================

def write_log(session_id: str, content: str):
    """Write detailed logs per session."""
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"session_{session_id}.log")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{content}\n")

def log_header(session_id: str, text: str):
    write_log(session_id, f"\n{'='*60}\n  {text.upper()}\n{'='*60}")

def log_step(session_id: str, step: str, content: str):
    write_log(session_id, f"\n[ {step} ]\n  {content}")

def init_session_log(session_id: str):
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = [{"role": "system", "content": system_prompt}]
        log_header(session_id, "NEW SESSION STARTED")
        write_log(session_id, f"  [ MODEL ]: {GEMINI_MODEL}")
        write_log(session_id, "  [ CAPABILITIES & LIVE TOOLS ]:")
        write_log(session_id, "    * get_weather (Real-time Weather) - Powered by wttr.in")
        write_log(session_id, "    * convert_currency (Currency Conversion) - Powered by Frankfurter API")
        write_log(session_id, "    * get_holidays (Public Holiday Lookup) - Powered by Nager.Date")
        write_log(session_id, "    * get_local_time (Timezone Checking) - Powered by TimeAPI.io")

async def run_travel_agent_stream(session_id: str, user_query: str, max_iters=5):
    """
    Generator that yields JSON strings for SSE.
    """
    init_session_log(session_id)
    
    history_messages = SESSION_MEMORY[session_id]
    
    log_header(session_id, "Travel Agent Processing")
    write_log(session_id, f"  User Query: {user_query}")
    history_messages.append({"role": "user", "content": user_query})

    for i in range(max_iters):
        log_step(session_id, f"Iteration {i+1}", "Thinking...")
        yield json.dumps({"type": "status", "message": f"Thinking (Step {i+1})..."}) + "\n"
        
        prompt = ""
        for m in history_messages:
            prompt += f"{m['role'].capitalize()}: {m['content']}\n\n"

        if not client:
            err = "Gemini Client not initialized (API key missing)."
            log_step(session_id, "Error", err)
            yield json.dumps({"type": "error", "message": err}) + "\n"
            return

        try:
            # We use synchronous call in an async generator. For high concurrency we'd use asyncio.to_thread, but this is fine here.
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            raw_text = response.text.strip()
        except Exception as e:
            err = f"API Error: {str(e)}"
            log_step(session_id, "Error", err)
            yield json.dumps({"type": "error", "message": err}) + "\n"
            return
            
        try:
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_text)
            if "thought" in parsed:
                log_step(session_id, "Thought", parsed["thought"])
                yield json.dumps({"type": "thought", "message": parsed["thought"]}) + "\n"
        except Exception as e:
            log_step(session_id, "Error", f"Error parsing LLM output: {raw_text}")
            yield json.dumps({"type": "error", "message": "Failed to parse agent response."}) + "\n"
            break

        if "answer" in parsed:
            log_header(session_id, "AGENT RESPONSE")
            write_log(session_id, parsed["answer"])
            history_messages.append({"role": "assistant", "content": raw_text})
            yield json.dumps({"type": "answer", "message": parsed["answer"]}) + "\n"
            return

        if "tool_name" in parsed:
            name = parsed["tool_name"]
            args = parsed.get("tool_arguments", {})
            log_step(session_id, "Action", f"Using {name} with {args}")
            yield json.dumps({"type": "action", "message": f"Calling {name}..."}) + "\n"
            
            if name in TOOL_REGISTRY:
                result = TOOL_REGISTRY[name](**args)
                log_step(session_id, "Observation", f"Data received: {result}")
                
                history_messages.append({"role": "assistant", "content": raw_text})
                history_messages.append({"role": "tool", "content": result})
            else:
                err = f"Tool {name} not found."
                log_step(session_id, "Error", err)
                yield json.dumps({"type": "error", "message": err}) + "\n"
                break
    
    yield json.dumps({"type": "error", "message": "Max iterations reached without a final answer."}) + "\n"
