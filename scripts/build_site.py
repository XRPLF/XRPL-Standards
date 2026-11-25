#!/usr/bin/env python3
"""Build the XLS Standards static site into scripts/_site."""

import datetime
import os
import posixpath
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import markdown
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from patch_map import amendment_name, map_patch, parse_headings
from xls_parser import XLSDocument, find_xls_documents

SCRIPTS_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPTS_DIR.parent
SITE_DIR = SCRIPTS_DIR / "_site"
REPO_URL = "https://github.com/XRPLF/XRPL-Standards"

CATEGORY_DESCRIPTIONS = {
    "Amendment": (
        "Changes to the core XRP Ledger protocol that require network "
        "consensus and activation through the amendment process."
    ),
    "System": (
        "XRP Ledger APIs, formats, and behaviors that do not require consensus "
        "changes but define how applications interact with the network."
    ),
    "Ecosystem": (
        "Best practices, conventions, and guidelines for the XRP Ledger "
        "ecosystem that do not require protocol changes."
    ),
    "Meta": "Standards about the XLS process itself.",
}

STATUS_DESCRIPTIONS = {
    "Draft": "Work in progress, subject to change.",
    "Final": "Completed standard. Only errata and clarifications change it.",
    "Living": "Updated continually; never reaches finality.",
    "Deprecated": "No longer supported.",
    "Stagnant": "A Draft with no activity for 6 months or more.",
    "Withdrawn": "Withdrawn by the author and will not be implemented.",
}


def _convert_math_delimiters(html: str) -> str:
    """Convert $...$ and $$...$$ to \\(...\\) and \\[...\\] in HTML.

    Only matches when the closing delimiter is NOT preceded by whitespace,
    which avoids false positives on currency like "$1.0m ... $1.0m".
    Skips content inside <code> and <pre> tags.
    """
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
            # Target the tab stop for this depth, but never outdent below the
            # parent's content column: CommonMark requires child items to be
            # indented at least to the parent's content column, so shifting
            # further left would break GitHub rendering.
            parent_content_col = stack[-1][1] if stack else 0
            new_indent = max(4 * depth, parent_content_col)
            stack.append((indent, item_match.end(), depth))
            out.append(_shift(line, new_indent - indent))
            continue

        # A continuation line (paragraph, table, code block, ...) belongs to the
        # innermost open item whose content column it reaches.
        while stack and indent < stack[-1][1]:
            stack.pop()
        if stack:
            parent_content_col = stack[-1][1]
            shift = 4 * (stack[-1][2] + 1) - parent_content_col
            # Clamp: never move the continuation below the parent's content
            # column, so wide ordered markers (e.g. `100. `) keep their
            # continuations nested in both CommonMark and Python-Markdown.
            shift = max(shift, parent_content_col - indent)
        else:
            shift = 0
        out.append(_shift(line, shift))

    return "\n".join(out)


class LinkResolver:
    """Map relative links in repository Markdown to their place in the site.

    `pages` maps a repo-relative source path (for example
    `XLS-0065-single-asset-vault/README.md`) to the site-relative path of the
    page rendered from it. A link to a rendered source becomes a link to its
    page. A link to any other file in the repository, except Markdown, becomes
    a link to a copy of that file in the site, at the same path under `xls/`
    that it has under the repository root. Other Markdown files and missing
    files point at GitHub.
    """

    def __init__(self, pages: dict[str, str], root_dir: Path, site_dir: Path):
        self.pages = pages
        self.root_dir = root_dir
        self.site_dir = site_dir
        self.copied: set[str] = set()

    def resolve(self, url: str, source: str, page: str) -> str:
        """Return `url` as seen from `page`, where `url` is written in `source`.

        `source` and `page` are POSIX paths relative to the repository root and
        the site root.
        """
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path or url.startswith("/"):
            return url
        target = posixpath.normpath(
            posixpath.join(posixpath.dirname(source), parts.path)
        )
        fragment = f"#{parts.fragment}" if parts.fragment else ""
        if target.startswith("../"):
            return url
        if target in self.pages:
            site_target = self.pages[target]
        elif (self.root_dir / target).is_file() and not target.endswith(".md"):
            site_target = self._copy(target)
        else:
            return f"{REPO_URL}/blob/master/{target}{fragment}"
        rel = posixpath.relpath(site_target, posixpath.dirname(page) or ".")
        return rel + fragment

    def _copy(self, target: str) -> str:
        site_target = f"xls/{target}"
        if target not in self.copied:
            dest = self.site_dir / site_target
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root_dir / target, dest)
            self.copied.add(target)
        return site_target


class _LinkTreeprocessor(Treeprocessor):
    def __init__(self, md, resolver: LinkResolver, source: str, page: str):
        super().__init__(md)
        self.resolver = resolver
        self.source = source
        self.page = page

    def run(self, root):
        for el in root.iter():
            attr = {"a": "href", "img": "src"}.get(el.tag)
            if attr and el.get(attr):
                el.set(attr, self.resolver.resolve(el.get(attr), self.source, self.page))


_ALERT_RE = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*")


class _AlertTreeprocessor(Treeprocessor):
    """Render GitHub alerts (`> [!NOTE]`) as `<div class="alert note">`."""

    def run(self, root):
        for quote in root.iter("blockquote"):
            first = quote[0] if len(quote) else None
            match = first is not None and first.tag == "p" and _ALERT_RE.match(first.text or "")
            if not match:
                continue
            kind = match.group(1).lower()
            first.text = first.text[match.end() :]
            quote.tag = "div"
            quote.set("class", f"alert {kind}")
            title = quote.makeelement("p", {"class": "alert-title"})
            title.text = kind.capitalize()
            quote.insert(0, title)


class _MarkerTreeprocessor(Treeprocessor):
    """Insert HTML after headings, keyed by heading id.

    Runs after the toc processor has given headings their ids.
    """

    def __init__(self, md, markers: dict[str, tuple[str, str]]):
        super().__init__(md)
        self.markers = markers

    def run(self, root):
        for parent in list(root.iter()):
            for i, el in reversed(list(enumerate(parent))):
                marker = self.markers.get(el.get("id", "")) if el.tag in _HEADINGS else None
                if marker:
                    html, amendments = marker
                    el.set("class", (el.get("class", "") + " patched").strip())
                    el.set("data-amendments", amendments)
                    holder = parent.makeelement("div", {})
                    holder.text = self.md.htmlStash.store(html)
                    parent.insert(i + 1, holder)


_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class _MarkerExtension(Extension):
    def __init__(self, markers: dict[str, tuple[str, str]]):
        super().__init__()
        self.markers = markers

    def extendMarkdown(self, md):
        # The toc treeprocessor (priority 5) assigns ids; run after it.
        md.treeprocessors.register(_MarkerTreeprocessor(md, self.markers), "xls_markers", 4)


class _LinkExtension(Extension):
    def __init__(self, resolver: LinkResolver, source: str, page: str):
        super().__init__()
        self.args = (resolver, source, page)

    def extendMarkdown(self, md):
        # Run after inline links are parsed (priority 20) and before the TOC.
        md.treeprocessors.register(_LinkTreeprocessor(md, *self.args), "xls_links", 15)
        md.treeprocessors.register(_AlertTreeprocessor(md), "xls_alerts", 14)


def _squash(text: str) -> str:
    return re.sub(r"\W", "", text.lower())


def strip_title_heading(content: str, title: str) -> str:
    """Remove the first `# ` heading if it repeats the preamble title.

    The page header already shows the title. Specs whose first H1 is something
    else (for example `# Abstract`) keep it.
    """
    match = re.search(r"^# (.+)\n", content, flags=re.MULTILINE)
    if match and _squash(title) in _squash(match.group(1)):
        return content[: match.start()] + content[match.end() :]
    return content


def convert_markdown_to_html(
    content: str,
    resolver: LinkResolver | None = None,
    source: str = "",
    page: str = "",
    markers: dict[str, tuple[str, str]] | None = None,
) -> tuple[str, str]:
    """Convert Markdown to HTML.

    Returns the body HTML (with the preamble <pre> block removed) and the
    table-of-contents HTML. Relative links are rewritten by `resolver` when
    one is given; `source` and `page` are the repo-relative path of the
    Markdown file and the site-relative path of the page it becomes.
    `markers` maps heading ids to (HTML inserted after the heading, a
    space-separated list set as the heading's data-amendments attribute).
    """
    content = re.sub(r"<pre>.*?</pre>", "", content, count=1, flags=re.DOTALL)
    content = normalize_list_indentation(content)

    extensions = ["extra", "codehilite", "toc"]
    if resolver:
        extensions.append(_LinkExtension(resolver, source, page))
    if markers:
        extensions.append(_MarkerExtension(markers))
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs={
            "codehilite": {"css_class": "highlight"},
            "toc": {"permalink": True, "toc_depth": "1-3"},
        },
    )
    html = md.convert(content)

    # Convert LaTeX math delimiters after markdown processing so that
    # the markdown processor doesn't strip backslashes from \(...\).
    html = _convert_math_delimiters(html)
    return html, md.toc


def page_path(doc: XLSDocument) -> str:
    """Return the site-relative page for a spec or patch.

    `XLS-0065-x/README.md` becomes `xls/XLS-0065-x.html`; a patch keeps its
    folder, so `XLS-0065-x/65.1-amendment/65.1.2-y.md` becomes
    `xls/XLS-0065-x/65.1-amendment/65.1.2-y.html` and `65.2-fix/README.md`
    becomes `xls/XLS-0065-x/65.2-fix/index.html`.
    """
    if not doc.is_patch:
        return f"xls/{doc.folder}.html"
    path = posixpath.splitext(doc.source)[0]
    if path.endswith("/README"):
        path = path[: -len("README")] + "index"
    return f"xls/{path}.html"


def relroot(page: str) -> str:
    return posixpath.relpath(".", posixpath.dirname(page) or ".")


def toc_ancestors(ids, headings, toc_level: int = 3) -> set[str]:
    """Return the ids to mark in the table of contents for changed headings.

    The contents list stops at level 3, so a changed level-5 heading marks its
    level-3 ancestor instead.
    """
    marked, stack = set(), []
    for heading in headings:
        while stack and stack[-1].level >= heading.level:
            stack.pop()
        stack.append(heading)
        if heading.id in ids:
            visible = [h for h in stack if h.level <= toc_level]
            if visible:
                marked.add(visible[-1].id)
    return marked


def amendments(patches: list[XLSDocument]) -> list[str]:
    """Return the distinct amendment names of the patches, in patch order."""
    return list(dict.fromkeys(p.amendment for p in patches if p.amendment))


def author_links(doc: XLSDocument) -> Markup:
    """Render a document's authors as comma-separated links."""
    return Markup(", ").join(
        Markup('<a href="{}">{}</a>').format(link, name) if link else name
        for name, link in doc.authors
    )


class SiteBuilder:
    def __init__(self, root_dir: Path = ROOT_DIR, site_dir: Path = SITE_DIR):
        self.root_dir = root_dir
        self.site_dir = site_dir
        # GitHub Pages serves the site under /<repo>/, so redirect pages need an
        # absolute target. Everything else uses relative links.
        self.base_url = os.environ.get(
            "GITHUB_PAGES_BASE_URL",
            "/XRPL-Standards" if "GITHUB_REPOSITORY" in os.environ else "",
        )
        self.env = Environment(
            loader=FileSystemLoader(SCRIPTS_DIR / "templates"),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["author_links"] = author_links
        self.env.globals.update(
            year=datetime.date.today().year,
            repo_url=REPO_URL,
            category_descriptions=CATEGORY_DESCRIPTIONS,
            status_descriptions=STATUS_DESCRIPTIONS,
        )

    def render(self, template: str, page: str, **context) -> None:
        """Render `template` to the site-relative path `page`."""
        out = self.site_dir / page
        out.parent.mkdir(parents=True, exist_ok=True)
        html = self.env.get_template(template).render(root=relroot(page), **context)
        out.write_text(html, encoding="utf-8")

    def build(self) -> list[XLSDocument]:
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        self.site_dir.mkdir()

        docs = find_xls_documents(self.root_dir)
        docs.sort(key=lambda d: d.raw_number, reverse=True)

        pages = {d.source: page_path(d) for d in docs}
        pages.update({p.source: page_path(p) for d in docs for p in d.patches})
        pages["CONTRIBUTING.md"] = "contribute.html"
        resolver = LinkResolver(pages, self.root_dir, self.site_dir)

        for doc in docs:
            self.write_doc(doc, resolver)
        self.write_redirects(docs)
        self.write_listings(docs)
        self.write_contribute(resolver)
        self.copy_assets()
        return docs

    def write_doc(self, doc: XLSDocument, resolver: LinkResolver) -> None:
        """Write a spec page, then a page for each of its patches."""
        content = self.read(doc)
        parent_headings = parse_headings(content) if doc.patches else []
        names = {h.id: h.name for h in parent_headings}
        by_parent = defaultdict(list)  # parent heading id -> [(patch, match)]
        by_patch = {}  # patch source -> [match]
        for patch in doc.patches:
            patch.amendment = amendment_name(self.read(patch)) or self.index_amendment(doc, patch)
            matches = map_patch(self.read(patch), parent_headings)
            by_patch[patch.source] = matches
            for match in matches:
                if match.leaf:
                    by_parent[match.parent_id].append((patch, match))

        page = page_path(doc)
        markers = {
            heading_id: (
                self.env.get_template("_parent_marker.html").render(
                    changes=changes, page_of=self.relative_page(page)
                ),
                " ".join(sorted({p.amendment for p, _ in changes})),
            )
            for heading_id, changes in by_parent.items()
        }
        self.write_page(
            doc,
            content,
            resolver,
            markers,
            amendments=amendments(doc.patches),
            patched_ids=sorted(toc_ancestors(markers, parent_headings)),
        )

        for patch in doc.patches:
            patch_page = page_path(patch)
            markers = {}
            for match in by_patch[patch.source]:
                markers.setdefault(match.patch_id, []).append(match)
            markers = {
                patch_id: (
                    self.env.get_template("_patch_marker.html").render(
                        parent=doc,
                        matches=matches,
                        parent_href=self.relative_page(patch_page)(doc),
                        names=names,
                    ),
                    patch.amendment,
                )
                for patch_id, matches in markers.items()
            }
            self.write_page(patch, self.read(patch), resolver, markers, parent=doc)

    def read(self, doc: XLSDocument) -> str:
        return (self.root_dir / doc.source).read_text(encoding="utf-8")

    def index_amendment(self, parent: XLSDocument, patch: XLSDocument) -> str:
        """Return the amendment named by the x.y index a patch belongs to."""
        index_xls = ".".join(patch.xls.split(".")[:2])
        for other in parent.patches:
            if other.xls == index_xls and other is not patch:
                return amendment_name(self.read(other))
        return ""

    def relative_page(self, from_page: str):
        """Return a function giving the href of a document's page from `from_page`."""
        return lambda doc: posixpath.relpath(page_path(doc), posixpath.dirname(from_page))

    def write_page(
        self,
        doc: XLSDocument,
        content: str,
        resolver: LinkResolver,
        markers: dict[str, str],
        **context,
    ) -> None:
        page = page_path(doc)
        content = strip_title_heading(content, doc.title)
        html, toc = convert_markdown_to_html(content, resolver, doc.source, page, markers)
        self.render(
            "xls.html",
            page,
            title=f"{doc.label}: {doc.title}",
            description=doc.description,
            doc=doc,
            requires=self.requires_links(doc, page),
            content=html,
            toc=toc,
            has_math=bool(re.search(r"\\\(|\\\[", html)),
            implementations=re.findall(r"https?://[^\s,;]+", doc.implementation or ""),
            page_of=self.relative_page(page),
            **context,
        )

    @staticmethod
    def requires_links(doc: XLSDocument, page: str) -> list[tuple[str, str]]:
        """Return (label, href) for each XLS named in the `requires` field.

        Each href points at the xls/xls-<number>.html redirect page, which
        also covers patch numbers such as 65.1.4.
        """
        text = re.sub(r"\]\([^)]*\)", "]", doc.requires or "")  # drop link targets
        numbers = dict.fromkeys(
            re.sub(r"^0+(?=\d)", "", n) for n in re.findall(r"\d+(?:\.\d+)*", text)
        )
        rel = posixpath.relpath("xls", posixpath.dirname(page))
        return [(f"XLS-{n}", posixpath.join(rel, f"xls-{n}.html")) for n in numbers]

    def write_redirects(self, docs: list[XLSDocument]) -> None:
        """Write xls/xls-<number>.html pages that redirect to each document.

        Patches get one too, for example xls/xls-65.1.2.html.
        """
        for doc in docs + [p for d in docs for p in d.patches]:
            target = page_path(doc)
            target = (
                f"{self.base_url}/{target}"
                if self.base_url
                else posixpath.relpath(target, "xls")
            )
            aliases = {doc.xls} if doc.is_patch else {doc.number, str(doc.raw_number)}
            for alias in aliases:
                self.render(
                    "redirect.html",
                    f"xls/xls-{alias}.html",
                    title=f"{doc.label}: {doc.title}",
                    target_url=target,
                )

    def write_listings(self, docs: list[XLSDocument]) -> None:
        by_category = defaultdict(list)
        for doc in docs:
            by_category[doc.category].append(doc)
        categories = sorted((c, len(d)) for c, d in by_category.items())

        self.render(
            "index.html",
            "index.html",
            title="XRP Ledger Standards (XLS)",
            description="Index of XRP Ledger Standards (XLSes).",
            docs=docs,
            categories=categories,
            total_count=len(docs),
        )
        for category, category_docs in by_category.items():
            self.render(
                "category.html",
                f"category/{category.lower()}.html",
                title=f"{category} XLS Standards",
                description=CATEGORY_DESCRIPTIONS.get(category, ""),
                category=category,
                docs=category_docs,
                categories=categories,
                total_count=len(docs),
            )

    def write_contribute(self, resolver: LinkResolver) -> None:
        source = "CONTRIBUTING.md"
        content = (self.root_dir / source).read_text(encoding="utf-8")
        html, _ = convert_markdown_to_html(content, resolver, source, "contribute.html")
        self.render(
            "contribute.html",
            "contribute.html",
            title="Contributing to XLS Standards",
            description="How to propose and update an XRP Ledger Standard.",
            content=html,
        )

    def copy_assets(self) -> None:
        shutil.copytree(SCRIPTS_DIR / "assets", self.site_dir / "assets")


def main() -> None:
    docs = SiteBuilder().build()
    print(f"Site built successfully! Generated {len(docs)} XLS documents.")
    for status, count in Counter(d.status.lower() for d in docs).items():
        print(f"- {status.capitalize()}: {count}")


if __name__ == "__main__":
    main()
