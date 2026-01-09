#!/usr/bin/env python3
"""
AI Offensive Code Review - HTML Report Generator
Reads CSV artifacts and generates a navigable HTML report.
Standard library only.
"""

import csv
import html
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
ARTIFACTS_DIR = Path("ai_artifacts")
OUTPUT_FILE = ARTIFACTS_DIR / "report.html"

# CSV files
OVERVIEW_MD = ARTIFACTS_DIR / "stage0" / "overview.md"
SERVICES_CSV = ARTIFACTS_DIR / "stage1" / "services.csv"
DEPS_CSV = ARTIFACTS_DIR / "stage1" / "dependencies.csv"
ENTRY_CSV = ARTIFACTS_DIR / "stage2" / "entry_points.csv"
STATE_CSV = ARTIFACTS_DIR / "stage3" / "state_and_links.csv"
FINDINGS_CSV = ARTIFACTS_DIR / "stage4" / "findings.csv"


def read_overview():
    """Read overview markdown file."""
    if not OVERVIEW_MD.exists():
        return None
    with open(OVERVIEW_MD, 'r', encoding='utf-8') as f:
        return f.read()


def read_csv_with_aliases(filepath):
    """Read CSV, extracting path aliases from comment lines."""
    aliases = {}
    rows = []

    if not filepath.exists():
        return aliases, rows

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#alias,'):
                parts = line.split(',')
                if len(parts) >= 3:
                    aliases[parts[1]] = parts[2]
            elif line and not line.startswith('#'):
                break

        f.seek(0)
        reader = csv.DictReader(
            (line for line in f if not line.startswith('#'))
        )
        rows = list(reader)

    return aliases, rows


def read_csv(filepath):
    """Simple CSV read."""
    if not filepath.exists():
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def resolve_path(alias_path, aliases):
    """Convert alias:relative/path to full path."""
    if ':' in alias_path and not alias_path.startswith('/'):
        alias, rel = alias_path.split(':', 1)
        base = aliases.get(alias, '')
        return os.path.join(base, rel) if base else alias_path
    return alias_path


def extract_snippet(filepath, func_name, context_lines=40):
    """Extract code snippet around a function definition."""
    if not os.path.exists(filepath):
        return None, "File not found"

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        return None, str(e)

    # Find function definition
    func_patterns = [
        rf'^\s*func\s+.*{re.escape(func_name)}\s*\(',  # Go
        rf'^\s*def\s+{re.escape(func_name)}\s*\(',     # Python
        rf'^\s*(async\s+)?function\s+{re.escape(func_name)}\s*\(',  # JS
        rf'^\s*(export\s+)?(const|let|var)\s+{re.escape(func_name)}\s*=',  # JS arrow
        rf'^\s*{re.escape(func_name)}\s*:\s*function',  # JS object method
        rf'^\s*(public|private|protected)?\s*(static)?\s*\w+\s+{re.escape(func_name)}\s*\(',  # Java
    ]

    func_line = None
    for i, line in enumerate(lines):
        for pattern in func_patterns:
            if re.search(pattern, line):
                func_line = i
                break
        if func_line is not None:
            break

    if func_line is None:
        # Fallback: search for function name anywhere
        for i, line in enumerate(lines):
            if func_name in line:
                func_line = i
                break

    if func_line is None:
        return None, "Function not found"

    start = max(0, func_line - 5)
    end = min(len(lines), func_line + context_lines)

    snippet_lines = []
    for i in range(start, end):
        snippet_lines.append(f"{i+1:4d} | {lines[i].rstrip()}")

    return '\n'.join(snippet_lines), None


def slugify(text):
    """Create URL-safe slug."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def esc(text):
    """HTML escape."""
    return html.escape(str(text)) if text else ''


def md_to_html(md_text):
    """Simple markdown to HTML conversion for overview."""
    if not md_text:
        return ''
    lines = md_text.split('\n')
    html_lines = []
    in_code = False
    in_list = False

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            else:
                html_lines.append('<pre><code>')
                in_code = True
            continue

        if in_code:
            html_lines.append(esc(line))
            continue

        # Headers
        if line.startswith('## '):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append(f'<h4>{esc(line[3:])}</h4>')
        elif line.startswith('# '):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append(f'<h3>{esc(line[2:])}</h3>')
        # List items
        elif line.strip().startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            # Handle bold
            item = line.strip()[2:]
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
            html_lines.append(f'<li>{item}</li>')
        # Empty line
        elif not line.strip():
            if in_list:
                html_lines.append('</ul>')
                in_list = False
        # Regular text
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', esc(line))
            html_lines.append(f'<p>{text}</p>')

    if in_list:
        html_lines.append('</ul>')

    return '\n'.join(html_lines)


def generate_html(services, deps, entries, state, findings, aliases, overview=None):
    """Generate the full HTML report."""

    # Group data by service
    entries_by_svc = defaultdict(list)
    for e in entries:
        entries_by_svc[e.get('svc_name', 'unknown')].append(e)

    state_by_svc = defaultdict(list)
    for s in state:
        state_by_svc[s.get('svc_name', 'unknown')].append(s)

    findings_by_svc = defaultdict(list)
    for f in findings:
        findings_by_svc[f.get('svc_name', 'unknown')].append(f)

    deps_by_svc = defaultdict(list)
    for d in deps:
        deps_by_svc[d.get('svc_name', 'unknown')].append(d)

    # Dangerous patterns for "look at first"
    dangerous_types = {'SUBPROCESS_EXEC', 'FILE_INTERACTION', 'EXTERNAL_CALL_INPUT', 'DANGEROUS_PRIMITIVE'}
    priority_findings = [f for f in findings if f.get('condition_type') in dangerous_types]

    # Count stats
    svc_names = list(set(s.get('svc_name', '') for s in services))
    http_count = sum(1 for e in entries if e.get('entry_type') == 'HTTP')
    queue_count = sum(1 for e in entries if e.get('entry_type') == 'QUEUE')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html_parts = [f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Security Review Report</title>
<style>
:root {{
    --bg: #0d1117;
    --fg: #c9d1d9;
    --accent: #58a6ff;
    --border: #30363d;
    --card-bg: #161b22;
    --warn: #d29922;
    --code-bg: #0d1117;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--fg);
    line-height: 1.6;
    display: flex;
}}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* Sidebar */
#sidebar {{
    width: 260px;
    height: 100vh;
    position: fixed;
    background: var(--card-bg);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    padding: 1rem;
}}
#sidebar h2 {{ font-size: 0.9rem; color: var(--accent); margin: 1rem 0 0.5rem; }}
#sidebar ul {{ list-style: none; }}
#sidebar li {{ margin: 0.25rem 0; }}
#sidebar a {{ display: block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem; }}
#sidebar a:hover {{ background: var(--border); }}
#search {{
    width: 100%;
    padding: 0.5rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--fg);
    margin-bottom: 1rem;
}}

/* Main content */
main {{
    margin-left: 260px;
    padding: 2rem;
    max-width: 1200px;
    width: 100%;
}}
h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
h2 {{ font-size: 1.4rem; margin: 2rem 0 1rem; padding-top: 1rem; border-top: 1px solid var(--border); }}
h3 {{ font-size: 1.1rem; margin: 1.5rem 0 0.75rem; color: var(--accent); }}

/* Cards */
.card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0;
}}
.card h4 {{ margin-bottom: 0.5rem; }}

/* Stats grid */
.stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}}
.stat {{
    background: var(--card-bg);
    padding: 1rem;
    border-radius: 6px;
    text-align: center;
}}
.stat-num {{ font-size: 2rem; font-weight: bold; color: var(--accent); }}
.stat-label {{ font-size: 0.8rem; color: #8b949e; }}

/* Tables */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    font-size: 0.85rem;
    table-layout: fixed;
}}
th, td {{
    padding: 0.5rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
    word-wrap: break-word;
    overflow-wrap: break-word;
    max-width: 200px;
}}
td code {{
    word-break: break-all;
}}
th {{
    background: var(--card-bg);
    cursor: pointer;
    user-select: none;
}}
th:hover {{ background: var(--border); }}
tr:hover {{ background: rgba(88, 166, 255, 0.1); }}

/* Code blocks */
pre {{
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1rem;
    overflow-x: auto;
    font-size: 0.8rem;
    line-height: 1.4;
    position: relative;
}}
.copy-btn {{
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: var(--border);
    border: none;
    color: var(--fg);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.7rem;
}}
.copy-btn:hover {{ background: var(--accent); color: var(--bg); }}

/* Tags */
.tag {{
    display: inline-block;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.75rem;
    margin-right: 0.25rem;
}}
.tag-http {{ background: #238636; }}
.tag-queue {{ background: #8957e5; }}
.tag-sdk {{ background: #d29922; }}
.tag-condition {{ background: var(--border); }}

/* Validation box */
.validation {{
    background: rgba(210, 153, 34, 0.1);
    border-left: 3px solid var(--warn);
    padding: 0.75rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
}}

/* Priority list */
.priority-item {{
    padding: 0.5rem;
    margin: 0.5rem 0;
    background: rgba(210, 153, 34, 0.1);
    border-radius: 4px;
}}

/* Searchable/filterable */
.searchable {{ transition: opacity 0.2s; }}
.hidden {{ display: none !important; }}
</style>
</head>
<body>

<nav id="sidebar">
    <input type="text" id="search" placeholder="Search..." onkeyup="filterContent()">

    <h2>Overview</h2>
    <ul>
        <li><a href="#app-overview">Application</a></li>
        <li><a href="#executive">Executive Map</a></li>
        <li><a href="#attack-surface">Attack Surface</a></li>
    </ul>

    <h2>Services ({len(svc_names)})</h2>
    <ul>
''']

    for svc in svc_names:
        html_parts.append(f'        <li><a href="#svc-{slugify(svc)}">{esc(svc)}</a></li>\n')

    html_parts.append('''    </ul>

    <h2>Sections</h2>
    <ul>
        <li><a href="#entries">Entry Points</a></li>
        <li><a href="#findings">Leads</a></li>
        <li><a href="#dataflow">Data Flows</a></li>
        <li><a href="#deps">Dependencies</a></li>
    </ul>
</nav>

<main>
''')

    # Application Overview (from stage0)
    if overview:
        overview_html = md_to_html(overview)
        html_parts.append(f'''
<section id="app-overview">
<div class="card">
{overview_html}
</div>
</section>
''')

    # Executive Map
    html_parts.append(f'''
<section id="executive">
<h1>Security Review Report</h1>
<p style="color:#8b949e">Generated: {timestamp}</p>

<div class="stats">
    <div class="stat"><div class="stat-num">{len(svc_names)}</div><div class="stat-label">Services</div></div>
    <div class="stat"><div class="stat-num">{len(entries)}</div><div class="stat-label">Entry Points</div></div>
    <div class="stat"><div class="stat-num">{http_count}</div><div class="stat-label">HTTP Routes</div></div>
    <div class="stat"><div class="stat-num">{queue_count}</div><div class="stat-label">Queue Consumers</div></div>
    <div class="stat"><div class="stat-num">{len(findings)}</div><div class="stat-label">Leads</div></div>
</div>

<h3>What to Look at First</h3>
<div class="card">
''')

    if priority_findings:
        for f in priority_findings[:10]:
            html_parts.append(f'''<div class="priority-item">
    <strong>{esc(f.get('id', ''))}</strong> - {esc(f.get('condition_type', ''))}
    <br><small>{esc(f.get('svc_name', ''))} → {esc(f.get('entry_point', ''))}</small>
    <br><a href="#finding-{slugify(f.get('id', ''))}">Details →</a>
</div>
''')
    else:
        html_parts.append('<p>No high-priority conditions identified.</p>')

    html_parts.append('</div></section>')

    # Attack Surface Navigator
    html_parts.append('''
<section id="attack-surface">
<h2>Attack Surface Navigator</h2>
''')

    for svc in svc_names:
        svc_entries = entries_by_svc.get(svc, [])
        html_parts.append(f'''
<div class="card" id="svc-{slugify(svc)}">
<h3>{esc(svc)}</h3>
<table class="sortable">
<thead>
<tr><th>Type</th><th>Route/Command</th><th>Method</th><th>Handler</th><th>Params</th><th></th></tr>
</thead>
<tbody>
''')
        for e in svc_entries:
            entry_id = slugify(f"{svc}-{e.get('route', '')}-{e.get('method', '')}")
            tag_class = f"tag-{e.get('entry_type', 'http').lower()}"
            html_parts.append(f'''<tr class="searchable" data-search="{esc(e.get('route', ''))} {esc(e.get('handler_func', ''))}">
<td><span class="tag {tag_class}">{esc(e.get('entry_type', ''))}</span></td>
<td><code>{esc(e.get('route', ''))}</code></td>
<td>{esc(e.get('method', ''))}</td>
<td><code>{esc(e.get('handler_func', ''))}</code></td>
<td><small>{esc(e.get('param_sources', ''))}</small></td>
<td><a href="#entry-{entry_id}">→</a></td>
</tr>
''')
        html_parts.append('</tbody></table></div>')

    html_parts.append('</section>')

    # Entry Point Details
    html_parts.append('''
<section id="entries">
<h2>Entry Point Details</h2>
''')

    for svc in svc_names:
        for e in entries_by_svc.get(svc, []):
            entry_id = slugify(f"{svc}-{e.get('route', '')}-{e.get('method', '')}")
            handler_file = resolve_path(e.get('handler_file', ''), aliases)
            handler_func = e.get('handler_func', '')

            # Get related findings
            related = [f for f in findings_by_svc.get(svc, [])
                      if e.get('route', '') in f.get('entry_point', '')]

            # Get related state
            related_state = [s for s in state_by_svc.get(svc, [])
                           if s.get('src_func', '') == handler_func]

            # Try to get code snippet
            snippet, snippet_err = extract_snippet(handler_file, handler_func)

            html_parts.append(f'''
<div class="card searchable" id="entry-{entry_id}" data-search="{esc(e.get('route', ''))} {esc(handler_func)}">
<h4><span class="tag tag-{e.get('entry_type', 'http').lower()}">{esc(e.get('entry_type', ''))}</span> {esc(e.get('method', ''))} {esc(e.get('route', ''))}</h4>
<p><strong>Handler:</strong> <code>{esc(handler_func)}</code> in <code>{esc(e.get('handler_file', ''))}</code></p>
<p><strong>Parameters:</strong> {esc(e.get('param_sources', 'none'))}</p>
<p><strong>Calls:</strong> <code>{esc(e.get('called_funcs', 'none'))}</code></p>
''')

            if related_state:
                html_parts.append('<p><strong>State touched:</strong></p><ul>')
                for s in related_state:
                    html_parts.append(f'<li>{esc(s.get("artifact_type", ""))} {esc(s.get("op", ""))} → {esc(s.get("identifier", ""))}</li>')
                html_parts.append('</ul>')

            if related:
                html_parts.append('<p><strong>Related leads:</strong></p><ul>')
                for f in related:
                    html_parts.append(f'<li><a href="#finding-{slugify(f.get("id", ""))}">{esc(f.get("id", ""))}</a> - {esc(f.get("condition_type", ""))}</li>')
                html_parts.append('</ul>')

            if snippet:
                html_parts.append(f'''
<h5>Code</h5>
<pre><button class="copy-btn" onclick="copyCode(this)">Copy</button><code>{esc(snippet)}</code></pre>
''')
            elif snippet_err:
                html_parts.append(f'<p><em>Code snippet unavailable: {esc(snippet_err)}</em></p>')

            html_parts.append('</div>')

    html_parts.append('</section>')

    # Leads Catalog
    html_parts.append('''
<section id="findings">
<h2>Leads</h2>
<p>All items require human validation. Verify condition exists, test reachability, confirm preconditions can be met.</p>
''')

    for svc in svc_names:
        svc_findings = findings_by_svc.get(svc, [])
        if not svc_findings:
            continue

        html_parts.append(f'<h3>{esc(svc)}</h3>')

        for f in svc_findings:
            fid = f.get('id', '')
            html_parts.append(f'''
<div class="card searchable" id="finding-{slugify(fid)}" data-search="{esc(fid)} {esc(f.get('condition_type', ''))} {esc(f.get('description', ''))}">
<h4><span class="tag tag-condition">{esc(f.get('condition_type', ''))}</span> {esc(fid)}</h4>
<p><strong>Entry point:</strong> {esc(f.get('entry_point', ''))}</p>
<p><strong>Description:</strong> {esc(f.get('description', ''))}</p>
<p><strong>Preconditions:</strong> {esc(f.get('preconditions', 'none'))}</p>
<p><strong>State touched:</strong> {esc(f.get('state_touched', 'none'))}</p>
<p><strong>Cross-service:</strong> {esc(f.get('cross_svc', 'no'))}</p>
<p><strong>External dependency:</strong> {esc(f.get('ext_dep', 'no'))}</p>
</div>
''')

    html_parts.append('</section>')

    # Data Flows
    html_parts.append('''
<section id="dataflow">
<h2>Data Flows and State</h2>
<table class="sortable">
<thead>
<tr><th>Service</th><th>Type</th><th>Identifier</th><th>Op</th><th>Source</th><th>Target</th></tr>
</thead>
<tbody>
''')

    for s in state:
        html_parts.append(f'''<tr class="searchable" data-search="{esc(s.get('identifier', ''))} {esc(s.get('src_func', ''))}">
<td>{esc(s.get('svc_name', ''))}</td>
<td>{esc(s.get('artifact_type', ''))}</td>
<td><code>{esc(s.get('identifier', ''))}</code></td>
<td>{esc(s.get('op', ''))}</td>
<td><code>{esc(s.get('src_func', ''))}</code></td>
<td><code>{esc(s.get('target_func', ''))}</code></td>
</tr>
''')

    html_parts.append('</tbody></table></section>')

    # Dependencies
    html_parts.append('''
<section id="deps">
<h2>Dependencies</h2>
''')

    risky_keywords = ['exec', 'shell', 'sql', 'orm', 'serialize', 'pickle', 'yaml', 'template', 'crypto', 'jwt', 'http', 'request', 'socket']

    for svc in svc_names:
        svc_deps = deps_by_svc.get(svc, [])
        if not svc_deps:
            continue

        html_parts.append(f'''
<div class="card">
<h4>{esc(svc)}</h4>
<table>
<thead><tr><th>Dependency</th><th>Version</th><th>Scope</th><th>Notes</th></tr></thead>
<tbody>
''')
        for d in svc_deps:
            dep_name = d.get('dep_name', '').lower()
            notes = []
            for kw in risky_keywords:
                if kw in dep_name:
                    notes.append(kw)
            note_str = ', '.join(notes) if notes else '-'

            html_parts.append(f'''<tr>
<td><code>{esc(d.get('dep_name', ''))}</code></td>
<td>{esc(d.get('version', ''))}</td>
<td>{esc(d.get('scope', ''))}</td>
<td><small>{esc(note_str)}</small></td>
</tr>
''')
        html_parts.append('</tbody></table></div>')

    html_parts.append('</section>')

    # Footer and scripts
    html_parts.append('''
<footer style="margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border);color:#8b949e;font-size:0.8rem">
<p>All findings are leads requiring human validation. No severity assigned by design.</p>
</footer>

</main>

<script>
// Search filter
function filterContent() {
    const query = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('.searchable').forEach(el => {
        const text = (el.dataset.search || el.textContent).toLowerCase();
        el.classList.toggle('hidden', query && !text.includes(query));
    });
}

// Copy code
function copyCode(btn) {
    const code = btn.parentElement.querySelector('code').textContent;
    navigator.clipboard.writeText(code);
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 1500);
}

// Sortable tables
document.querySelectorAll('.sortable th').forEach((th, idx) => {
    th.addEventListener('click', () => {
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const dir = th.dataset.dir === 'asc' ? 'desc' : 'asc';
        th.dataset.dir = dir;

        rows.sort((a, b) => {
            const aVal = a.cells[idx]?.textContent || '';
            const bVal = b.cells[idx]?.textContent || '';
            return dir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        });

        rows.forEach(row => tbody.appendChild(row));
    });
});
</script>
</body>
</html>
''')

    return ''.join(html_parts)


def main():
    print("Reading artifacts...")

    # Read overview
    overview = read_overview()

    # Read CSVs
    aliases, services = read_csv_with_aliases(SERVICES_CSV)
    deps = read_csv(DEPS_CSV)
    entries = read_csv(ENTRY_CSV)
    state = read_csv(STATE_CSV)
    findings = read_csv(FINDINGS_CSV)

    print(f"  Overview: {'yes' if overview else 'no'}")
    print(f"  Services: {len(services)}")
    print(f"  Dependencies: {len(deps)}")
    print(f"  Entry points: {len(entries)}")
    print(f"  State links: {len(state)}")
    print(f"  Findings: {len(findings)}")
    print(f"  Path aliases: {len(aliases)}")

    print("Generating report...")
    html = generate_html(services, deps, entries, state, findings, aliases, overview)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report written to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
