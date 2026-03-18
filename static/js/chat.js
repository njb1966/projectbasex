// ─── ProjectBaseX Chat ────────────────────────────────────────────────────────

const Chat = (() => {
  let projectId       = null;
  let conversationId  = null;
  let currentMode     = 'general';
  let isStreaming     = false;

  const MODES = {
    general:  { label: 'General',  desc: 'Open conversation about this project' },
    planning: { label: 'Planning', desc: 'Build a spec before writing code' },
    stuck:    { label: 'Stuck',    desc: 'Diagnose a problem without burning tokens' },
    review:   { label: 'Review',   desc: 'Honest assessment of current state' },
    decision: { label: 'Decision', desc: 'Tradeoff analysis — you decide' },
  };

  function init(pid) {
    projectId = pid;
    bindEvents();
    loadConversation();
  }

  function bindEvents() {
    document.getElementById('chat-send-btn').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') sendMessage();
    });
    document.getElementById('chat-new-btn').addEventListener('click', showModeSelector);
    document.getElementById('chat-mode-confirm').addEventListener('click', startNewConversation);
    document.getElementById('chat-mode-cancel').addEventListener('click', hideModeSelector);
  }

  async function loadConversation() {
    const res = await fetch(`/projects/${projectId}/chat`);
    const data = await res.json();

    if (!data.conversation) {
      showEmptyState();
      return;
    }

    conversationId = data.conversation.id;
    currentMode    = data.conversation.mode;
    updateModeDisplay(currentMode);
    updateTokenDisplay(data.total_input || 0, data.total_output || 0);

    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    data.messages.forEach(m => appendMessage(m.role, m.content, false));
    scrollToBottom();
  }

  async function sendMessage() {
    if (isStreaming) return;

    const input   = document.getElementById('chat-input');
    const content = input.value.trim();
    if (!content) { input.focus(); return; }

    input.value = '';
    appendMessage('user', content, false);
    scrollToBottom();

    const assistantDiv = appendMessage('assistant', '', true);
    isStreaming = true;
    updateSendBtn(true);

    try {
      const res = await fetch(`/projects/${projectId}/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          conversation_id: conversationId,
          mode: currentMode,
        }),
      });

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer    = '';
      let fullText  = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = JSON.parse(line.slice(6));

          if (payload.error) {
            setMessageContent(assistantDiv, `⚠️ ${payload.error}`);
            break;
          }
          if (payload.done) {
            conversationId = payload.conversation_id;
            hideEmptyState();
            updateTokenDisplay(payload.total_input || 0, payload.total_output || 0);
            break;
          }
          if (payload.text) {
            fullText += payload.text;
            setMessageContent(assistantDiv, fullText, true);
            scrollToBottom();
          }
        }
      }
    } catch (err) {
      setMessageContent(assistantDiv, `⚠️ Connection error: ${err.message}`);
    } finally {
      isStreaming = false;
      updateSendBtn(false);
      removeTypingCursor(assistantDiv);
      scrollToBottom();
    }
  }

  function appendMessage(role, content, isStreaming) {
    const container = document.getElementById('chat-messages');
    const empty     = document.getElementById('chat-empty');
    if (empty) empty.style.display = 'none';

    const div = document.createElement('div');
    div.className = `chat-message chat-message-${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    if (isStreaming) {
      bubble.innerHTML = '<span class="typing-cursor">▋</span>';
    } else {
      bubble.innerHTML = renderMarkdown(content);
    }

    div.appendChild(bubble);
    container.appendChild(div);
    return div;
  }

  function setMessageContent(div, text, streaming = false) {
    const bubble = div.querySelector('.chat-bubble');
    if (streaming) {
      bubble.innerHTML = renderMarkdown(text) + '<span class="typing-cursor">▋</span>';
    } else {
      bubble.innerHTML = renderMarkdown(text);
    }
  }

  function removeTypingCursor(div) {
    const cursor = div.querySelector('.typing-cursor');
    if (cursor) cursor.remove();
  }

  // Minimal markdown: bold, code blocks, inline code, line breaks
  function renderMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      // code blocks
      .replace(/```[\w]*\n?([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      // inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // bold
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // italic
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      // numbered lists
      .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
      // bullet lists
      .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
      // wrap consecutive li items
      .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
      // line breaks (after code blocks handled)
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^(.+)$/, '<p>$1</p>');
  }

  function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
  }

  function updateSendBtn(sending) {
    const btn = document.getElementById('chat-send-btn');
    btn.textContent = sending ? '...' : 'Send';
    btn.disabled = sending;
  }

  function updateModeDisplay(mode) {
    currentMode = mode;
    const info = MODES[mode] || MODES.general;
    const badge = document.getElementById('chat-mode-badge');
    const desc  = document.getElementById('chat-mode-desc');
    if (badge) { badge.textContent = info.label; badge.className = `chat-mode-badge mode-${mode}`; }
    if (desc)  { desc.textContent = info.desc; }

    // Update mode select if visible
    const sel = document.getElementById('chat-mode-select');
    if (sel) sel.value = mode;
  }

  function showEmptyState() {
    const empty = document.getElementById('chat-empty');
    if (empty) empty.style.display = 'block';
  }

  function hideEmptyState() {
    const empty = document.getElementById('chat-empty');
    if (empty) empty.style.display = 'none';
  }

  function showModeSelector() {
    document.getElementById('chat-mode-picker').style.display = 'block';
  }

  function hideModeSelector() {
    document.getElementById('chat-mode-picker').style.display = 'none';
  }

  function updateTokenDisplay(inputTokens, outputTokens) {
    const el = document.getElementById('chat-token-count');
    if (!el) return;
    const total = inputTokens + outputTokens;
    if (total === 0) { el.textContent = ''; return; }
    el.textContent = `${total.toLocaleString()} tokens (↑${inputTokens.toLocaleString()} ↓${outputTokens.toLocaleString()})`;
  }

  async function startNewConversation() {
    const sel  = document.getElementById('chat-mode-select');
    const mode = sel ? sel.value : 'general';

    const res  = await fetch(`/projects/${projectId}/chat/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
    const data = await res.json();

    conversationId = data.conversation_id;
    updateModeDisplay(mode);
    hideModeSelector();

    document.getElementById('chat-messages').innerHTML = '';
    updateTokenDisplay(0, 0);
    showEmptyState();
  }

  // Start a new conversation in a given mode, switch to the AI tab, and send a pre-set message.
  async function healthCheck(message) {
    // Switch to AI tab
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    const aiBtn = document.querySelector('.tab-btn[data-tab="ai"]');
    if (aiBtn) aiBtn.classList.add('active');
    const aiPanel = document.getElementById('tab-ai');
    if (aiPanel) aiPanel.classList.add('active');
    location.hash = 'ai';

    // Start fresh review conversation
    const res  = await fetch(`/projects/${projectId}/chat/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'review' }),
    });
    const data = await res.json();

    conversationId = data.conversation_id;
    updateModeDisplay('review');
    hideModeSelector();
    document.getElementById('chat-messages').innerHTML = '';
    updateTokenDisplay(0, 0);
    showEmptyState();

    // Pre-fill and send
    const input = document.getElementById('chat-input');
    input.value = message;
    sendMessage();
  }

  return { init, healthCheck };
})();
