"""Map sections of a nested amendment patch to the parent sections they change.

Patches (XLS-1 §4.4.4) are prose deltas, so this reads only what a patch
states. A patch section points at a parent section when:

1. it links to one (`../README.md#312-fields`), or names one by number
   (`parent §3.8.5.2`, `parent [§3.2.1](...)`); or
2. it sits under the patch's Specification section and its heading path
   matches the parent's by title: `Transaction: VaultDelete` > `Failure
   Conditions` > `Data Verification` matches the parent's headings with the
   same titles, whatever their numbers.

Anything else is not matched. Nothing is guessed from body text.
"""

import re
from dataclasses import dataclass, field

import markdown

# A leading section number: "3.1.2 ", "3.1.2. ", "A.1 ".
_NUMBER_RE = re.compile(r"^(?:[A-Z]|\d+)(?:\.\d+)*\.?\s+")
# "parent §3.8.5.2" or "parent [§3.2.1](...)". \b keeps "transparent §" out.
SECTION_REF_RE = re.compile(r"\b[Pp]arent\s+\[?§\s*(\d+(?:\.\d+)*)")
PARENT_LINK_RE = re.compile(r"\]\(\.\./README\.md#([^)\s]+)\)")
_FENCE_RE = re.compile(r"^(```|~~~)")


@dataclass
class Heading:
    level: int
    id: str
    name: str  # as written, for example "3.1.2 Fields"
    number: str  # "3.1.2", or "" when unnumbered
    title: str  # "Fields"
    body: str = ""  # Markdown between this heading and the next one
    children: list = field(default_factory=list)


@dataclass
class Match:
    patch_id: str
    parent_id: str
    how: str  # "link", "section", or "title"
    patch_name: str = ""
    parent_name: str = ""
    # False when a section below this patch section also matches; the more
    # specific match is the one to show a reader.
    leaf: bool = True


def normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.replace("`", "").lower()).strip()


def parse_headings(content: str) -> list[Heading]:
    """Return every heading with the id Python-Markdown's toc gives it."""
    md = markdown.Markdown(extensions=["toc"])
    md.convert(content)
    flat = []

    def walk(tokens):
        for token in tokens:
            name = token["name"]
            number = _NUMBER_RE.match(name)
            flat.append(
                Heading(
                    level=token["level"],
                    id=token["id"],
                    name=name,
                    number=number.group(0).strip().rstrip(".") if number else "",
                    title=name[number.end() :] if number else name,
                )
            )
            walk(token["children"])

    walk(md.toc_tokens)
    _attach_bodies(content, flat)
    _attach_children(flat)
    return flat


def _attach_bodies(content: str, headings: list[Heading]) -> None:
    """Split the Markdown at ATX headings and give each heading its text."""
    bodies, current, fence = [], None, False
    for line in content.split("\n"):
        if _FENCE_RE.match(line.strip()):
            fence = not fence
        if not fence and re.match(r"#{1,6} ", line):
            if current is not None:
                bodies.append("\n".join(current))
            current = []
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        bodies.append("\n".join(current))
    # Setext headings or headings inside HTML make the counts differ; then
    # fall back to no bodies rather than attaching text to the wrong heading.
    if len(bodies) == len(headings):
        for heading, body in zip(headings, bodies):
            heading.body = body


def _attach_children(headings: list[Heading]) -> None:
    stack: list[Heading] = []
    for heading in headings:
        while stack and stack[-1].level >= heading.level:
            stack.pop()
        if stack:
            stack[-1].children.append(heading)
        stack.append(heading)


def spec_sections(headings: list[Heading]) -> list[Heading]:
    """Return the headings below the Specification section, if any."""
    for i, heading in enumerate(headings):
        if normalize(heading.title) == "specification":
            end = next(
                (j for j in range(i + 1, len(headings)) if headings[j].level <= heading.level),
                len(headings),
            )
            return headings[i + 1 : end]
    return []


def _title_index(parent: list[Heading]) -> dict[tuple, Heading]:
    """Index parent headings by their title path below Specification."""
    index = {}
    sections = spec_sections(parent)
    if not sections:
        return index
    top = sections[0].level
    stack: list[Heading] = []
    for heading in sections:
        while stack and stack[-1].level >= heading.level:
            stack.pop()
        stack.append(heading)
        if heading.level >= top:
            key = tuple(normalize(h.title) for h in stack)
            index.setdefault(key, heading)
    return index


def map_patch(patch_content: str, parent_headings: list[Heading]) -> list[Match]:
    """Return the patch sections that point at a parent section."""
    by_id = {h.id: h for h in parent_headings}
    by_number = {h.number: h for h in parent_headings if h.number}
    titles = _title_index(parent_headings)
    patch = parse_headings(patch_content)
    matches: list[Match] = []
    seen: set[tuple[str, str]] = set()

    patch_by_id = {h.id: h for h in patch}

    def add(patch_id, parent, how):
        if parent and (patch_id, parent.id) not in seen:
            seen.add((patch_id, parent.id))
            matches.append(
                Match(patch_id, parent.id, how, patch_by_id[patch_id].name, parent.name)
            )

    # 1. Explicit links and § references. A reference only counts when the
    # text says it is to the parent: a link to ../README.md, or "parent §".
    for heading in patch:
        for anchor in PARENT_LINK_RE.findall(heading.body):
            add(heading.id, by_id.get(anchor), "link")
        for ref in SECTION_REF_RE.findall(heading.body):
            add(heading.id, by_number.get(ref), "section")

    # 2. Title paths below Specification.
    sections = spec_sections(patch)
    if sections:
        top = sections[0].level
        stack: list[Heading] = []
        for heading in sections:
            while stack and stack[-1].level >= heading.level:
                stack.pop()
            stack.append(heading)
            if heading.level < top:
                continue
            key = tuple(normalize(h.title) for h in stack)
            if any(m.patch_id == heading.id for m in matches):
                continue
            add(heading.id, titles.get(key), "title")

    matched = {m.patch_id for m in matches}
    for m in matches:
        m.leaf = not any(d.id in matched for d in _descendants(patch_by_id[m.patch_id]))
    return matches


def _descendants(heading: Heading):
    for child in heading.children:
        yield child
        yield from _descendants(child)


def unmatched_sections(patch_content: str, matches: list[Match]) -> list[Heading]:
    """Return the Specification sections of a patch that touch no parent section.

    A section is covered when it, a section above it, or a section below it
    matches; a new subsection of a matched section is new content, not a gap.
    Only the highest uncovered section of each branch is returned.
    """
    matched = {m.patch_id for m in matches}

    def covered_below(heading):
        return heading.id in matched or any(covered_below(c) for c in heading.children)

    result = []

    def visit(heading):
        if heading.id in matched:
            return
        if not covered_below(heading):
            result.append(heading)
            return
        for child in heading.children:
            visit(child)

    sections = spec_sections(parse_headings(patch_content))
    if sections:
        top = min(h.level for h in sections)
        for heading in sections:
            if heading.level == top:
                visit(heading)
    return result


def amendment_name(content: str) -> str:
    """Return the amendment a patch says it belongs to, or "" if it names none.

    Patches state it in prose: "Under the `fixCleanup3_4_0` amendment, ...",
    "introduced by the `LendingProtocolV1_1` amendment", or "The
    `fixCleanup3_1_3` amendment makes ...".
    """
    match = re.search(
        r"(?:[Uu]nder|introduced by)\s+(?:the\s+)?`(\w+)`|\b[Tt]he\s+`(\w+)`\s+amendment\b",
        content,
    )
    return (match.group(1) or match.group(2)) if match else ""
