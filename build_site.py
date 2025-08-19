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
    
    return XLSDocument(
        number=number,
        title=metadata['title'],
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
    template_dir = root_dir / 'site' / 'templates'
    assets_dir = root_dir / 'site' / 'assets'
    
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
    if not template_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {template_dir}")
    
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
    
    # Sort documents by number in reverse order (later ones more relevant)
    xls_docs.sort(key=lambda x: int(x.number), reverse=True)
    
    # Generate index page
    index_template = env.get_template('index.html')
    index_html = index_template.render(
        title="XRP Ledger Standards (XLS)",
        total_count=len(xls_docs),
        xls_docs=xls_docs,
        base_url=base_url
    )
    
    # Write index file
    with open(site_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Copy CSS file
    css_source = assets_dir / 'style.css'
    css_dest = site_dir / 'assets' / 'style.css'
    if css_source.exists():
        shutil.copy2(css_source, css_dest)
    else:
        raise FileNotFoundError(f"CSS file not found: {css_source}")
    
    print(f"Site built successfully! Generated {len(xls_docs)} XLS documents.")
    
    # Count by status for reporting
    released_count = len([doc for doc in xls_docs if doc.status == 'released'])
    candidates_count = len([doc for doc in xls_docs if doc.status == 'candidate'])
    drafts_count = len([doc for doc in xls_docs if doc.status == 'draft'])
    others_count = len([doc for doc in xls_docs if doc.status not in ['draft', 'candidate', 'released']])
    
    print(f"- Released: {released_count}")
    print(f"- Candidates: {candidates_count}")
    print(f"- Drafts: {drafts_count}")
    print(f"- Others: {others_count}")

if __name__ == "__main__":
    build_site()