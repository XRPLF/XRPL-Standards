#!/usr/bin/env python3
"""
Build script for XLS Standards static site generator.
Converts markdown XLS files to HTML and creates an index page.
"""

import os
import re
import shutil
from collections import Counter
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from xls_parser import find_xls_documents


def _convert_math_delimiters(html: str) -> str:
    """Convert $...$ and $$...$$ to \\(...\\) and \\[...\\] in HTML.

    Only matches when the closing delimiter is NOT preceded by whitespace,
    which avoids false positives on currency like "$1.0m ... $1.0m".
    Skips content inside <code> and <pre> tags.
    """
    # Split the HTML into segments: code/pre blocks vs. everything else.
    # Process only non-code segments.
    parts = re.split(
        r"(<code[^>]*>.*?</code>|<pre[^>]*>.*?</pre>)", html, flags=re.DOTALL
    )
    for i, part in enumerate(parts):
        if part.startswith("<code") or part.startswith("<pre"):
            continue
        # Display math $$...$$ → \[...\]
        part = re.sub(r"\$\$([^\$]+?)\$\$", r"\\[\1\\]", part)
        # Inline math $...$ → \(...\)
        # Require: non-whitespace after opening $ and before closing $.
        # Disallow newlines and HTML tags (<, >) inside the match to
        # prevent spanning across HTML element boundaries.
        part = re.sub(
            r"(?<!\$)\$(\S(?:[^\$\n<>]*?\S)?)\$(?!\$)",
            r"\\(\1\\)",
            part,
        )
        parts[i] = part
    return "".join(parts)


_LIST_ITEM_RE = re.compile(r"^(?P<indent> *)(?P<marker>[-*+]|\d{1,9}[.)])(?P<space> +)")
_FENCE_RE = re.compile(r"^ *(?P<fence>```+|~~~+)")


def _shift(line: str, amount: int) -> str:
    """Add (or, for a negative amount, remove) leading spaces from a line."""
    if amount >= 0:
        return " " * amount + line
    return line[min(-amount, len(line) - len(line.lstrip(" "))) :]


def normalize_list_indentation(content: str) -> str:
    """Re-indent nested lists to 4 spaces per level.

    GitHub (CommonMark) nests a list item whenever it is indented to the
    parent item's content column, so `- ` parents accept 2-space children and
    `1. ` parents accept 3-space children. Python-Markdown instead requires a
    full tab stop (4 spaces) per level and renders anything shallower as a
    sibling. This rewrites the indentation so both renderers agree.
    """
    # Each stack entry describes an open list item we are currently inside:
    # the column its marker starts at, the column its content starts at, and
    # its nesting depth (one tab stop per level in the rewritten output).
    stack: list[tuple[int, int, int]] = []
    fence: str | None = None
    out = []

    for line in content.split("\n"):
        fence_match = _FENCE_RE.match(line)
        if fence is not None:
            # Inside a fenced code block: pass lines through untouched and only
            # look for the closing fence.
            if fence_match and fence_match.group("fence").startswith(fence):
                fence = None
            out.append(line)
            continue

        if fence_match:
            # Fenced blocks are left exactly as they are: Python-Markdown only
            # recognizes fences indented by less than a tab stop, so moving one
            # can only ever break it.
            fence = fence_match.group("fence")
            out.append(line)
            continue

        if not line.strip():
            out.append(line)
            continue

        indent = len(line) - len(line.lstrip(" "))
        item_match = _LIST_ITEM_RE.match(line)

        if item_match:
            # Close every item whose content column this marker sits outside of.
            while stack and indent < stack[-1][1]:
                stack.pop()
            depth = len(stack)
            stack.append((indent, item_match.end(), depth))
            out.append(_shift(line, 4 * depth - indent))
            continue

        # A continuation line (paragraph, table, code block, ...) belongs to the
        # innermost open item whose content column it reaches.
        while stack and indent < stack[-1][1]:
            stack.pop()
        shift = 4 * (stack[-1][2] + 1) - stack[-1][1] if stack else 0
        out.append(_shift(line, shift))

    return "\n".join(out)


def convert_markdown_to_html(content: str) -> str:
    """Convert markdown content to HTML."""
    # Insert a TOC marker after the first metadata block, unless one already exists.
    if "[TOC]" not in content:
        content = re.sub(r"</pre>", "</pre>\n\n[TOC]\n\n", content, count=1)
    content = re.sub(r"\.\./(XLS-[0-9A-Za-z-]+)/README\.md", r"./\1.html", content)
    content = normalize_list_indentation(content)

    md = markdown.Markdown(
        extensions=["extra", "codehilite", "toc", "tables"],
        extension_configs={
            "codehilite": {"css_class": "highlight"},
            "toc": {
                "permalink": True,
                "baselevel": 2,
                "toc_depth": 3,
                "title": "Table of Contents",
            },
        },
    )
    html = md.convert(content)

    # Convert LaTeX math delimiters after markdown processing so that
    # the markdown processor doesn't strip backslashes from \(...\).
    html = _convert_math_delimiters(html)

    return html


def build_site():
    """Main function to build the static site."""

    # Setup directories
    source_dir = Path(__file__).parent.resolve()
    root_dir = source_dir.parent
    site_dir = source_dir / "_site"
    template_dir = source_dir / "templates"
    assets_dir = source_dir / "assets"

    # Set base URL for GitHub Pages (can be overridden with env var)
    base_url = (
        os.environ.get("GITHUB_PAGES_BASE_URL", "/XRPL-Standards")
        if "GITHUB_REPOSITORY" in os.environ
        else os.environ.get("GITHUB_PAGES_BASE_URL", ".")
    )

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
        def add_redirect(redirect_url, target_url):
            redirect_xls_path = site_dir / "xls" / redirect_url
            with open(redirect_xls_path, "w", encoding="utf-8") as f:
                f.write(redirect_html)

            print(f"Generated redirect: {redirect_xls_path} -> {target_url}")

        add_redirect(f"xls-{doc.number}.html", target_url)
        add_redirect(f"xls-{doc.raw_number}.html", target_url)

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
    status_counts = Counter(
        getattr(doc, "status", "").strip().lower() or "unknown" for doc in xls_docs
    )

    for status, count in status_counts.items():
        print(f"- {status.capitalize()}: {count}")


if __name__ == "__main__":
    build_site()
