# AI Travel Agent ✈️

> A professional, agentic AI travel assistant that demonstrates the "Thought-Action-Observation" loop in real-time.
> 
> ✨ **Real-time Data + Agentic Reasoning + Visual Trace = The Future of Travel Planning.**

📹 **Demo Video:** *[Coming Soon]*

<img width="1344" height="2540" alt="Screenshot_20260425-084512 (1)" src="https://github.com/user-attachments/assets/e540387f-5cee-44ca-a209-5e8b11772fe9" />
<img width="1340" height="2546" alt="Screenshot_20260425-084455 (1)" src="https://github.com/user-attachments/assets/ece2e03b-ae64-4c55-9d50-d2b09804f843" />


---

## 📖 "The What" — What is this project?
The **AI Travel Agent** is an educational demonstration designed to demystify the "black box" of AI agents. While it functions as a travel planner, its primary purpose is to showcase how a Large Language Model (LLM) can be transformed into an **Autonomous Agent** that interacts with the real world in real-time.

Built with a premium glassmorphic UI, it provides a tactile and visual way to see an AI move through a logical sequence of reasoning and tool-calling.

---

## 🧠 "Under the Hood" — For the Curious Minds
We built this not just for travelers, but for students and the AI community. By tapping the **Brain Icon** (🧠) in the top-right corner, you can step inside the agent's mind.

Instead of seeing a messy terminal log, you get a beautiful, structured timeline of the agent's "Visual Trace":
- 👤 **Your Query**: Where it all starts.
- 🧠 **Internal Thought**: What the LLM is actually thinking before it acts.
- 🛠️ **Tool Execution**: Exactly which API was called and with what parameters.
- ✨ **Final Response**: The polished, data-backed answer delivered to you.

---

## 🤔 "The Why" — The Logic Behind the Agent
Most people see AI as a "text-in, text-out" box. This project exists to prove that AI can do much more—it can **Reason and Act (ReAct)**. 

The "Why" here is less about the travel problem itself and more about the **educational journey** of understanding the agentic loop. By using a simple set of travel-related tools, we can clearly visualize the foundational loop that powers every advanced AI agent:

1. **Thought (Reasoning)**: The LLM analyzes the user's intent and decides which real-world data it's missing.
2. **Action (Acting)**: The agent proactively triggers one of its 4 live tools (Weather, Currency, Holidays, or Timezone).
3. **Observation (Feedback)**: The agent "sees" the raw data returned from the API and updates its internal state.
4. **Agent Response**: The agent synthesizes all its thoughts and observations into a data-backed recommendation.

This project is a blueprint for students and developers to see exactly what happens "under the hood" of the next generation of AI applications.

---

## 🛠️ "How to run it"
Since this project uses local session logging and private API keys, you'll need to run it locally on your machine.

### 1. Clone the Repository
```bash
git clone https://github.com/pradeepelavarasan/travel-agent.git
cd travel-agent
```

### 2. Set Up the Environment
Create a virtual environment to keep your system clean:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Configure your API Key
Create a file named `.env` in the root directory and add your Gemini API key:
```text
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```
*(You can get a free API key at [Google AI Studio](https://aistudio.google.com/))*

### 4. Launch the Agent
```bash
python backend/main.py
```
Open your browser to `http://localhost:8000` and start planning!

---

## 🏗️ Architecture & Logic

```text
┌─────────────────────────────────────────────────────┐
│                  Frontend (HTML/CSS/JS)             │
│                                                     │
│  ├─ Dynamic Chat UI (Glassmorphic)                  │
│  ├─ "Under the Hood" Trace Viewer                   │
│  └─ Service Worker (PWA Offline Support)            │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               Backend (FastAPI Server)              │
│                                                     │
│  1. Manages Real-time Streaming (NDJSON)            │
│  2. Handles Session-based File Logging              │
│  3. Orchestrates the Agentic Loop                   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                Agentic AI Engine                    │
│                                                     │
│  🧠 Thought: Decides what tools are needed          │
│  🛠️ Action: Calls Live Public APIs                  │
│  👁️ Observation: Processes tool output               │
└────────────────────────┬────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
     [ Live Weather ]          [ Currency API ]
     (wttr.in)                 (Frankfurter)
            
            ▼                         ▼
     [ Holiday API ]           [ Timezone API ]
     (Nager.Date)              (TimeAPI.io)
```

### Key Technology Choices
| Layer | Technology | Why |
|---|---|---|
| **AI Model** | Gemini / Gemma | Large context window and natively handles tool-calling logic. |
| **Backend** | FastAPI | High performance, asynchronous streaming, and easy API routing. |
| **Frontend** | Vanilla JS / CSS | Zero-dependency, lightweight, and allows for custom glassmorphic animations. |
| **Real-time** | NDJSON Streams | Allows the agent's "thoughts" to appear instantly as they happen. |
| **Storage** | Local Log Files | Provides a permanent, local audit trail of every agent interaction. |

---

*Built by [Pradeep Elavarasan](https://www.linkedin.com/in/pradeepelavarasan/) · Co-created with Google Agent*
