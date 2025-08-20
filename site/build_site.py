#!/usr/bin/env python3
"""
Build script for XLS Standards static site generator.
Converts markdown XLS files to HTML and creates an index page.
"""

import os
import shutil
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from xls_parser import find_xls_documents


def convert_markdown_to_html(content: str) -> str:
    """Convert markdown content to HTML."""
    md = markdown.Markdown(
        extensions=["extra", "codehilite", "toc", "tables"],
        extension_configs={
            "codehilite": {"css_class": "highlight"},
            "toc": {"permalink": True},
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

    # Generate index page
    index_template = env.get_template("index.html")
    index_html = index_template.render(
        title="XRP Ledger Standards (XLS)",
        total_count=len(xls_docs),
        xls_docs=xls_docs,
        base_url=base_url,
    )

    # Write index file
    with open(site_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    # Copy CSS file
    css_source = assets_dir / "style.css"
    css_dest = site_dir / "assets" / "style.css"
    if css_source.exists():
        shutil.copy2(css_source, css_dest)
    else:
        raise FileNotFoundError(f"CSS file not found: {css_source}")

    print(f"Site built successfully! Generated {len(xls_docs)} XLS documents.")

    # Count by status for reporting
    released_count = len([doc for doc in xls_docs if doc.status == "released"])
    candidates_count = len([doc for doc in xls_docs if doc.status == "candidate"])
    drafts_count = len([doc for doc in xls_docs if doc.status == "draft"])
    others_count = len(
        [
            doc
            for doc in xls_docs
            if doc.status not in ["draft", "candidate", "released"]
        ]
    )

    print(f"- Released: {released_count}")
    print(f"- Candidates: {candidates_count}")
    print(f"- Drafts: {drafts_count}")
    print(f"- Others: {others_count}")


if __name__ == "__main__":
    build_site()
