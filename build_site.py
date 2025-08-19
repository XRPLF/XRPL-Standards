#!/usr/bin/env python3
"""
Build script for XLS Standards static site generator.
Converts markdown XLS files to HTML and creates an index page.
"""

import os
import re
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
import markdown
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

@dataclass
class XLSDocument:
    """Represents an XLS document with metadata."""
    number: str
    title: str
    type: str
    description: str
    author: str
    folder: str
    filename: str
    status: str  # draft, candidate, released, etc.
    created_date: str = ""  # Creation date
    
    def to_dict(self):
        return asdict(self)

def extract_xls_metadata(content: str, folder_name: str) -> Optional[XLSDocument]:
    """Extract metadata from XLS markdown content."""
    
    # Initialize metadata with defaults
    metadata = {
        'title': 'Unknown Title',
        'type': 'unknown',
        'description': '',
        'author': 'Unknown Author',
        'created': ''
    }
    
    # Parse HTML pre block for metadata
    soup = BeautifulSoup(content, 'html.parser')
    pre_block = soup.find('pre')
    
    if pre_block:
        pre_text = pre_block.get_text()
        
        # Extract metadata using various patterns
        patterns = {
            'title': [
                r'title:\s*<b>(.*?)</b>',
                r'Title:\s*<b>(.*?)</b>',
                r'title:\s*(.*?)(?:\n|$)',
                r'Title:\s*(.*?)(?:\n|$)'
            ],
            'type': [
                r'type:\s*(.*?)(?:\n|$)',
                r'Type:\s*(.*?)(?:\n|$)'
            ],
            'description': [
                r'description:\s*(.*?)(?:\n|$)',
                r'Description:\s*(.*?)(?:\n|$)'
            ],
            'author': [
                r'author:\s*(.*?)(?:\n|$)',
                r'Author:\s*(.*?)(?:\n|$)'
            ],
            'created': [
                r'created:\s*(.*?)(?:\n|$)',
                r'Created:\s*(.*?)(?:\n|$)',
                r'date:\s*(.*?)(?:\n|$)',
                r'Date:\s*(.*?)(?:\n|$)'
            ]
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, pre_text, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    # Clean HTML tags from value
                    value = BeautifulSoup(value, 'html.parser').get_text()
                    metadata[key] = value
                    break
    else:
        # Try to extract from first heading and content
        lines = content.split('\n')
        first_line = lines[0].strip() if lines else ''
        
        # Try to extract title from first heading
        heading_match = re.match(r'^#\s*(.*)', first_line)
        if heading_match:
            metadata['title'] = heading_match.group(1).strip()
            
        # For files without pre blocks, try to infer some info
        print(f"Warning: No metadata pre block found in {folder_name}, using fallback extraction")
    
    # Extract XLS number from folder name
    xls_match = re.match(r'XLS-(\d+)([d]?)', folder_name)
    if xls_match:
        number = xls_match.group(1)
        is_draft = xls_match.group(2) == 'd'
        status = 'draft' if is_draft else 'released'
    else:
        number = '000'
        status = 'unknown'
    
    # Determine status from type field if available
    if 'draft' in metadata['type'].lower():
        status = 'draft'
    elif 'released' in metadata['type'].lower():
        status = 'released'
    elif 'candidate' in metadata['type'].lower():
        status = 'candidate'
    
    return XLSDocument(
        number=number,
        title=metadata['title'],
        type=metadata['type'],
        description=metadata['description'],
        author=metadata['author'],
        folder=folder_name,
        filename='README.md',
        status=status,
        created_date=metadata['created']
    )

def convert_markdown_to_html(content: str) -> str:
    """Convert markdown content to HTML."""
    md = markdown.Markdown(
        extensions=[
            'extra',
            'codehilite',
            'toc',
            'tables'
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight'
            },
            'toc': {
                'permalink': True
            }
        }
    )
    return md.convert(content)

def build_site():
    """Main function to build the static site."""
    
    # Setup directories
    root_dir = Path('.')
    site_dir = root_dir / '_site'
    
    # Set base URL for GitHub Pages (can be overridden with env var)
    base_url = os.environ.get('GITHUB_PAGES_BASE_URL', '/XRPL-Standards')
    
    # Clean and create site directory
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir()
    
    # Create subdirectories
    (site_dir / 'xls').mkdir()
    (site_dir / 'assets').mkdir()
    
    # Setup Jinja2 environment
    template_dir = root_dir / 'templates'
    if not template_dir.exists():
        template_dir.mkdir()
        
    # Create templates if they don't exist
    create_templates(template_dir, base_url)
    
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Find all XLS documents
    xls_docs = []
    xls_folders = [d for d in root_dir.iterdir() 
                   if d.is_dir() and d.name.startswith('XLS-')]
    
    for folder in xls_folders:
        readme_path = folder / 'README.md'
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                doc = extract_xls_metadata(content, folder.name)
                if doc:
                    xls_docs.append(doc)
                    
                    # Convert to HTML
                    html_content = convert_markdown_to_html(content)
                    
                    # Render XLS page
                    xls_template = env.get_template('xls.html')
                    rendered_html = xls_template.render(
                        doc=doc,
                        content=html_content,
                        title=f"XLS-{doc.number}: {doc.title}",
                        base_url=base_url
                    )
                    
                    # Write XLS HTML file
                    output_path = site_dir / 'xls' / f"{folder.name}.html"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(rendered_html)
                    
                    print(f"Generated: {output_path}")
                    
            except Exception as e:
                print(f"Error processing {folder.name}: {e}")
    
    # Sort documents by number
    xls_docs.sort(key=lambda x: int(x.number))
    
    # Group by status
    drafts = [doc for doc in xls_docs if doc.status == 'draft']
    candidates = [doc for doc in xls_docs if doc.status == 'candidate']
    released = [doc for doc in xls_docs if doc.status == 'released']
    others = [doc for doc in xls_docs if doc.status not in ['draft', 'candidate', 'released']]
    
    # Generate index page
    index_template = env.get_template('index.html')
    index_html = index_template.render(
        title="XRP Ledger Standards (XLS)",
        total_count=len(xls_docs),
        drafts=drafts,
        candidates=candidates,
        released=released,
        others=others,
        base_url=base_url
    )
    
    # Write index file
    with open(site_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Create CSS file
    create_css(site_dir / 'assets', base_url)
    
    print(f"Site built successfully! Generated {len(xls_docs)} XLS documents.")
    print(f"- Released: {len(released)}")
    print(f"- Candidates: {len(candidates)}")
    print(f"- Drafts: {len(drafts)}")
    print(f"- Others: {len(others)}")

def create_templates(template_dir: Path, base_url: str = "/XRPL-Standards"):
    """Create HTML templates."""
    
    # Base template
    base_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{% block title %}}{{{{ title }}}}{{% endblock %}}</title>
    <link rel="stylesheet" href="{base_url}/assets/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1><a href="{base_url}/">XRP Ledger Standards</a></h1>
            <nav>
                <a href="{base_url}/">All Standards</a>
                <a href="https://github.com/XRPLF/XRPL-Standards">GitHub</a>
            </nav>
        </div>
    </header>
    
    <main class="container">
        {{% block content %}}{{% endblock %}}
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2024 XRP Ledger Foundation. Licensed under <a href="https://github.com/XRPLF/XRPL-Standards/blob/master/LICENSE">Apache License 2.0</a>.</p>
        </div>
    </footer>
</body>
</html>"""
    
    # Index template
    index_template = f"""{{% extends "base.html" %}}

{{% block content %}}
<div class="intro">
    <h2>XRP Ledger Standards (XLS)</h2>
    <p>XRP Ledger Standards (XLSs) describe standards and specifications relating to the XRP Ledger ecosystem that help achieve interoperability, compatibility, and excellent user experience.</p>
    <p>Total standards: <strong>{{{{ total_count }}}}</strong></p>
</div>

<div class="standards-table-container">
    <table class="standards-table">
        <thead>
            <tr>
                <th>Number</th>
                <th>Title</th>
                <th>Author</th>
                <th>Type</th>
                <th>Status</th>
                <th>Created</th>
            </tr>
        </thead>
        <tbody>
            {{% for doc in released %}}
            <tr class="status-released">
                <td class="number-col" data-label="Number">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html" class="xls-link">XLS-{{{{ doc.number }}}}</a>
                </td>
                <td class="title-col" data-label="Title">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html">{{{{ doc.title }}}}</a>
                </td>
                <td class="author-col" data-label="Author">{{{{ doc.author }}}}</td>
                <td class="type-col" data-label="Type">{{{{ doc.type }}}}</td>
                <td class="status-col" data-label="Status">
                    <span class="status-badge released">Released</span>
                </td>
                <td class="date-col" data-label="Created">{{{{ doc.created_date or '-' }}}}</td>
            </tr>
            {{% endfor %}}
            
            {{% for doc in candidates %}}
            <tr class="status-candidate">
                <td class="number-col" data-label="Number">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html" class="xls-link">XLS-{{{{ doc.number }}}}</a>
                </td>
                <td class="title-col" data-label="Title">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html">{{{{ doc.title }}}}</a>
                </td>
                <td class="author-col" data-label="Author">{{{{ doc.author }}}}</td>
                <td class="type-col" data-label="Type">{{{{ doc.type }}}}</td>
                <td class="status-col" data-label="Status">
                    <span class="status-badge candidate">Candidate</span>
                </td>
                <td class="date-col" data-label="Created">{{{{ doc.created_date or '-' }}}}</td>
            </tr>
            {{% endfor %}}
            
            {{% for doc in drafts %}}
            <tr class="status-draft">
                <td class="number-col" data-label="Number">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html" class="xls-link">XLS-{{{{ doc.number }}}}</a>
                </td>
                <td class="title-col" data-label="Title">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html">{{{{ doc.title }}}}</a>
                </td>
                <td class="author-col" data-label="Author">{{{{ doc.author }}}}</td>
                <td class="type-col" data-label="Type">{{{{ doc.type }}}}</td>
                <td class="status-col" data-label="Status">
                    <span class="status-badge draft">Draft</span>
                </td>
                <td class="date-col" data-label="Created">{{{{ doc.created_date or '-' }}}}</td>
            </tr>
            {{% endfor %}}
            
            {{% for doc in others %}}
            <tr class="status-other">
                <td class="number-col" data-label="Number">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html" class="xls-link">XLS-{{{{ doc.number }}}}</a>
                </td>
                <td class="title-col" data-label="Title">
                    <a href="{base_url}/xls/{{{{ doc.folder }}}}.html">{{{{ doc.title }}}}</a>
                </td>
                <td class="author-col" data-label="Author">{{{{ doc.author }}}}</td>
                <td class="type-col" data-label="Type">{{{{ doc.type }}}}</td>
                <td class="status-col" data-label="Status">
                    <span class="status-badge other">{{{{ doc.status.title() }}}}</span>
                </td>
                <td class="date-col" data-label="Created">{{{{ doc.created_date or '-' }}}}</td>
            </tr>
            {{% endfor %}}
        </tbody>
    </table>
</div>
{{% endblock %}}"""
    
    # XLS document template
    xls_template = f"""{{% extends "base.html" %}}

{{% block content %}}
<div class="xls-document">
    <div class="xls-meta">
        <div class="xls-number-large">XLS-{{{{ doc.number }}}}</div>
        <div class="xls-status-badge {{{{ doc.status }}}}">{{{{ doc.status.title() }}}}</div>
    </div>
    
    <div class="document-content">
        {{{{ content|safe }}}}
    </div>
    
    <div class="document-nav">
        <a href="{base_url}/">&larr; Back to All Standards</a>
        <a href="https://github.com/XRPLF/XRPL-Standards/tree/master/{{{{ doc.folder }}}}">View on GitHub</a>
    </div>
</div>
{{% endblock %}}"""
    
    # Write templates
    with open(template_dir / 'base.html', 'w') as f:
        f.write(base_template)
    
    with open(template_dir / 'index.html', 'w') as f:
        f.write(index_template)
    
    with open(template_dir / 'xls.html', 'w') as f:
        f.write(xls_template)

def create_css(assets_dir: Path, base_url: str = "/XRPL-Standards"):
    """Create CSS styles."""
    
    css_content = """/* XLS Standards Site Styles */

/* Reset and base styles */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.5;
    color: #24292f;
    background-color: #ffffff;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
}

/* Header */
header {
    background: #ffffff;
    border-bottom: 1px solid #d1d9e0;
    padding: 16px 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

header .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

header h1 {
    font-size: 20px;
    font-weight: 600;
}

header h1 a {
    text-decoration: none;
    color: #0969da;
}

header h1 a:hover {
    text-decoration: underline;
}

header nav a {
    margin-left: 24px;
    text-decoration: none;
    color: #656d76;
    font-weight: 500;
}

header nav a:hover {
    color: #0969da;
}

/* Main content */
main {
    padding: 32px 0 64px;
    min-height: calc(100vh - 120px);
}

/* Introduction section */
.intro {
    text-align: center;
    margin-bottom: 48px;
    padding: 48px 32px;
    background: #f6f8fa;
    border-radius: 12px;
    border: 1px solid #d1d9e0;
}

.intro h2 {
    font-size: 32px;
    font-weight: 600;
    color: #24292f;
    margin-bottom: 16px;
}

.intro p {
    font-size: 16px;
    color: #656d76;
    margin-bottom: 8px;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}

/* Standards table */
.standards-table-container {
    background: #ffffff;
    border: 1px solid #d1d9e0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.standards-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.standards-table thead {
    background: #f6f8fa;
    border-bottom: 1px solid #d1d9e0;
}

.standards-table th {
    padding: 16px 12px;
    text-align: left;
    font-weight: 600;
    color: #24292f;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-right: 1px solid #d1d9e0;
}

.standards-table th:last-child {
    border-right: none;
}

.standards-table td {
    padding: 12px;
    border-bottom: 1px solid #eaeef2;
    border-right: 1px solid #eaeef2;
    vertical-align: top;
}

.standards-table td:last-child {
    border-right: none;
}

.standards-table tbody tr:hover {
    background-color: #f6f8fa;
}

.standards-table tbody tr:last-child td {
    border-bottom: none;
}

/* Column styling */
.number-col {
    width: 120px;
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, Courier, monospace;
}

.title-col {
    width: auto;
    min-width: 300px;
}

.author-col {
    width: 200px;
    color: #656d76;
}

.type-col {
    width: 150px;
    color: #656d76;
    font-size: 13px;
}

.status-col {
    width: 120px;
    text-align: center;
}

.date-col {
    width: 120px;
    color: #656d76;
    font-size: 13px;
}

/* Links */
.xls-link {
    font-weight: 600;
    color: #0969da;
    text-decoration: none;
}

.xls-link:hover {
    text-decoration: underline;
}

.title-col a {
    color: #0969da;
    text-decoration: none;
    font-weight: 500;
    display: block;
    word-wrap: break-word;
}

.title-col a:hover {
    text-decoration: underline;
}

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    text-align: center;
    min-width: 70px;
}

.status-badge.released {
    background-color: #dcfdf7;
    color: #065f46;
    border: 1px solid #a7f3d0;
}

.status-badge.candidate {
    background-color: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
}

.status-badge.draft {
    background-color: #e0e7ff;
    color: #3730a3;
    border: 1px solid #c7d2fe;
}

.status-badge.other {
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
}

/* Row status styling (subtle left border) */
.status-released {
    border-left: 3px solid #10b981;
}

.status-candidate {
    border-left: 3px solid #f59e0b;
}

.status-draft {
    border-left: 3px solid #6366f1;
}

.status-other {
    border-left: 3px solid #6b7280;
}

/* XLS document page */
.xls-document {
    background: #ffffff;
    border: 1px solid #d1d9e0;
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.xls-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    padding-bottom: 24px;
    border-bottom: 2px solid #eaeef2;
}

.xls-number-large {
    font-size: 28px;
    font-weight: 700;
    color: #0969da;
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, Courier, monospace;
}

.xls-status-badge {
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.xls-status-badge.released {
    background-color: #dcfdf7;
    color: #065f46;
    border: 1px solid #a7f3d0;
}

.xls-status-badge.candidate {
    background-color: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
}

.xls-status-badge.draft {
    background-color: #e0e7ff;
    color: #3730a3;
    border: 1px solid #c7d2fe;
}

.xls-status-badge.other {
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
}

/* Document content styling */
.document-content {
    max-width: none;
    line-height: 1.6;
}

.document-content h1,
.document-content h2,
.document-content h3,
.document-content h4,
.document-content h5,
.document-content h6 {
    margin-top: 32px;
    margin-bottom: 16px;
    color: #24292f;
    font-weight: 600;
}

.document-content h1 {
    font-size: 28px;
    border-bottom: 1px solid #eaeef2;
    padding-bottom: 16px;
}

.document-content h2 {
    font-size: 24px;
    border-bottom: 1px solid #eaeef2;
    padding-bottom: 8px;
}

.document-content h3 {
    font-size: 20px;
}

.document-content p {
    margin-bottom: 16px;
    color: #24292f;
}

.document-content pre {
    background: #f6f8fa;
    border: 1px solid #d1d9e0;
    border-radius: 6px;
    padding: 16px;
    overflow-x: auto;
    margin: 16px 0;
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 13px;
    line-height: 1.4;
}

.document-content code {
    background: #f6f8fa;
    border: 1px solid #d1d9e0;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 13px;
}

.document-content pre code {
    background: none;
    border: none;
    padding: 0;
}

.document-content blockquote {
    border-left: 4px solid #0969da;
    margin: 16px 0;
    padding: 8px 16px;
    color: #656d76;
    background: #f6f8fa;
}

.document-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    border: 1px solid #d1d9e0;
    border-radius: 6px;
    overflow: hidden;
}

.document-content th,
.document-content td {
    border-bottom: 1px solid #eaeef2;
    border-right: 1px solid #eaeef2;
    padding: 12px;
    text-align: left;
}

.document-content th:last-child,
.document-content td:last-child {
    border-right: none;
}

.document-content th {
    background: #f6f8fa;
    font-weight: 600;
}

.document-content tbody tr:last-child td {
    border-bottom: none;
}

/* Document navigation */
.document-nav {
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid #eaeef2;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.document-nav a {
    color: #0969da;
    text-decoration: none;
    font-weight: 500;
    padding: 8px 16px;
    border-radius: 6px;
    border: 1px solid #d1d9e0;
    transition: all 0.2s;
}

.document-nav a:hover {
    background: #f6f8fa;
    text-decoration: none;
}

/* Footer */
footer {
    background: #f6f8fa;
    border-top: 1px solid #d1d9e0;
    padding: 24px 0;
    text-align: center;
    color: #656d76;
    font-size: 14px;
}

footer a {
    color: #0969da;
    text-decoration: none;
}

footer a:hover {
    text-decoration: underline;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 0 16px;
    }
    
    header .container {
        flex-direction: column;
        gap: 16px;
        text-align: center;
    }
    
    header nav a {
        margin: 0 12px;
    }
    
    .intro {
        padding: 32px 24px;
    }
    
    .intro h2 {
        font-size: 24px;
    }
    
    .xls-meta {
        flex-direction: column;
        align-items: flex-start;
        gap: 16px;
    }
    
    .document-nav {
        flex-direction: column;
        gap: 12px;
    }
    
    .document-nav a {
        text-align: center;
        width: 100%;
    }
    
    /* Make table responsive */
    .standards-table-container {
        overflow-x: auto;
    }
    
    .standards-table {
        min-width: 800px;
    }
    
    /* Stack table cells on very small screens */
    @media (max-width: 600px) {
        .standards-table thead {
            display: none;
        }
        
        .standards-table,
        .standards-table tbody,
        .standards-table tr,
        .standards-table td {
            display: block;
        }
        
        .standards-table {
            min-width: auto;
        }
        
        .standards-table tr {
            border: 1px solid #d1d9e0;
            margin-bottom: 16px;
            border-radius: 8px;
            padding: 16px;
            background: #ffffff;
        }
        
        .standards-table td {
            border: none;
            padding: 8px 0;
            display: flex;
            justify-content: space-between;
        }
        
        .standards-table td:before {
            content: attr(data-label);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            color: #656d76;
            margin-right: 16px;
        }
    }
}"""
    
    with open(assets_dir / 'style.css', 'w') as f:
        f.write(css_content)

if __name__ == "__main__":
    build_site()