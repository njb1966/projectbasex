"""
Recommendation engine for "What should I work on?"

Scores non-completed projects by status priority + staleness.
Returns top N with a human-readable reason.
"""
from datetime import datetime, timezone

STATUS_SCORES = {
    'needs-attention': 80,
    'idle-review':     65,
    'active':          50,
    'planning':        35,
    'paused':          20,
    'idea':            10,
}

SKIP = {'completed', 'archived'}


def recommend(projects, top_n=3):
    """
    Score and rank projects. Returns top_n as list of dicts with
    added keys: rec_score, rec_reason, rec_urgency ('high'|'medium'|'low')
    """
    scored = []
    for p in projects:
        if p.get('status') in SKIP:
            continue
        days  = _days_since(p.get('last_modified') or p.get('created_date'))
        score = STATUS_SCORES.get(p['status'], 10) + _staleness(days)
        scored.append({
            **p,
            'rec_score':   score,
            'rec_reason':  _reason(p['status'], days),
            'rec_urgency': _urgency(score),
            'rec_days':    days,
        })

    scored.sort(key=lambda x: x['rec_score'], reverse=True)
    return scored[:top_n]


def _days_since(dt_str):
    if not dt_str:
        return 999
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - dt).days)
    except Exception:
        return 999


def _staleness(days):
    if days <= 2:   return 0
    if days <= 7:   return 8
    if days <= 14:  return 18
    if days <= 30:  return 28
    if days <= 90:  return 38
    return 48


def _urgency(score):
    if score >= 90:  return 'high'
    if score >= 55:  return 'medium'
    return 'low'


def _reason(status, days):
    if status == 'needs-attention':
        if days > 30:
            return f"Blocked for {days} days with no progress — needs a decision"
        if days > 7:
            return f"Stuck for {days} days — what's the actual blocker?"
        return "Actively blocked — this is your top priority"

    if status == 'idle-review':
        if days > 90:
            return f"Untouched for {days} days — continue, pause, or archive?"
        return f"No activity in {days} days — worth a quick review"

    if status == 'active':
        if days > 30:
            return f"Marked active but no movement in {days} days — is it actually stalled?"
        if days > 14:
            return f"Slowing down — {days} days since last touch"
        if days > 7:
            return f"A week without activity — pick it back up"
        return "Active and recent — keep the momentum going"

    if status == 'planning':
        if days > 14:
            return f"Been planning for {days} days — time to start building or decide not to"
        return "In planning — move to active when ready"

    if status == 'paused':
        if days > 60:
            return f"Paused {days} days ago — is this worth returning to?"
        return f"Paused {days} days ago — conditions changed?"

    if status == 'idea':
        if days > 30:
            return f"Idea sitting for {days} days — explore it or let it go"
        return "New idea — worth a planning session?"

    return f"Last touched {days} days ago"
