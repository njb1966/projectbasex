// ─── Idea Modal ───────────────────────────────────────────────────────────────

const ideaModal   = document.getElementById('idea-modal');
const newIdeaBtn  = document.getElementById('new-idea-btn');
const ideaClose   = document.getElementById('idea-modal-close');
const ideaCancel  = document.getElementById('idea-cancel');
const ideaSave    = document.getElementById('idea-save');

if (newIdeaBtn) {
  newIdeaBtn.addEventListener('click', () => {
    ideaModal.classList.add('visible');
    setTimeout(() => document.getElementById('idea-title').focus(), 50);
  });
}

function closeIdeaModal() {
  ideaModal.classList.remove('visible');
  document.getElementById('idea-title').value = '';
  document.getElementById('idea-description').value = '';
  document.getElementById('idea-sparked').value = '';
  const projSel = document.getElementById('idea-project');
  if (projSel) projSel.value = '';
}

if (ideaClose)  ideaClose.addEventListener('click', closeIdeaModal);
if (ideaCancel) ideaCancel.addEventListener('click', closeIdeaModal);
if (ideaModal)  ideaModal.addEventListener('click', e => { if (e.target === ideaModal) closeIdeaModal(); });

if (ideaSave) {
  ideaSave.addEventListener('click', async () => {
    const title = document.getElementById('idea-title').value.trim();
    if (!title) { document.getElementById('idea-title').focus(); return; }

    const projSel = document.getElementById('idea-project');
    const payload = {
      title,
      description:        document.getElementById('idea-description').value.trim(),
      sparked_by:         document.getElementById('idea-sparked').value.trim(),
      related_project_id: projSel ? projSel.value || null : null,
    };

    const res = await fetch('/ideas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      closeIdeaModal();
      showToast('Idea captured');
    }
  });
}

// ─── Status Change on Dashboard Cards ────────────────────────────────────────

document.querySelectorAll('.status-select[data-project-id]').forEach(sel => {
  sel.addEventListener('change', async () => {
    const projectId  = sel.dataset.projectId;
    const newStatus  = sel.value;
    const oldStatus  = sel.dataset.currentStatus;
    if (newStatus === oldStatus) return;

    let reason = '';
    if (['paused', 'needs-attention', 'archived'].includes(newStatus)) {
      reason = (prompt(`Reason for moving to "${newStatus}"? (optional, press Enter to skip)`) || '').trim();
    }

    const res = await fetch(`/projects/${projectId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus, reason }),
    });

    if (res.ok) {
      window.location.reload();
    } else {
      sel.value = oldStatus; // revert on failure
    }
  });
});

// ─── Status Change on Detail Page ────────────────────────────────────────────

const detailStatusSel = document.getElementById('detail-status-select');
if (detailStatusSel) {
  detailStatusSel.addEventListener('change', async () => {
    const projectId = detailStatusSel.dataset.projectId;
    const newStatus = detailStatusSel.value;
    const oldStatus = detailStatusSel.dataset.currentStatus;
    if (newStatus === oldStatus) return;

    let reason = '';
    if (['paused', 'needs-attention', 'archived'].includes(newStatus)) {
      reason = (prompt(`Reason for moving to "${newStatus}"? (optional)`) || '').trim();
    }

    const res = await fetch(`/projects/${projectId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus, reason }),
    });

    if (res.ok) {
      detailStatusSel.dataset.currentStatus = newStatus;
      const badge = document.getElementById('status-badge');
      if (badge) {
        badge.textContent = newStatus.replace(/-/g, ' ');
        badge.className = `badge badge-status-${newStatus}`;
      }
      showToast('Status updated');
    } else {
      detailStatusSel.value = oldStatus;
    }
  });
}

// ─── Notes (detail page) ─────────────────────────────────────────────────────

const addNoteBtn = document.getElementById('add-note-btn');
if (addNoteBtn) {
  addNoteBtn.addEventListener('click', async () => {
    const textarea  = document.getElementById('note-input');
    const content   = textarea.value.trim();
    if (!content) { textarea.focus(); return; }

    const projectId = addNoteBtn.dataset.projectId;
    const res = await fetch(`/projects/${projectId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });

    if (res.ok) {
      const note = await res.json();
      textarea.value = '';
      prependNote(note, projectId);
      const empty = document.getElementById('notes-empty');
      if (empty) empty.remove();
    }
  });

  // Ctrl+Enter submits
  document.getElementById('note-input').addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') addNoteBtn.click();
  });
}

function prependNote(note, projectId) {
  const list = document.getElementById('notes-list');
  const div  = document.createElement('div');
  div.className = 'note-item';
  div.dataset.noteId = note.id;
  div.innerHTML = `
    <div class="note-date">${formatDate(note.created_date)}</div>
    <div class="note-content">${escapeHtml(note.content)}</div>
    <button class="note-delete" data-note-id="${note.id}" data-project-id="${projectId}" onclick="deleteNote(this)">✕</button>
  `;
  list.insertBefore(div, list.firstChild);
}

function deleteNote(btn) {
  if (!confirm('Delete this note?')) return;
  const noteId    = btn.dataset.noteId;
  const projectId = btn.dataset.projectId;

  fetch(`/projects/${projectId}/notes/${noteId}`, { method: 'DELETE' })
    .then(res => {
      if (res.ok) btn.closest('.note-item').remove();
    });
}

// ─── Tabs ─────────────────────────────────────────────────────────────────────

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${target}`).classList.add('active');
    // Keep tab in URL hash for reload persistence
    history.replaceState(null, '', `#${target}`);
  });
});

// Restore tab from URL hash on load
(function() {
  const hash = location.hash.slice(1);
  if (hash) {
    const btn = document.querySelector(`.tab-btn[data-tab="${hash}"]`);
    if (btn) btn.click();
  }
})();

// ─── Lane Collapse / Expand ───────────────────────────────────────────────────

document.querySelectorAll('.lane-header.clickable').forEach(header => {
  header.addEventListener('click', () => {
    const lane = header.closest('.lane');
    const body = lane.querySelector('.lane-body');
    const collapsed = lane.classList.toggle('collapsed');
    body.style.display = collapsed ? 'none' : '';
  });
});

// ─── Toast ────────────────────────────────────────────────────────────────────

function showToast(msg) {
  document.querySelector('.toast')?.remove();
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => {
    requestAnimationFrame(() => t.classList.add('visible'));
  });
  setTimeout(() => {
    t.classList.remove('visible');
    setTimeout(() => t.remove(), 300);
  }, 2500);
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return iso; }
}
