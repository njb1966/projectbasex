"""
Git integration utilities for ProjectBaseX.

Two tiers:
  - is_git_repo(path)   — fast filesystem check, safe to call for every dashboard card
  - get_git_info(path)  — full subprocess info, used only on project detail page
  - get_recent_commits(path, n) — last N commits for timeline injection
"""
import os
import subprocess
from datetime import datetime, timezone


def is_git_repo(path):
    """
    Return True/False/None:
      True  — directory exists and contains a git repo
      False — directory exists but is NOT a git repo
      None  — directory path not set or doesn't exist
    """
    if not path:
        return None
    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        return None
    return os.path.isdir(os.path.join(expanded, '.git'))


def get_git_info(path):
    """
    Return a dict with full git info for a single project, or None if unavailable.

    Keys:
      branch, last_commit_hash, last_commit_short, last_commit_message,
      last_commit_date, last_commit_author, is_dirty, commit_count,
      remote_url, exists (bool), is_git (bool)
    """
    if not path:
        return None

    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        return {'exists': False, 'is_git': False}

    if not os.path.isdir(os.path.join(expanded, '.git')):
        return {'exists': True, 'is_git': False}

    def _run(*args):
        try:
            result = subprocess.run(
                ['git', '-C', expanded] + list(args),
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    branch       = _run('branch', '--show-current') or _run('rev-parse', '--abbrev-ref', 'HEAD')
    log_line     = _run('log', '-1', '--format=%H|%s|%aI|%an')
    dirty_output = _run('status', '--porcelain')
    commit_count = _run('rev-list', '--count', 'HEAD')
    remote_url   = _run('remote', 'get-url', 'origin')

    last_commit_hash    = None
    last_commit_short   = None
    last_commit_message = None
    last_commit_date    = None
    last_commit_author  = None

    if log_line:
        parts = log_line.split('|', 3)
        if len(parts) == 4:
            last_commit_hash    = parts[0]
            last_commit_short   = parts[0][:7]
            last_commit_message = parts[1]
            last_commit_date    = parts[2]
            last_commit_author  = parts[3]

    return {
        'exists':              True,
        'is_git':              True,
        'branch':              branch,
        'last_commit_hash':    last_commit_hash,
        'last_commit_short':   last_commit_short,
        'last_commit_message': last_commit_message,
        'last_commit_date':    last_commit_date,
        'last_commit_author':  last_commit_author,
        'is_dirty':            bool(dirty_output),
        'commit_count':        int(commit_count) if commit_count and commit_count.isdigit() else None,
        'remote_url':          remote_url,
    }


def get_recent_commits(path, n=15):
    """
    Return last N commits as list of dicts for timeline injection.
    Each dict: {hash, short_hash, message, date, author}
    Returns [] if not a git repo or on any error.
    """
    if not path:
        return []

    expanded = os.path.expanduser(path)
    if not os.path.isdir(os.path.join(expanded, '.git')):
        return []

    try:
        result = subprocess.run(
            ['git', '-C', expanded, 'log', f'-{n}', '--format=%H|%s|%aI|%an'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return []
    except Exception:
        return []

    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split('|', 3)
        if len(parts) == 4:
            commits.append({
                'hash':       parts[0],
                'short_hash': parts[0][:7],
                'message':    parts[1],
                'date':       parts[2],
                'author':     parts[3],
            })
    return commits
