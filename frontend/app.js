const messagesContainer = document.getElementById('messages');
const ephemeralContainer = document.getElementById('ephemeral-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newSessionBtn = document.getElementById('new-session-btn');
const brainBtn = document.getElementById('brain-btn');
const welcomeMessage = document.querySelector('.welcome-message');

// Session Management - Always start fresh on load
let sessionId = generateSessionId();

function generateSessionId() {
    const now = new Date();
    const pad = (n) => n.toString().padStart(2, '0');
    return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

async function initSession() {
    sessionId = generateSessionId();
    // Clear UI
    messagesContainer.innerHTML = '';
    ephemeralContainer.innerHTML = '';
    welcomeMessage.style.display = 'block';

    // Ping backend to create log file instantly
    try {
        await fetch('/init_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
    } catch (e) {
        console.error("Failed to initialize session on backend", e);
    }
}

// Initialize on start
initSession();

newSessionBtn.addEventListener('click', initSession);

brainBtn.addEventListener('click', () => {
    // Placeholder for future "Under the hood" view
    alert(`Current Session ID: ${sessionId}\nCheck the logs directory on the backend for the detailed trace!`);
});

// Simple Markdown to HTML parser
function parseMarkdown(text) {
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    return html;
}

// UI Helpers
function appendMessage(role, content) {
    welcomeMessage.style.display = 'none'; // hide welcome on first message
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    msgDiv.classList.add(role === 'user' ? 'user-msg' : 'bot-msg');
    
    if (role === 'bot') {
        msgDiv.innerHTML = parseMarkdown(content);
    } else {
        msgDiv.textContent = content;
    }
    
    messagesContainer.appendChild(msgDiv);
    scrollToBottom();
}

function setEphemeralIndicator(type, text) {
    ephemeralContainer.innerHTML = '';
    if (!text) return;

    const div = document.createElement('div');
    div.classList.add('ephemeral-indicator');
    if (type === 'thought') div.classList.add('thought');

    const loader = `<div class="loader-dots"><span></span><span></span><span></span></div>`;
    
    div.innerHTML = `
        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" class="ephemeral-icon">
            ${type === 'thought' 
                ? '<path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"></path>' 
                : '<circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51z"></path>'}
        </svg>
        <span>${text}</span>
        ${loader}
    `;
    ephemeralContainer.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    const main = document.getElementById('chat-container');
    main.scrollTop = main.scrollHeight;
}

// Network Request
async function sendMessage(query) {
    if (!query.trim()) return;

    appendMessage('user', query);
    userInput.value = '';
    setEphemeralIndicator('thought', 'Thinking...');

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, query: query })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            
            // NDJSON means separated by newlines
            let lines = buffer.split('\n');
            buffer = lines.pop(); // Keep the last partial line in buffer

            for (let line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    
                    if (data.type === 'thought') {
                        setEphemeralIndicator('thought', data.message);
                    } else if (data.type === 'action' || data.type === 'status') {
                        setEphemeralIndicator('action', data.message);
                    } else if (data.type === 'answer') {
                        setEphemeralIndicator(null, null); // clear indicator
                        appendMessage('bot', data.message);
                    } else if (data.type === 'error') {
                        setEphemeralIndicator(null, null);
                        appendMessage('bot', `**Error:** ${data.message}`);
                    }
                } catch (e) {
                    console.error("Error parsing stream line:", line, e);
                }
            }
        }
    } catch (error) {
        console.error("Fetch error:", error);
        setEphemeralIndicator(null, null);
        appendMessage('bot', `**Connection Error:** Could not reach the server.`);
    }
}

// Event Listeners
sendBtn.addEventListener('click', () => {
    sendMessage(userInput.value);
});

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage(userInput.value);
    }
});

// Service Worker Registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('./sw.js')
            .then(reg => console.log('Service Worker registered', reg))
            .catch(err => console.error('Service Worker registration failed', err));
    });
}
