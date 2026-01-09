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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #F5F7FC;
  --surface: #FFFFFF;
  --text: #150A35;
  --text-muted: #6B7280;
  --border: #E5E7EB;
  --hover: #EAECF4;
  --accent: #A577FF;
  --accent-light: #C4A7FF;
  --accent-dark: #8B5CF6;
  --code-bg: #F0EEF7;
  --code-text: #150A35;
  --code-inline-bg: #F0EEF7;
  --code-inline-text: #150A35;
  --copy-btn-bg: #E5E7EB;
  --copy-btn-text: #6B7280;
}}

.dark {{
  --bg: #150A35;
  --surface: #1E1245;
  --text: #F5F7FC;
  --text-muted: #A1A1AA;
  --border: #2A1B5A;
  --hover: #2A1B5A;
  --code-bg: #0D0620;
  --code-text: #E4E4E7;
  --code-inline-bg: #0D0620;
  --code-inline-text: #E4E4E7;
  --copy-btn-bg: #2A1B5A;
  --copy-btn-text: #A1A1AA;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

html {{ scroll-behavior: smooth; }}

body {{
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  transition: background 0.3s, color 0.3s;
}}

.container {{
  margin-left: 180px;
  padding: 3rem 4rem;
}}

/* Header */
header {{
  text-align: center;
  margin-bottom: 3rem;
}}

header h1 {{
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}}

header .timestamp {{
  color: var(--text-muted);
  font-size: 0.875rem;
}}

/* Theme Toggle */
.theme-toggle {{
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--surface);
  border: 1px solid var(--border);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  transition: all 0.3s;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.theme-toggle:hover {{
  transform: scale(1.1);
  border-color: var(--accent);
}}

/* Stats */
.stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 3rem;
}}

.stat {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  transition: background 0.3s, border-color 0.3s, transform 0.2s, box-shadow 0.2s;
}}

.stat:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}

.stat-num {{
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--accent);
  line-height: 1;
}}

.stat-label {{
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.5rem;
}}

/* Sections */
section {{
  margin-bottom: 3rem;
}}

section h2 {{
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}}

.count-badge {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 0.5rem;
  background: var(--accent);
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 14px;
}}

section .desc {{
  color: var(--text-muted);
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}}

/* Cards */
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  transition: background 0.3s, border-color 0.3s, transform 0.2s;
}}

.card:hover {{
  border-color: var(--accent);
}}

.card h3 {{
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--accent);
}}

.card h4 {{
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}}

/* Priority Items */
a.priority-item {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  padding: 0.625rem 1rem;
  margin-bottom: 0.5rem;
  transition: background 0.3s, border-color 0.3s, transform 0.2s;
  text-decoration: none;
  cursor: pointer;
}}

a.priority-item:hover {{
  transform: translateX(3px);
  border-color: var(--accent);
}}

.priority-item strong {{
  color: var(--text);
  font-size: 0.875rem;
}}

.priority-item small {{
  color: var(--text-muted);
  font-size: 0.8rem;
  margin-left: auto;
}}

/* Tags */
.tag {{
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}}

.tag-http {{ background: #7C3AED; color: white; }}
.tag-queue {{ background: #A855F7; color: white; }}
.tag-sdk {{ background: #C084FC; color: white; }}
.tag-websocket {{ background: #6366F1; color: white; }}
.tag-grpc {{ background: #8B5CF6; color: white; }}
.tag-cron {{ background: #A78BFA; color: white; }}
.tag-file {{ background: #E9D5FF; color: #581C87; }}
.tag-stdin {{ background: #9333EA; color: white; }}
.tag-event {{ background: #7E22CE; color: white; }}
.tag-ipc {{ background: #581C87; color: white; }}
.tag-condition {{ background: var(--hover); color: var(--text); border: 1px solid var(--border); }}

/* Tables */
.table-wrap {{
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 1rem;
  background: var(--surface);
  transition: background 0.3s, border-color 0.3s;
}}

/* Table scrollbar */
.table-wrap::-webkit-scrollbar {{
  width: 8px;
  height: 8px;
}}

.table-wrap::-webkit-scrollbar-track {{
  background: var(--surface);
  border-radius: 4px;
}}

.table-wrap::-webkit-scrollbar-thumb {{
  background: var(--border);
  border-radius: 4px;
}}

.table-wrap::-webkit-scrollbar-thumb:hover {{
  background: var(--text-muted);
}}

.table-wrap::-webkit-scrollbar-corner {{
  background: var(--surface);
}}

table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  background: var(--surface);
}}

th, td {{
  padding: 0.875rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}}

th {{
  background: var(--surface);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.3s, color 0.2s;
}}

th:hover {{
  color: var(--accent);
}}

/* Legend box - condition type map */
.legend {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
  padding: 1.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 1.5rem;
}}

.legend-item {{
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--bg);
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}}

.legend-item:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}

.legend-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}}

.legend-term {{
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--accent);
}}

.legend-count {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 0.5rem;
  background: var(--accent);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 12px;
}}

.legend-def {{
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}}

tbody tr {{
  background: var(--surface);
  transition: background 0.2s;
}}

tbody tr:hover {{
  background: var(--hover);
}}

tbody tr:last-child td {{
  border-bottom: none;
}}

td code {{
  background: var(--code-inline-bg);
  color: var(--code-inline-text);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: 'Fira Code', monospace;
}}

/* Code blocks */
.code-wrapper {{
  position: relative;
  margin: 1rem 0;
  width: 100%;
}}

pre {{
  background: var(--code-bg);
  color: var(--code-text);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.25rem;
  padding-top: 2.5rem;
  overflow: auto;
  font-size: 0.75rem;
  font-family: 'Fira Code', monospace;
  line-height: 1.5;
  max-height: 500px;
  width: 100%;
}}

/* Scrollbar for code blocks */
pre::-webkit-scrollbar {{
  width: 8px;
  height: 8px;
}}

pre::-webkit-scrollbar-track {{
  background: var(--code-bg);
  border-radius: 4px;
}}

pre::-webkit-scrollbar-thumb {{
  background: var(--border);
  border-radius: 4px;
}}

pre::-webkit-scrollbar-thumb:hover {{
  background: var(--text-muted);
}}

pre::-webkit-scrollbar-corner {{
  background: var(--code-bg);
}}

.copy-btn {{
  position: absolute;
  top: 0.75rem;
  right: 1.25rem;
  background: var(--copy-btn-bg);
  border: none;
  color: var(--copy-btn-text);
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.7rem;
  font-family: inherit;
  transition: all 0.2s;
  z-index: 10;
}}

.copy-btn:hover {{
  background: var(--accent);
  color: white;
}}

/* Links */
a {{
  color: var(--accent);
  text-decoration: none;
}}

a:hover {{
  color: var(--accent-light);
}}

/* Entry detail */
.entry-meta {{
  display: grid;
  gap: 0.5rem;
  margin-bottom: 1rem;
}}

.entry-meta p {{
  font-size: 0.875rem;
  margin: 0;
}}

.entry-meta strong {{
  color: var(--text-muted);
  font-weight: 500;
  margin-right: 0.5rem;
}}

.entry-meta ul {{
  list-style: none;
  margin: 0.25rem 0 0 0;
  padding: 0;
}}

.entry-meta li {{
  font-size: 0.8rem;
  color: var(--text-muted);
  padding: 0.125rem 0;
}}

/* Lead/Finding card */
.lead-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 1rem;
  overflow: hidden;
  transition: background 0.3s, border-color 0.3s;
}}

.lead-card:hover {{
  border-color: var(--accent);
}}

.lead-header {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--hover);
  border-bottom: 1px solid var(--border);
}}

.lead-header .tag {{
  flex-shrink: 0;
}}

.lead-id {{
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text);
}}

.lead-body {{
  padding: 1.25rem;
}}

.lead-description {{
  font-size: 0.9rem;
  color: var(--text);
  margin-bottom: 1rem;
  line-height: 1.5;
}}

.lead-details {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}}

.lead-detail {{
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: var(--bg);
  border-radius: 8px;
}}

.lead-detail-label {{
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 500;
}}

.lead-detail-value {{
  font-size: 0.85rem;
  color: var(--text);
  word-break: break-word;
}}

.lead-detail-value code {{
  background: var(--code-inline-bg);
  color: var(--code-inline-text);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: 'Fira Code', monospace;
}}

/* Finding meta (bottom row) */
.finding-meta {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}}

.finding-meta-item {{
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  text-align: center;
  padding: 0.5rem;
}}

.finding-meta-label {{
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 500;
}}

.finding-meta-value {{
  font-size: 0.8rem;
  color: var(--text);
}}

/* Nav */
nav {{
  position: fixed;
  top: 0;
  left: 0;
  width: 180px;
  height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 2rem 1rem;
  z-index: 100;
  transition: background 0.3s, border-color 0.3s;
  overflow-y: auto;
}}

nav ul {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}}

nav a {{
  display: block;
  padding: 0.625rem 0.875rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-muted);
  border-radius: 6px;
  transition: all 0.2s;
}}

nav a:hover {{
  color: var(--accent);
  background: var(--hover);
}}

nav a.active {{
  background: var(--accent);
  color: white;
}}


/* Footer */
footer {{
  text-align: center;
  padding: 2rem 0;
  color: var(--text-muted);
  font-size: 0.8rem;
  border-top: 1px solid var(--border);
}}

/* Responsive */
@media (max-width: 768px) {{
  nav {{ display: none; }}
  .container {{
    margin-left: 0;
    padding: 1.5rem 1rem;
  }}
  header h1 {{ font-size: 1.75rem; }}
}}

/* Overview card */
.overview-card {{
  border-left: 4px solid var(--accent);
}}

.overview-card h3 {{
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}}

.overview-card h3:first-child {{
  margin-top: 0;
}}

.overview-card h4 {{
  margin-top: 1rem;
  font-size: 0.95rem;
}}

.overview-card p {{
  margin: 0.5rem 0;
  color: var(--text-muted);
}}

.overview-card ul {{
  margin: 0.5rem 0 0.5rem 1.5rem;
}}

.overview-card li {{
  margin: 0.25rem 0;
  color: var(--text-muted);
}}

.overview-card pre {{
  width: fit-content;
  margin: 1rem auto;
  max-width: 100%;
}}
</style>
</head>
<body>

<button class="theme-toggle" onclick="toggleTheme()">🌙</button>

<nav>
  <ul>
    <li><a href="#app-overview">Overview</a></li>
    <li><a href="#executive">Priority</a></li>
    <li><a href="#attack-surface">Attack Surface</a></li>
    <li><a href="#entries">Entry Points</a></li>
    <li><a href="#findings">Leads</a></li>
    <li><a href="#dataflow">Data Flows</a></li>
    <li><a href="#deps">Dependencies</a></li>
  </ul>
</nav>

<div class="container">

<header>
  <h1>Security Review Report</h1>
  <p class="timestamp">Generated {timestamp}</p>
</header>


<div class="stats">
  <div class="stat"><div class="stat-num">{len(svc_names)}</div><div class="stat-label">Services</div></div>
  <div class="stat"><div class="stat-num">{len(entries)}</div><div class="stat-label">Entry Points</div></div>
  {'<div class="stat"><div class="stat-num">' + str(queue_count) + '</div><div class="stat-label">Queue Consumers</div></div>' if queue_count > 0 else ''}
  <div class="stat"><div class="stat-num">{len(state)}</div><div class="stat-label">Data Flows</div></div>
  <div class="stat"><div class="stat-num">{len(findings)}</div><div class="stat-label">Leads</div></div>
</div>

''']

    # Application Overview (from stage0)
    if overview:
        overview_html = md_to_html(overview)
        html_parts.append(f'''
<section id="app-overview">
<h2>Application Overview</h2>
<div class="card overview-card">
{overview_html}
</div>
</section>
''')

    html_parts.append(f'''
<section id="executive">
<h2>What to Look at First <span class="count-badge">{len(priority_findings)}</span></h2>
<p class="desc">Conditions involving command execution, file operations, or external calls with user input.</p>
''')

    if priority_findings:
        for f in priority_findings[:10]:
            html_parts.append(f'''<a href="#finding-{slugify(f.get('id', ''))}" class="priority-item searchable" data-search="{esc(f.get('id', ''))} {esc(f.get('condition_type', ''))}">
<strong>{esc(f.get('id', ''))}</strong><span class="tag tag-condition">{esc(f.get('condition_type', ''))}</span><small>{esc(f.get('svc_name', ''))} → {esc(f.get('entry_point', ''))}</small>
</a>
''')
    else:
        html_parts.append('<p class="desc">No high-priority conditions identified.</p>')

    html_parts.append('</section>')

    # Attack Surface Navigator
    html_parts.append(f'''
<section id="attack-surface">
<h2>Attack Surface <span class="count-badge">{len(entries)}</span></h2>
<p class="desc">All places where external input enters the application.</p>
''')

    for svc in svc_names:
        svc_entries = entries_by_svc.get(svc, [])
        html_parts.append(f'''
<div class="card">
<h3>{esc(svc)}</h3>
<div class="table-wrap">
<table class="sortable">
<thead>
<tr><th>Type</th><th>Route</th><th>Method</th><th>Handler</th><th>Params</th></tr>
</thead>
<tbody>
''')
        for e in svc_entries:
            entry_id = slugify(f"{svc}-{e.get('route', '')}-{e.get('method', '')}")
            tag_class = f"tag-{e.get('entry_type', 'http').lower()}"
            html_parts.append(f'''<tr class="searchable" data-search="{esc(e.get('route', ''))} {esc(e.get('handler_func', ''))}">
<td><span class="tag {tag_class}">{esc(e.get('entry_type', ''))}</span></td>
<td><a href="#entry-{entry_id}"><code>{esc(e.get('route', ''))}</code></a></td>
<td>{esc(e.get('method', ''))}</td>
<td><code>{esc(e.get('handler_func', ''))}</code></td>
<td>{esc(e.get('param_sources', ''))}</td>
</tr>
''')
        html_parts.append('</tbody></table></div></div>')

    html_parts.append('</section>')

    # Entry Point Details
    html_parts.append(f'''
<section id="entries">
<h2>Entry Point Details <span class="count-badge">{len(entries)}</span></h2>
<p class="desc">Handler functions, parameters, and code snippets.</p>
''')

    for svc in svc_names:
        for e in entries_by_svc.get(svc, []):
            entry_id = slugify(f"{svc}-{e.get('route', '')}-{e.get('method', '')}")
            handler_file = resolve_path(e.get('handler_file', ''), aliases)
            handler_func = e.get('handler_func', '')

            related = [f for f in findings_by_svc.get(svc, [])
                      if e.get('route', '') in f.get('entry_point', '')]

            related_state = [s for s in state_by_svc.get(svc, [])
                           if s.get('src_func', '') == handler_func]

            snippet, snippet_err = extract_snippet(handler_file, handler_func)

            html_parts.append(f'''
<div class="card searchable" id="entry-{entry_id}" data-search="{esc(e.get('route', ''))} {esc(handler_func)}">
<h4><span class="tag tag-{e.get('entry_type', 'http').lower()}">{esc(e.get('entry_type', ''))}</span> {esc(e.get('method', ''))} {esc(e.get('route', ''))}</h4>
<div class="entry-meta">
<p><strong>Handler:</strong> <code>{esc(handler_func)}</code></p>
<p><strong>File:</strong> {esc(e.get('handler_file', ''))}</p>
<p><strong>Parameters:</strong> {esc(e.get('param_sources', 'none'))}</p>
<p><strong>Calls:</strong> {esc(e.get('called_funcs', 'none'))}</p>
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

            html_parts.append('</div>')

            if snippet:
                html_parts.append(f'''
<div class="code-wrapper"><button class="copy-btn" onclick="copyCode(this)">Copy</button><pre><code>{esc(snippet)}</code></pre></div>
''')

            html_parts.append('</div>')

    html_parts.append('</section>')

    # Leads Catalog - count by condition type
    condition_counts = defaultdict(int)
    for f in findings:
        ctype = f.get('condition_type', 'UNKNOWN')
        condition_counts[ctype] += 1

    # Condition type descriptions
    condition_descriptions = {
        'MISSING_VALIDATION': 'User input without sanitization',
        'TRUST_BOUNDARY_CROSSING': 'Data crosses trust zones',
        'DANGEROUS_PRIMITIVE': 'eval(), SQL builders, deserializers',
        'STATE_MUTATION': 'DB writes, cache, session changes',
        'CONFIG_DEPENDENT': 'Behavior varies by env/config',
        'EXTERNAL_CALL_INPUT': 'User data to external APIs',
        'FILE_INTERACTION': 'File ops from user input',
        'SUBPROCESS_EXEC': 'Shell commands, processes',
        'AUTH_BYPASS': 'Authentication logic flaws',
        'AUTHZ_BYPASS': 'Missing permission checks, IDOR',
        'SESSION_HANDLING': 'Weak sessions, fixation',
        'SSRF': 'Server fetches user-supplied URL',
        'OPEN_REDIRECT': 'Redirect to user-supplied URL',
        'PATH_TRAVERSAL': 'Directory traversal (../)',
        'TEMPLATE_INJECTION': 'User input in templates',
        'XML_PARSING': 'XXE in XML parsers',
        'MASS_ASSIGNMENT': 'Binding without allowlist',
        'HARDCODED_SECRET': 'Keys, passwords in code',
        'WEAK_CRYPTO': 'MD5, SHA1, weak keys',
        'SENSITIVE_LOGGING': 'PII, creds in logs',
        'INFO_DISCLOSURE': 'Stack traces, debug exposed',
        'RACE_CONDITION': 'TOCTOU, concurrent access',
    }

    # Build legend with only existing types and counts
    legend_items = []
    for ctype, count in sorted(condition_counts.items(), key=lambda x: -x[1]):
        label = ctype.replace('_', ' ').title()
        desc = condition_descriptions.get(ctype, '')
        legend_items.append(f'''<div class="legend-item">
<div class="legend-header"><span class="legend-term">{esc(label)}</span><span class="legend-count">{count}</span></div>
<span class="legend-def">{esc(desc)}</span>
</div>''')

    html_parts.append(f'''
<section id="findings">
<h2>Leads <span class="count-badge">{len(findings)}</span></h2>
<p class="desc">Conditions worth investigating. These are NOT confirmed vulnerabilities.</p>
<div class="legend">
{''.join(legend_items)}
</div>
''')

    for svc in svc_names:
        svc_findings = findings_by_svc.get(svc, [])
        if not svc_findings:
            continue

        html_parts.append(f'<h3 style="margin: 1.5rem 0 1rem; color: var(--accent);">{esc(svc)}</h3>')

        for f in svc_findings:
            fid = f.get('id', '')
            html_parts.append(f'''
<div class="lead-card searchable" id="finding-{slugify(fid)}" data-search="{esc(fid)} {esc(f.get('condition_type', ''))} {esc(f.get('description', ''))}">
<div class="lead-header">
<span class="lead-id">{esc(fid)}</span>
<span class="tag tag-condition">{esc(f.get('condition_type', ''))}</span>
</div>
<div class="lead-body">
<p class="lead-description">{esc(f.get('description', ''))}</p>
<div class="lead-details">
<div class="lead-detail">
<span class="lead-detail-label">Where it happens</span>
<span class="lead-detail-value"><code>{esc(f.get('entry_point', ''))}</code></span>
</div>
<div class="lead-detail">
<span class="lead-detail-label">When it triggers</span>
<span class="lead-detail-value">{esc(f.get('preconditions', 'none'))}</span>
</div>
</div>
<div class="finding-meta">
<div class="finding-meta-item"><span class="finding-meta-label">Data Affected</span><span class="finding-meta-value">{esc(f.get('state_touched', 'none'))}</span></div>
<div class="finding-meta-item"><span class="finding-meta-label">Multiple Services</span><span class="finding-meta-value">{esc(f.get('cross_svc', 'no'))}</span></div>
<div class="finding-meta-item"><span class="finding-meta-label">Libraries Involved</span><span class="finding-meta-value">{esc(f.get('ext_dep', 'no'))}</span></div>
</div>
</div>
</div>
''')

    html_parts.append('</section>')

    # Data Flows
    html_parts.append(f'''
<section id="dataflow">
<h2>Data Flows <span class="count-badge">{len(state)}</span></h2>
<p class="desc">How data moves through the application. Database operations, API calls, state mutations.</p>
<div class="legend">
<div class="legend-item"><span class="legend-term">Service</span><span class="legend-def">Which microservice or module</span></div>
<div class="legend-item"><span class="legend-term">Type</span><span class="legend-def">Resource category (DB, API, FILE, CACHE)</span></div>
<div class="legend-item"><span class="legend-term">Identifier</span><span class="legend-def">Table name, endpoint, or file path</span></div>
<div class="legend-item"><span class="legend-term">Op</span><span class="legend-def">Operation (READ, WRITE, DELETE, CALL)</span></div>
<div class="legend-item"><span class="legend-term">Source</span><span class="legend-def">Function initiating the operation</span></div>
<div class="legend-item"><span class="legend-term">Target</span><span class="legend-def">Destination function or resource</span></div>
</div>
<div class="table-wrap">
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

    html_parts.append('</tbody></table></div></section>')

    # Dependencies
    html_parts.append(f'''
<section id="deps">
<h2>Dependencies <span class="count-badge">{len(deps)}</span></h2>
<p class="desc">Third-party packages. Check for known CVEs.</p>
''')

    risky_keywords = ['exec', 'shell', 'sql', 'orm', 'serialize', 'pickle', 'yaml', 'template', 'crypto', 'jwt', 'http', 'request', 'socket']

    for svc in svc_names:
        svc_deps = deps_by_svc.get(svc, [])
        if not svc_deps:
            continue

        html_parts.append(f'''
<div class="card">
<h3>{esc(svc)}</h3>
<div class="table-wrap">
<table>
<thead><tr><th>Dependency</th><th>Version</th><th>Scope</th><th>Notes</th></tr></thead>
<tbody>
''')
        for d in svc_deps:
            dep_name = d.get('dep_name', '').lower()
            notes = [kw for kw in risky_keywords if kw in dep_name]
            note_str = ', '.join(notes) if notes else '-'

            html_parts.append(f'''<tr>
<td><code>{esc(d.get('dep_name', ''))}</code></td>
<td>{esc(d.get('version', ''))}</td>
<td>{esc(d.get('scope', ''))}</td>
<td>{esc(note_str)}</td>
</tr>
''')
        html_parts.append('</tbody></table></div></div>')

    html_parts.append('</section>')

    # Footer and scripts
    html_parts.append('''
<footer>
<p>All findings are leads requiring human validation. No severity assigned by design.</p>
</footer>

</div>

<script>
function toggleTheme() {
  document.body.classList.toggle('dark');
  const btn = document.querySelector('.theme-toggle');
  btn.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
}

// Load saved theme
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark');
  document.querySelector('.theme-toggle').textContent = '☀️';
}


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

// Nav highlighting
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('nav a');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    if (window.scrollY >= section.offsetTop - 200) {
      current = section.id;
    }
  });
  navLinks.forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === '#' + current);
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
