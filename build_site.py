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
    
    def to_dict(self):
        return asdict(self)

def extract_xls_metadata(content: str, folder_name: str) -> Optional[XLSDocument]:
    """Extract metadata from XLS markdown content."""
    
    # Initialize metadata with defaults
    metadata = {
        'title': 'Unknown Title',
        'type': 'unknown',
        'description': '',
        'author': 'Unknown Author'
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
        status=status
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
    create_templates(template_dir)
    
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
                        title=f"XLS-{doc.number}: {doc.title}"
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
        others=others
    )
    
    # Write index file
    with open(site_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Create CSS file
    create_css(site_dir / 'assets')
    
    print(f"Site built successfully! Generated {len(xls_docs)} XLS documents.")
    print(f"- Released: {len(released)}")
    print(f"- Candidates: {len(candidates)}")
    print(f"- Drafts: {len(drafts)}")
    print(f"- Others: {len(others)}")

def create_templates(template_dir: Path):
    """Create HTML templates."""
    
    # Base template
    base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ title }}{% endblock %}</title>
    <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1><a href="/">XRP Ledger Standards</a></h1>
            <nav>
                <a href="/">All Standards</a>
                <a href="https://github.com/XRPLF/XRPL-Standards">GitHub</a>
            </nav>
        </div>
    </header>
    
    <main class="container">
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2024 XRP Ledger Foundation. Licensed under <a href="https://github.com/XRPLF/XRPL-Standards/blob/master/LICENSE">Apache License 2.0</a>.</p>
        </div>
    </footer>
</body>
</html>"""
    
    # Index template
    index_template = """{% extends "base.html" %}

{% block content %}
<div class="intro">
    <h2>XRP Ledger Standards (XLS)</h2>
    <p>XRP Ledger Standards (XLSs) describe standards and specifications relating to the XRP Ledger ecosystem that help achieve interoperability, compatibility, and excellent user experience.</p>
    <p>Total standards: <strong>{{ total_count }}</strong></p>
</div>

{% if released %}
<section class="xls-section">
    <h3>Released Standards</h3>
    <div class="xls-grid">
        {% for doc in released %}
        <div class="xls-card released">
            <div class="xls-header">
                <span class="xls-number">XLS-{{ doc.number }}</span>
                <span class="xls-status">{{ doc.status }}</span>
            </div>
            <h4><a href="/xls/{{ doc.folder }}.html">{{ doc.title }}</a></h4>
            <p class="xls-description">{{ doc.description }}</p>
            <p class="xls-author">{{ doc.author }}</p>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}

{% if candidates %}
<section class="xls-section">
    <h3>Candidate Standards</h3>
    <div class="xls-grid">
        {% for doc in candidates %}
        <div class="xls-card candidate">
            <div class="xls-header">
                <span class="xls-number">XLS-{{ doc.number }}</span>
                <span class="xls-status">{{ doc.status }}</span>
            </div>
            <h4><a href="/xls/{{ doc.folder }}.html">{{ doc.title }}</a></h4>
            <p class="xls-description">{{ doc.description }}</p>
            <p class="xls-author">{{ doc.author }}</p>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}

{% if drafts %}
<section class="xls-section">
    <h3>Draft Standards</h3>
    <div class="xls-grid">
        {% for doc in drafts %}
        <div class="xls-card draft">
            <div class="xls-header">
                <span class="xls-number">XLS-{{ doc.number }}</span>
                <span class="xls-status">{{ doc.status }}</span>
            </div>
            <h4><a href="/xls/{{ doc.folder }}.html">{{ doc.title }}</a></h4>
            <p class="xls-description">{{ doc.description }}</p>
            <p class="xls-author">{{ doc.author }}</p>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}

{% if others %}
<section class="xls-section">
    <h3>Other Standards</h3>
    <div class="xls-grid">
        {% for doc in others %}
        <div class="xls-card other">
            <div class="xls-header">
                <span class="xls-number">XLS-{{ doc.number }}</span>
                <span class="xls-status">{{ doc.status }}</span>
            </div>
            <h4><a href="/xls/{{ doc.folder }}.html">{{ doc.title }}</a></h4>
            <p class="xls-description">{{ doc.description }}</p>
            <p class="xls-author">{{ doc.author }}</p>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}
{% endblock %}"""
    
    # XLS document template
    xls_template = """{% extends "base.html" %}

{% block content %}
<div class="xls-document">
    <div class="xls-meta">
        <div class="xls-number-large">XLS-{{ doc.number }}</div>
        <div class="xls-status-badge {{ doc.status }}">{{ doc.status.title() }}</div>
    </div>
    
    <div class="document-content">
        {{ content|safe }}
    </div>
    
    <div class="document-nav">
        <a href="/">&larr; Back to All Standards</a>
        <a href="https://github.com/XRPLF/XRPL-Standards/tree/master/{{ doc.folder }}">View on GitHub</a>
    </div>
</div>
{% endblock %}"""
    
    # Write templates
    with open(template_dir / 'base.html', 'w') as f:
        f.write(base_template)
    
    with open(template_dir / 'index.html', 'w') as f:
        f.write(index_template)
    
    with open(template_dir / 'xls.html', 'w') as f:
        f.write(xls_template)

def create_css(assets_dir: Path):
    """Create CSS styles."""
    
    css_content = """/* XLS Standards Site Styles */

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
header {
    background: #fff;
    border-bottom: 1px solid #e9ecef;
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

header h1 {
    margin: 0;
    font-size: 1.5rem;
    display: inline-block;
}

header h1 a {
    text-decoration: none;
    color: #007bff;
}

header nav {
    float: right;
    margin-top: 0.5rem;
}

header nav a {
    margin-left: 1rem;
    text-decoration: none;
    color: #6c757d;
    font-weight: 500;
}

header nav a:hover {
    color: #007bff;
}

/* Main content */
main {
    padding: 2rem 0;
    min-height: calc(100vh - 140px);
}

.intro {
    text-align: center;
    margin-bottom: 3rem;
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.intro h2 {
    margin-top: 0;
    color: #007bff;
}

/* XLS sections */
.xls-section {
    margin-bottom: 3rem;
}

.xls-section h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: #495057;
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 0.5rem;
}

.xls-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
}

.xls-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    border-left: 4px solid #e9ecef;
}

.xls-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.xls-card.released {
    border-left-color: #28a745;
}

.xls-card.candidate {
    border-left-color: #ffc107;
}

.xls-card.draft {
    border-left-color: #6c757d;
}

.xls-card.other {
    border-left-color: #17a2b8;
}

.xls-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.xls-number {
    font-weight: bold;
    color: #007bff;
    font-size: 0.9rem;
}

.xls-status {
    background: #e9ecef;
    color: #495057;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    text-transform: uppercase;
    font-weight: 600;
}

.xls-card.released .xls-status {
    background: #d4edda;
    color: #155724;
}

.xls-card.candidate .xls-status {
    background: #fff3cd;
    color: #856404;
}

.xls-card.draft .xls-status {
    background: #d1ecf1;
    color: #0c5460;
}

.xls-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
}

.xls-card h4 a {
    text-decoration: none;
    color: #333;
}

.xls-card h4 a:hover {
    color: #007bff;
}

.xls-description {
    color: #6c757d;
    margin: 0.5rem 0;
    font-size: 0.9rem;
}

.xls-author {
    margin: 0;
    font-size: 0.85rem;
    color: #868e96;
}

/* XLS document page */
.xls-document {
    background: white;
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.xls-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e9ecef;
}

.xls-number-large {
    font-size: 2rem;
    font-weight: bold;
    color: #007bff;
}

.xls-status-badge {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.9rem;
}

.xls-status-badge.released {
    background: #d4edda;
    color: #155724;
}

.xls-status-badge.candidate {
    background: #fff3cd;
    color: #856404;
}

.xls-status-badge.draft {
    background: #d1ecf1;
    color: #0c5460;
}

.xls-status-badge.other {
    background: #e2e3e5;
    color: #495057;
}

.document-content {
    max-width: none;
}

.document-content h1,
.document-content h2,
.document-content h3,
.document-content h4,
.document-content h5,
.document-content h6 {
    margin-top: 2rem;
    margin-bottom: 1rem;
    color: #333;
}

.document-content h1 {
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 0.5rem;
}

.document-content h2 {
    border-bottom: 1px solid #e9ecef;
    padding-bottom: 0.3rem;
}

.document-content pre {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 1rem;
    overflow-x: auto;
    margin: 1rem 0;
}

.document-content code {
    background: #f8f9fa;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-size: 0.9em;
}

.document-content pre code {
    background: none;
    padding: 0;
}

.document-content blockquote {
    border-left: 4px solid #007bff;
    margin: 1rem 0;
    padding-left: 1rem;
    color: #6c757d;
}

.document-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.document-content th,
.document-content td {
    border: 1px solid #e9ecef;
    padding: 0.5rem;
    text-align: left;
}

.document-content th {
    background: #f8f9fa;
    font-weight: 600;
}

.document-nav {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid #e9ecef;
    display: flex;
    justify-content: space-between;
}

.document-nav a {
    color: #007bff;
    text-decoration: none;
    font-weight: 500;
}

.document-nav a:hover {
    text-decoration: underline;
}

/* Footer */
footer {
    background: #fff;
    border-top: 1px solid #e9ecef;
    padding: 1.5rem 0;
    margin-top: 3rem;
    text-align: center;
    color: #6c757d;
}

footer a {
    color: #007bff;
    text-decoration: none;
}

footer a:hover {
    text-decoration: underline;
}

/* Responsive */
@media (max-width: 768px) {
    header nav {
        float: none;
        margin-top: 1rem;
    }
    
    .xls-meta {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .document-nav {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .xls-grid {
        grid-template-columns: 1fr;
    }
}"""
    
    with open(assets_dir / 'style.css', 'w') as f:
        f.write(css_content)

if __name__ == "__main__":
    build_site()