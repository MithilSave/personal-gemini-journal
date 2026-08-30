// ============================================
// MindScribe — Client Application Logic (Liquid Glass & Features)
// ============================================

// ---- Firebase Configuration ----
const firebaseConfig = {
  apiKey: "AIzaSyBILh0KFv_HaHozQoHDPVXG4r7iUAlPVnI",
  authDomain: "personal-gemini-journal-507013.firebaseapp.com",
  projectId: "personal-gemini-journal-507013",
  appId: "1:73858131259:web:75837c4f49cd470565431e"
};
firebase.initializeApp(firebaseConfig);

// ---- Application State ----
let idToken = null;
let currentJournalId = null;
let chatHistory = [];
let isRecording = false;

// ---- DOM References ----
const loginBtn = document.getElementById('login-btn');
const newSessionBtn = document.getElementById('new-session-btn');
const userDisplay = document.getElementById('user-display');
const userName = document.getElementById('user-name');
const userAvatar = document.getElementById('user-avatar');

const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const summarizeBtn = document.getElementById('summarize-btn');
const micBtn = document.getElementById('mic-btn');
const chatWindow = document.getElementById('chat-window');
const welcomeScreen = document.getElementById('welcome-screen');

const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const sessionIdDisplay = document.getElementById('session-id');

const sidebar = document.getElementById('sidebar');
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
const sidebarList = document.getElementById('sidebar-list');
const moodSection = document.getElementById('mood-section');
const moodChartCanvas = document.getElementById('mood-chart');
const moodLegend = document.getElementById('mood-legend');

// ---- Scroll Animation Observer ----
const scrollObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      // Optional: stop observing once revealed
      // scrollObserver.unobserve(entry.target); 
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -20px 0px' });

// Utility to append elements and trigger scroll animation
function appendToChat(element) {
  element.classList.add('reveal-item');
  chatWindow.appendChild(element);
  scrollObserver.observe(element);
  
  // Smooth scroll to bottom
  setTimeout(() => {
    chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: 'smooth' });
  }, 50);
}

// ---- Voice-to-Text (Web Speech API) ----
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add('recording');
    chatInput.placeholder = "Listening...";
  };

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    chatInput.value = transcript;
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error", event.error);
    stopRecording();
  };

  recognition.onend = () => {
    stopRecording();
  };
} else {
  micBtn.style.display = 'none'; // Hide if unsupported
}

function stopRecording() {
  isRecording = false;
  micBtn.classList.remove('recording');
  chatInput.placeholder = "Reflect on your thoughts, challenges, or goals...";
}

micBtn.onclick = () => {
  if (!recognition) return;
  if (isRecording) {
    recognition.stop();
  } else {
    chatInput.value = '';
    recognition.start();
  }
};


// ---- Utility: Create Chat Message Element ----
function createMessage(role, content) {
  const wrapper = document.createElement('div');
  wrapper.className = `chat-msg ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? '✦' : '🧠';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = content;

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  return wrapper;
}

// ---- Utility: System Messages & Loaders ----
function showLoading() {
  const loader = document.createElement('div');
  loader.className = 'chat-loading reveal-item';
  loader.id = 'chat-loader';
  loader.innerHTML = `<div class="loading-dots"><span></span><span></span><span></span></div><span>Synthesizing...</span>`;
  appendToChat(loader);
}

function hideLoading() {
  const loader = document.getElementById('chat-loader');
  if (loader) loader.remove();
}

function showSystemMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'chat-system';
  msg.textContent = text;
  appendToChat(msg);
}


// ---- UI Rendering: Summary Card ----
function renderSummary(summary) {
  const card = document.createElement('div');
  card.className = 'summary-card glass-panel';

  const sentimentPct = ((summary.sentiment_score + 1) / 2) * 100;
  const sentimentColor = summary.sentiment_score >= 0.3 ? '#34d399' : summary.sentiment_score <= -0.3 ? '#fb7185' : '#fbbf24';
  const distortionTags = summary.cognitive_distortions_detected.map(d => `<span class="tag distortion">${d}</span>`).join('');
  const themeTags = summary.key_themes.map(t => `<span class="tag">${t}</span>`).join('');

  card.innerHTML = `
    <div class="summary-title"><span>📊</span> ${summary.title}</div>
    <div class="summary-grid">
      <div class="summary-item">
        <div class="label">Primary Emotion</div>
        <div class="value">${summary.primary_emotion}</div>
      </div>
      <div class="summary-item">
        <div class="label">Sentiment Valence</div>
        <div class="sentiment-gauge">
          <div class="sentiment-bar">
            <div class="sentiment-fill" style="width: ${sentimentPct}%; background: ${sentimentColor};"></div>
          </div>
          <span class="sentiment-label" style="color: ${sentimentColor};">${summary.sentiment_score.toFixed(2)}</span>
        </div>
      </div>
      <div class="summary-item">
        <div class="label">Key Themes</div>
        <div class="summary-tags">${themeTags}</div>
      </div>
      <div class="summary-item">
        <div class="label">Cognitive Distortions</div>
        <div class="summary-tags">${distortionTags || '<span class="value">None detected</span>'}</div>
      </div>
    </div>
    <div class="summary-item" style="margin-bottom: 1rem;">
      <div class="label">Action Items</div>
      <div class="value" style="font-size: 0.85rem;">${summary.action_items.map((item, i) => `${i + 1}. ${item}`).join('<br>')}</div>
    </div>
    <div class="summary-insight">
      <strong>💡 Growth Insight:</strong> ${summary.growth_insight}
    </div>
  `;
  appendToChat(card);
}

// ---- Sidebar & History Replay ----
sidebarToggleBtn.onclick = () => sidebar.classList.toggle('collapsed');
sidebarCloseBtn.onclick = () => sidebar.classList.add('collapsed');

async function loadSidebarHistory() {
  if (!idToken) return;
  try {
    const res = await fetch('/api/journals', { headers: { 'Authorization': `Bearer ${idToken}` }});
    const data = await res.json();
    
    if (data.journals.length === 0) {
      sidebarList.innerHTML = '<p class="sidebar-empty">No journals yet. Start reflecting!</p>';
      return;
    }

    sidebarList.innerHTML = '';
    data.journals.forEach(j => {
      const el = document.createElement('div');
      el.className = `journal-item ${j.id === currentJournalId ? 'active' : ''}`;
      
      const title = j.summary?.title || 'Untitled Session';
      const emotion = j.summary?.primary_emotion || 'Neutral';
      const date = j.last_updated ? new Date(j.last_updated).toLocaleDateString() : 'Just now';

      el.innerHTML = `
        <div class="journal-item-title">${title}</div>
        <div class="journal-item-meta">
          <span>${date}</span>
          <span class="journal-item-emotion">${emotion}</span>
        </div>
      `;
      
      el.onclick = () => loadSession(j.id);
      sidebarList.appendChild(el);
    });

    loadMoodChart();
  } catch (err) {
    console.error("Error loading sidebar", err);
  }
}

async function loadSession(journalId) {
  if (currentJournalId === journalId) return;
  if (window.innerWidth < 900) sidebar.classList.add('collapsed');

  showLoading();
  try {
    const res = await fetch(`/api/journals/${journalId}/messages`, { headers: { 'Authorization': `Bearer ${idToken}` }});
    const data = await res.json();
    
    currentJournalId = journalId;
    chatHistory = [];
    chatWindow.innerHTML = ''; // clear chat
    sessionIdDisplay.textContent = `Session: ${journalId.slice(0, 8)}…`;

    data.messages.forEach(msg => {
      chatHistory.push({ role: msg.role, content: msg.content });
      appendToChat(createMessage(msg.role, msg.content));
    });

    // Update sidebar active state
    loadSidebarHistory();
  } catch (err) {
    showSystemMessage("Failed to load session history.");
  } finally {
    hideLoading();
  }
}

newSessionBtn.onclick = () => {
  currentJournalId = null;
  chatHistory = [];
  chatWindow.innerHTML = '';
  sessionIdDisplay.textContent = 'New Session';
  showSystemMessage('New session started. What is on your mind?');
  loadSidebarHistory(); // clear active state
  chatInput.focus();
};

// ---- Mood Timeline Chart (Canvas) ----
async function loadMoodChart() {
  try {
    const res = await fetch('/api/mood-timeline', { headers: { 'Authorization': `Bearer ${idToken}` }});
    const data = await res.json();
    const timeline = data.timeline;

    if (timeline.length < 2) {
      moodSection.classList.remove('visible');
      return;
    }
    
    moodSection.classList.add('visible');
    const ctx = moodChartCanvas.getContext('2d');
    const w = moodChartCanvas.width;
    const h = moodChartCanvas.height;
    
    ctx.clearRect(0, 0, w, h);
    
    // Config
    const padX = 20;
    const padY = 20;
    const graphW = w - padX * 2;
    const graphH = h - padY * 2;

    // Draw zero line (neutral)
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(255,255,255,0.1)';
    ctx.setLineDash([5, 5]);
    ctx.moveTo(padX, h / 2);
    ctx.lineTo(w - padX, h / 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // Map data to points
    const points = timeline.map((entry, i) => {
      const x = padX + (i / (timeline.length - 1)) * graphW;
      // Sentiment is -1 to 1. Map to graphH.
      const normalizedY = (entry.sentiment_score * -1 + 1) / 2; 
      const y = padY + normalizedY * graphH;
      return { x, y, val: entry.sentiment_score };
    });

    // Draw line
    ctx.beginPath();
    ctx.strokeStyle = '#818cf8'; // Indigo
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.stroke();

    // Fill under line
    ctx.lineTo(points[points.length-1].x, h - padY);
    ctx.lineTo(points[0].x, h - padY);
    ctx.closePath();
    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, 'rgba(129, 140, 248, 0.4)');
    gradient.addColorStop(1, 'rgba(129, 140, 248, 0)');
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw dots
    points.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = p.val >= 0.3 ? '#34d399' : p.val <= -0.3 ? '#fb7185' : '#fbbf24';
      ctx.fill();
      ctx.strokeStyle = '#0b0f1a';
      ctx.lineWidth = 2;
      ctx.stroke();
    });

  } catch (err) {
    console.error("Chart error", err);
  }
}

// ---- Authentication: Google Sign-In ----
loginBtn.onclick = async () => {
  try {
    const provider = new firebase.auth.GoogleAuthProvider();
    const res = await firebase.auth().signInWithPopup(provider);
    idToken = await res.user.getIdToken();

    const displayName = res.user.displayName || 'User';
    const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

    userName.textContent = displayName;
    userAvatar.textContent = initials;
    userDisplay.classList.remove('hidden');
    loginBtn.classList.add('hidden');
    newSessionBtn.classList.remove('hidden');

    chatInput.disabled = false;
    sendBtn.disabled = false;
    summarizeBtn.disabled = false;
    micBtn.disabled = false;

    statusDot.classList.remove('offline');
    statusDot.classList.add('online');
    statusText.textContent = 'Authenticated & Encrypted';

    if (welcomeScreen) welcomeScreen.remove();
    showSystemMessage('Session initialized. What would you like to reflect on today?');

    loadSidebarHistory();
    chatInput.focus();
  } catch (err) {
    console.error('Auth error:', err);
    showSystemMessage('Authentication failed. Ensure popup is allowed and config is correct.');
  }
};

// ---- Chat: Send Message ----
async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message || !idToken) return;

  chatInput.value = '';
  sendBtn.disabled = true;

  appendToChat(createMessage('user', message));
  chatHistory.push({ role: 'user', content: message });

  showLoading();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${idToken}` },
      body: JSON.stringify({ journal_id: currentJournalId, message, history: chatHistory })
    });

    if (!res.ok) throw new Error(`API error: ${res.status}`);

    const data = await res.json();
    currentJournalId = data.journal_id;
    chatHistory.push({ role: 'model', content: data.reply });

    hideLoading();
    appendToChat(createMessage('model', data.reply));

    sessionIdDisplay.textContent = `Session: ${currentJournalId.slice(0, 8)}…`;
    loadSidebarHistory(); // update last_updated in sidebar
  } catch (err) {
    hideLoading();
    showSystemMessage('Failed to get response. Please try again.');
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

sendBtn.onclick = sendMessage;
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ---- Summarize: Cognitive Analysis ----
summarizeBtn.onclick = async () => {
  if (!currentJournalId || !idToken) return;
  summarizeBtn.disabled = true;
  showSystemMessage('Synthesizing cognitive metrics…');
  showLoading();

  try {
    const res = await fetch(`/api/summarize/${currentJournalId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${idToken}` }
    });
    if (!res.ok) throw new Error(`API error`);
    const data = await res.json();
    hideLoading();
    renderSummary(data.summary);
    loadSidebarHistory(); // Refresh chart & titles
  } catch (err) {
    hideLoading();
    showSystemMessage('Failed to generate summary.');
  } finally {
    summarizeBtn.disabled = false;
  }
};
