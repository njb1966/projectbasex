"""
File system reading utilities for AI context injection.

Strategy:
  1. README (any variant) from project root — highest priority
  2. All .md and .txt files in project root — not recursive
  3. Always inject a directory listing so Claude knows what exists
  4. Hard limits: 50KB per file, 200KB total across all files read
  5. Claude asks to dig deeper if it needs more
"""
import os

MAX_FILE_BYTES  = 50_000   # per file
MAX_TOTAL_BYTES = 200_000  # total across all files read

README_NAMES  = ['README.md', 'README.txt', 'README.rst', 'README']
READ_EXTENSIONS = {'.md', '.txt'}

# Files to skip — not useful as context
SKIP_NAMES = {
    'license', 'licence', 'license.md', 'licence.md',
    'license.txt', 'licence.txt', 'copying', 'copying.txt',
}


def read_project_files(directory_path):
    """
    Read README and root-level .md/.txt files from a project directory.
    Also returns a directory listing of all root-level files.
    Returns dict: {'files': [...], 'listing': [...]}
    """
    if not directory_path:
        return {'files': [], 'listing': []}

    path = os.path.expanduser(directory_path.strip())
    if not os.path.isdir(path):
        return {'files': [], 'listing': []}

    files       = []
    total_bytes = 0
    seen        = set()
    listing     = []

    # Collect directory listing (root level, files + dirs)
    try:
        for entry in sorted(os.scandir(path), key=lambda e: (e.is_dir(), e.name.lower())):
            if entry.name.startswith('.'):
                continue
            if entry.is_dir():
                listing.append(f"{entry.name}/")
            else:
                listing.append(entry.name)
    except PermissionError:
        pass

    # 1. README first
    for name in README_NAMES:
        fpath = os.path.join(path, name)
        if os.path.isfile(fpath):
            content = _safe_read(fpath, MAX_FILE_BYTES)
            if content is not None:
                files.append({'name': name, 'content': content})
                total_bytes += len(content.encode('utf-8'))
                seen.add(name.lower())
            break

    # 2. Other .md and .txt files in root
    try:
        entries = sorted(
            [e for e in os.scandir(path)
             if e.is_file()
             and os.path.splitext(e.name)[1].lower() in READ_EXTENSIONS
             and e.name.lower() not in seen
             and e.name.lower() not in SKIP_NAMES],
            key=lambda e: e.name.lower()
        )
        for entry in entries:
            if total_bytes >= MAX_TOTAL_BYTES:
                break
            size = entry.stat().st_size
            if size > MAX_FILE_BYTES:
                continue
            content = _safe_read(entry.path, MAX_FILE_BYTES)
            if content is not None:
                files.append({'name': entry.name, 'content': content})
                total_bytes += len(content.encode('utf-8'))
    except PermissionError:
        pass

    return {'files': files, 'listing': listing}


def _safe_read(fpath, max_bytes):
    """Read a file, returning None on any error or if it exceeds max_bytes."""
    try:
        if os.path.getsize(fpath) > max_bytes:
            return None
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except (OSError, PermissionError):
        return None


def format_file_context(result):
    """Format file read results into a string for injection into the system prompt."""
    files   = result.get('files', [])
    listing = result.get('listing', [])

    sections = []

    # Always include directory listing if we have one
    if listing:
        sections.append("Project directory contents (root level):\n" + '\n'.join(f"  {f}" for f in listing))

    # File contents
    if files:
        file_sections = []
        for f in files:
            content = f['content']
            if len(content) > 4000:
                content = content[:4000] + f"\n[... truncated — {len(f['content']) - 4000} more characters not shown. Ask the user to paste more if needed ...]"
            file_sections.append(f"### {f['name']}\n{content}")
        sections.append("Project files (readable root-level docs):\n\n" + "\n\n".join(file_sections))
    elif listing:
        sections.append("No README or text files were readable at the root level. Use the directory listing above to ask the user to paste relevant file contents.")

    return '\n\n'.join(sections) if sections else None
