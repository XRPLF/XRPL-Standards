#!/usr/bin/env python3
"""
Build script for XLS Standards static site generator.
Converts markdown XLS files to HTML and creates an index page.
"""

import os
import shutil
from pathlib import Path
import re

import markdown
from jinja2 import Environment, FileSystemLoader

from xls_parser import find_xls_documents
from collections import Counter


def convert_markdown_to_html(content: str) -> str:
    """Convert markdown content to HTML."""
    # Insert a TOC marker after the first metadata block, unless one already exists.
    if "[TOC]" not in content:
        content = re.sub(r"</pre>", "</pre>\n\n[TOC]\n\n", content, count=1)
    content = re.sub(r"\.\./(XLS-[0-9A-Za-z-]+)/README\.md", r"./\1.html", content)

    md = markdown.Markdown(
        extensions=["extra", "codehilite", "toc", "tables"],
        extension_configs={
            "codehilite": {"css_class": "highlight"},
            "toc": {"permalink": True, "baselevel": 2, "toc_depth": 3, "title": "Table of Contents"},
        },
    )
    return md.convert(content)


def build_site():
    """Main function to build the static site."""

    # Setup directories
    source_dir = Path(__file__).parent.resolve()
    root_dir = source_dir.parent
    site_dir = source_dir / "_site"
    template_dir = source_dir / "templates"
    assets_dir = source_dir / "assets"

    # Set base URL for GitHub Pages (can be overridden with env var)
    base_url = os.environ.get("GITHUB_PAGES_BASE_URL", "/XRPL-Standards") if "GITHUB_REPOSITORY" in os.environ else os.environ.get("GITHUB_PAGES_BASE_URL", ".")

    # Clean and create site directory
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir()

    # Create subdirectories
    (site_dir / "xls").mkdir()
    (site_dir / "category").mkdir()  # New directory for category pages
    (site_dir / "assets").mkdir()

    # Setup Jinja2 environment
    if not template_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {template_dir}")

    env = Environment(loader=FileSystemLoader(template_dir))

    # Find and parse all XLS documents using the parser module
    xls_docs = find_xls_documents(root_dir)

    # Generate HTML for each document
    for doc in xls_docs:
        folder = root_dir / doc.folder
        readme_path = folder / "README.md"

        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Convert to HTML
            html_content = convert_markdown_to_html(content)

            # Render XLS page
            xls_template = env.get_template("xls.html")
            rendered_html = xls_template.render(
                doc=doc,
                content=html_content,
                title=f"XLS-{doc.number}: {doc.title}",
                base_url=".." if base_url == "." else base_url,
            )

            # Write XLS HTML file
            output_path = site_dir / "xls" / f"{doc.folder}.html"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)

            print(f"Generated: {output_path}")

        except Exception as e:
            print(f"Error processing {doc.folder}: {e}")
            raise

    # Sort documents by number in reverse order (later ones more relevant)
    xls_docs.sort(key=lambda x: int(x.number), reverse=True)

    # Generate simple redirect pages so /xls-<number>.html redirects to
    # the canonical document URL under /xls/<folder>.html.
    redirect_template = env.get_template("redirect.html")
    for doc in xls_docs:
        # Redirect pages live under /xls/, next to the canonical XLS HTML files.
        # For local builds (base_url == "."), use a relative URL that does *not*
        # add another /xls/ segment; otherwise we create /xls/xls/<file>.html.
        if base_url == ".":
            # From scripts/_site/xls/xls-<number>.html → ./<folder>.html
            target_url = f"./{doc.folder}.html"
        else:
            # On GitHub Pages, use an absolute URL with the base path.
            target_url = f"{base_url}/xls/{doc.folder}.html"

        redirect_html = redirect_template.render(
            title=f"XLS-{doc.number}: {doc.title}",
            target_url=target_url,
        )

        # /xls/ alias: /xls/xls-<number>.html
        redirect_xls_path = site_dir / "xls" / f"xls-{doc.number}.html"
        with open(redirect_xls_path, "w", encoding="utf-8") as f:
            f.write(redirect_html)

        print(f"Generated redirect: {redirect_xls_path} -> {target_url}")

    # Group documents by category for category pages and navigation
    categories = {}
    for doc in xls_docs:
        category = doc.category
        if category not in categories:
            categories[category] = []
        categories[category].append(doc)

    # Generate category pages
    category_template = env.get_template("category.html")
    all_categories = [(cat, len(docs)) for cat, docs in sorted(categories.items())]

    for category, category_docs in categories.items():
        # Sort category documents by number in reverse order
        category_docs.sort(key=lambda x: int(x.number), reverse=True)

        category_html = category_template.render(
            title=f"{category} XLS Standards",
            category=category,
            category_docs=category_docs,
            all_categories=all_categories,
            total_count=len(xls_docs),
            base_url=".." if base_url == "." else base_url,
        )

        # Write category HTML file
        category_file = site_dir / "category" / f"{category.lower()}.html"
        with open(category_file, "w", encoding="utf-8") as f:
            f.write(category_html)

        print(f"Generated category page: {category_file}")

    # Generate index page with category navigation
    index_template = env.get_template("index.html")
    index_html = index_template.render(
        title="XRP Ledger Standards (XLS)",
        total_count=len(xls_docs),
        xls_docs=xls_docs,
        all_categories=all_categories,
        base_url=base_url,
    )

    # Write index file
    with open(site_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    # Generate contribute page from CONTRIBUTING.md
    contributing_path = root_dir / "CONTRIBUTING.md"
    if contributing_path.exists():
        try:
            with open(contributing_path, "r", encoding="utf-8") as f:
                contributing_content = f.read()

            # Convert markdown to HTML
            contributing_html_content = convert_markdown_to_html(contributing_content)

            # Render contribute page
            contribute_template = env.get_template("contribute.html")
            contribute_html = contribute_template.render(
                title="Contributing to XLS Standards",
                content=contributing_html_content,
                base_url=base_url,
            )

            # Write contribute file
            with open(site_dir / "contribute.html", "w", encoding="utf-8") as f:
                f.write(contribute_html)

            print(f"Generated contribute page from CONTRIBUTING.md")

        except Exception as e:
            print(f"Error generating contribute page: {e}")
    else:
        print("Warning: CONTRIBUTING.md not found")

    # Copy CSS file
    css_source = assets_dir / "style.css"
    css_dest = site_dir / "assets" / "style.css"
    if css_source.exists():
        shutil.copy2(css_source, css_dest)
    else:
        raise FileNotFoundError(f"CSS file not found: {css_source}")

    # Copy favicon
    favicon_source = assets_dir / "favicon.ico"
    favicon_dest = site_dir / "assets" / "favicon.ico"
    if favicon_source.exists():
        shutil.copy2(favicon_source, favicon_dest)
    else:
        print(f"Warning: Favicon not found: {favicon_source}")

    print(f"Site built successfully! Generated {len(xls_docs)} XLS documents.")

    # Count by status for reporting
    # Count documents by status (case-insensitive, no hardcoding)
    status_counts = Counter(getattr(doc, "status", "").strip().lower() or "unknown" for doc in xls_docs)

    for status, count in status_counts.items():
        print(f"- {status.capitalize()}: {count}")


if __name__ == "__main__":
    build_site()
