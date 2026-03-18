import json
import uuid
import threading
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response, stream_with_context
import anthropic
from database import get_db
from config import Config
from utils.files import read_project_files, format_file_context
from utils.embeddings import retrieve, format_rag_context, ensure_file_embeddings

chat_bp = Blueprint('chat', __name__)

client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

# ─── Mode System Prompts ──────────────────────────────────────────────────────

BASE_PROMPT = """You are an AI collaborator embedded in ProjectBaseX, a project management tool for a solo developer named Nick. Your role is analytical partner — not a yes-man, not a cheerleader.

Core behaviors:
- Ask clarifying questions before making assumptions
- Challenge plans that seem vague, risky, or under-scoped
- Be honest about what could cause this project to stall
- Stop trial-and-error: if you need more information to give useful advice, ask for it first
- Be concise and direct — Nick works alone and values signal over noise
- Remember: one person, finite time, competing projects

{mode_instructions}

Current project context:
{project_context}"""

MODE_INSTRUCTIONS = {
    'planning': """The user wants help planning this project. Your job is to help develop a clear specification BEFORE any code is written.

Push on these questions:
- What exactly defines "done" for this project?
- What are the technical risks or unknowns?
- What could realistically cause this to stall?
- Is the scope achievable for a solo developer?
- What decisions need to be locked in before starting?

Challenge vague answers. A plan with unclear success criteria will fail.""",

    'stuck': """The user is stuck on a technical problem. DO NOT immediately suggest solutions.

Instead:
1. Ask 2-3 diagnostic questions to understand the actual problem first
2. Identify whether this is a knowledge gap, tool limitation, wrong approach, or missing context
3. If the problem involves niche or retro technology, acknowledge that your training data may be limited — do not guess
4. Suggest specific research steps and where to look, rather than trial-and-error coding
5. Only propose concrete solutions once you have a clear picture of the actual problem

Burning tokens on wrong approaches is exactly what this tool is designed to prevent.""",

    'review': """Provide an honest review of this project's current state. Be direct, not motivational.

Address:
- Is this project still aligned with its original plan?
- What concrete progress has been made since the project started?
- What are the realistic blockers ahead?
- Is the scope still right, or has it drifted?
- Honest recommendation: continue as-is, pivot, pause, or archive?

Do not sugarcoat. Nick needs accurate information to make good decisions.""",

    'decision': """The user needs help making a decision. Your job is tradeoff analysis — not making the decision for them.

Structure:
1. Clarify the options (ask if they're not clearly stated)
2. Identify key tradeoffs for each option
3. Flag which factors matter most given this project's context and constraints
4. Present the analysis clearly

Do NOT recommend a specific choice. Present the tradeoffs and let Nick decide.""",

    'general': """Open-ended conversation about this project. Be analytical and direct. Challenge assumptions when you spot them, ask clarifying questions when something is vague, and provide structured thinking rather than just agreement.""",
}


def build_project_context(project_id, db, query=None):
    """
    Build context for the AI system prompt.
    If query is provided, uses RAG to retrieve relevant chunks.
    Falls back to last 5 notes if no embeddings exist yet.
    """
    project = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        return "Project not found."

    p = dict(project)
    lines = [
        f"Name: {p['name']}",
        f"Status: {p['status']}",
        f"Category: {p['category']}",
    ]

    if p.get('description'):
        lines.append(f"Description: {p['description']}")
    if p.get('original_plan'):
        lines.append(f"What defines done: {p['original_plan']}")
    if p.get('directory_path'):
        lines.append(f"Directory: {p['directory_path']}")

    tech = json.loads(p.get('tech_stack') or '[]')
    if tech:
        lines.append(f"Tech stack: {', '.join(tech)}")

    tags = json.loads(p.get('tags') or '[]')
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    # File context: directory listing + README + root .md/.txt files
    # Also triggers embedding of any new/changed files
    file_result = None
    if p.get('directory_path'):
        file_result = read_project_files(p['directory_path'])
        file_ctx = format_file_context(file_result)
        if file_ctx:
            lines.append(f"\n{file_ctx}")
        # Index file contents for RAG in background — never blocks the response
        if file_result and file_result.get('files'):
            files_copy = file_result['files']
            t = threading.Thread(
                target=ensure_file_embeddings,
                args=(project_id, files_copy),
                daemon=True
            )
            t.start()

    # Notes context: RAG if query provided, else last 5 notes
    if query:
        chunks = retrieve(project_id, query)
        rag_ctx = format_rag_context(chunks)
        if rag_ctx:
            lines.append(f"\n{rag_ctx}")
        else:
            # No embeddings yet — fall back to recent notes
            lines.extend(_recent_notes_context(db, project_id))
    else:
        lines.extend(_recent_notes_context(db, project_id))

    return '\n'.join(lines)


def _recent_notes_context(db, project_id):
    notes = db.execute(
        "SELECT content FROM notes WHERE project_id=? ORDER BY created_date DESC LIMIT 5",
        (project_id,)
    ).fetchall()
    if not notes:
        return []
    lines = ["\nRecent notes:"]
    for n in notes:
        lines.append(f"  - {n['content'][:300].replace(chr(10), ' ')}")
    return lines


def build_system_prompt(mode, project_context):
    instructions = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS['general'])
    return BASE_PROMPT.format(
        mode_instructions=instructions,
        project_context=project_context,
    )


# ─── Routes ──────────────────────────────────────────────────────────────────

@chat_bp.route('/projects/<project_id>/chat')
def get_conversation(project_id):
    """Return the most recent conversation for a project, or empty state."""
    with get_db() as db:
        conv = db.execute(
            "SELECT * FROM conversations WHERE project_id = ? ORDER BY last_message DESC LIMIT 1",
            (project_id,)
        ).fetchone()

        if not conv:
            return jsonify({'conversation': None, 'messages': []})

        messages = db.execute(
            "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conv['id'],)
        ).fetchall()

    return jsonify({
        'conversation': dict(conv),
        'messages':     [dict(m) for m in messages],
        'total_input':  conv['total_input_tokens'],
        'total_output': conv['total_output_tokens'],
    })


@chat_bp.route('/projects/<project_id>/chat/new', methods=['POST'])
def new_conversation(project_id):
    """Start a fresh conversation with a given mode."""
    data = request.get_json()
    mode = data.get('mode', 'general')
    now = datetime.now(timezone.utc).isoformat()
    conv_id = str(uuid.uuid4())

    with get_db() as db:
        db.execute(
            "INSERT INTO conversations (id, project_id, mode, started, last_message) VALUES (?, ?, ?, ?, ?)",
            (conv_id, project_id, mode, now, now)
        )

    return jsonify({'conversation_id': conv_id, 'mode': mode, 'ok': True})


@chat_bp.route('/projects/<project_id>/chat/send', methods=['POST'])
def send(project_id):
    """Send a message and stream the response."""
    data = request.get_json()
    content = (data.get('content') or '').strip()
    conversation_id = data.get('conversation_id')
    mode = data.get('mode', 'general')

    if not content:
        return jsonify({'error': 'Content required'}), 400

    now = datetime.now(timezone.utc).isoformat()

    with get_db() as db:
        # Create conversation if needed
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO conversations (id, project_id, mode, started, last_message) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, project_id, mode, now, now)
            )

        # Save user message
        db.execute(
            "INSERT INTO messages (id, conversation_id, role, content, timestamp) VALUES (?, ?, 'user', ?, ?)",
            (str(uuid.uuid4()), conversation_id, content, now)
        )

        # Load full history for this conversation
        history = db.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,)
        ).fetchall()

        project_context = build_project_context(project_id, db, query=content)

    api_messages = [{'role': m['role'], 'content': m['content']} for m in history]
    system_prompt = build_system_prompt(mode, project_context)

    def generate():
        full_response = []
        try:
            with client.messages.stream(
                model=Config.AI_MODEL,
                max_tokens=1500,
                system=system_prompt,
                messages=api_messages,
            ) as stream:
                for text in stream.text_stream:
                    full_response.append(text)
                    yield f"data: {json.dumps({'text': text})}\n\n"

            # Capture token usage and save assistant response
            response_text = ''.join(full_response)
            final_msg     = stream.get_final_message()
            input_tokens  = final_msg.usage.input_tokens
            output_tokens = final_msg.usage.output_tokens
            save_now      = datetime.now(timezone.utc).isoformat()

            with get_db() as db:
                db.execute(
                    "INSERT INTO messages (id, conversation_id, role, content, timestamp, input_tokens, output_tokens) VALUES (?, ?, 'assistant', ?, ?, ?, ?)",
                    (str(uuid.uuid4()), conversation_id, response_text, save_now, input_tokens, output_tokens)
                )
                db.execute("""
                    UPDATE conversations
                    SET last_message = ?,
                        total_input_tokens  = total_input_tokens  + ?,
                        total_output_tokens = total_output_tokens + ?
                    WHERE id = ?
                """, (save_now, input_tokens, output_tokens, conversation_id))

                totals = db.execute(
                    "SELECT total_input_tokens, total_output_tokens FROM conversations WHERE id = ?",
                    (conversation_id,)
                ).fetchone()

            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id, 'input_tokens': input_tokens, 'output_tokens': output_tokens, 'total_input': totals['total_input_tokens'], 'total_output': totals['total_output_tokens']})}\n\n"

        except anthropic.AuthenticationError:
            yield f"data: {json.dumps({'error': 'Invalid API key. Check your .env file.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )
