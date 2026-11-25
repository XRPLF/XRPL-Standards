"""Tests for the site generator. Run: python -m unittest discover -s scripts"""

import tempfile
import unittest
from pathlib import Path

from build_site import (
    LinkResolver,
    SiteBuilder,
    author_links,
    convert_markdown_to_html,
    page_path,
    strip_title_heading,
)
from patch_map import amendment_name, map_patch, parse_headings, unmatched_sections
from validate_xls_template import XLSTemplateValidator
from xls_parser import extract_xls_metadata, find_xls_documents, parse_author

PREAMBLE = """<pre>
  xls: 65
  title: Single Asset Vault
  description: A vault.
  author: Ada Lovelace <ada@example.com>, Bob (@bob)
  category: Amendment
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/1
  created: 2024-01-01
  requires: XLS-33, 64
</pre>
"""


class ParserTest(unittest.TestCase):
    def test_preamble(self):
        doc = extract_xls_metadata(PREAMBLE, "XLS-0065-single-asset-vault")
        self.assertEqual(doc.number, "0065")
        self.assertEqual(doc.raw_number, 65)
        self.assertEqual(doc.title, "Single Asset Vault")
        self.assertEqual(
            doc.authors,
            [("Ada Lovelace", "mailto:ada@example.com"), ("Bob", "https://github.com/bob")],
        )
        self.assertEqual(doc.requires, "XLS-33, 64")
        self.assertIsNone(doc.updated)

    def test_missing_preamble_raises(self):
        with self.assertRaises(ValueError):
            extract_xls_metadata("# No preamble", "XLS-0001-x")

    def test_author_without_link(self):
        self.assertEqual(parse_author(" Satoshi "), ("Satoshi", ""))

    def test_author_links_escape(self):
        doc = extract_xls_metadata(PREAMBLE, "XLS-0065-x")
        doc.authors = [("A<b>", "https://x.y/?a&b"), ("Plain", "")]
        self.assertEqual(
            str(author_links(doc)),
            '<a href="https://x.y/?a&amp;b">A&lt;b&gt;</a>, Plain',
        )


class LinkResolverTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "repo"
        self.site = Path(tmp.name) / "site"
        (self.root / "XLS-0066-lending").mkdir(parents=True)
        (self.root / "XLS-0066-lending/diagram.svg").write_text("<svg/>")
        (self.root / "XLS-0066-lending/notes.md").write_text("notes")
        pages = {
            "XLS-0065-vault/README.md": "xls/XLS-0065-vault.html",
            "XLS-0066-lending/README.md": "xls/XLS-0066-lending.html",
            "CONTRIBUTING.md": "contribute.html",
        }
        self.resolver = LinkResolver(pages, self.root, self.site)

    def resolve(self, url, source="XLS-0066-lending/README.md", page="xls/XLS-0066-lending.html"):
        return self.resolver.resolve(url, source, page)

    def test_cross_spec_link_keeps_fragment(self):
        self.assertEqual(self.resolve("../XLS-0065-vault/README.md#312-fields"), "XLS-0065-vault.html#312-fields")

    def test_link_from_root_page(self):
        self.assertEqual(
            self.resolve("./XLS-0065-vault/README.md", "CONTRIBUTING.md", "contribute.html"),
            "xls/XLS-0065-vault.html",
        )
        self.assertEqual(
            self.resolve("XLS-0065-vault/README.md", "XLS-0066-lending/README.md", "contribute.html"),
            "https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0066-lending/XLS-0065-vault/README.md",
        )

    def test_image_is_copied(self):
        self.assertEqual(self.resolve("./diagram.svg"), "XLS-0066-lending/diagram.svg")
        self.assertTrue((self.site / "xls/XLS-0066-lending/diagram.svg").is_file())

    def test_unrendered_markdown_goes_to_github(self):
        self.assertEqual(
            self.resolve("./notes.md#a"),
            "https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0066-lending/notes.md#a",
        )

    def test_absolute_and_anchor_links_unchanged(self):
        for url in ("https://xrpl.org", "#section", "mailto:a@b.c", "/x"):
            self.assertEqual(self.resolve(url), url)

    def test_markdown_conversion_rewrites_links(self):
        html, toc = convert_markdown_to_html(
            PREAMBLE + "# T\n\n## 1. A\n\nSee [vault](../XLS-0065-vault/README.md) and ![d](./diagram.svg).",
            self.resolver,
            "XLS-0066-lending/README.md",
            "xls/XLS-0066-lending.html",
        )
        self.assertIn('href="XLS-0065-vault.html"', html)
        self.assertIn('src="XLS-0066-lending/diagram.svg"', html)
        self.assertNotIn("<pre>", html)
        self.assertIn('href="#1-a"', toc)


class AlertTest(unittest.TestCase):
    def test_github_alert(self):
        resolver = LinkResolver({}, Path("."), Path("."))
        html, _ = convert_markdown_to_html("> [!WARNING]\n> Be careful.", resolver, "a.md", "a.html")
        self.assertIn('<div class="alert warning">', html)
        self.assertIn('<p class="alert-title">Warning</p>', html)
        self.assertNotIn("[!WARNING]", html)


class TitleHeadingTest(unittest.TestCase):
    def test_strips_matching_title(self):
        self.assertEqual(strip_title_heading("# Single Asset Vault\n\n## 1", "Single Asset Vault"), "\n## 1")

    def test_keeps_other_heading(self):
        text = "# Abstract\n\nText"
        self.assertEqual(strip_title_heading(text, "Tagged Addresses"), text)


def preamble(xls, title):
    return PREAMBLE.replace("xls: 65", f"xls: {xls}").replace(
        "title: Single Asset Vault", f"title: {title}"
    )


PARENT = preamble(65, "Vault") + """
# Vault

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.2 Fields

#### 3.1.10 Invariants

### 3.4 Transaction: `VaultDelete`

#### 3.4.2 Failure Conditions

##### 3.4.2.1 Data Verification
"""

INDEX = preamble("65.1", "V1_1 Changes") + """
This index groups the changes introduced by the `LendingProtocolV1_1` amendment.
"""

PATCH = preamble("65.1.2", "Memo") + """
## 3. Specification

### 3.1 Transaction: `VaultDelete`

#### 3.1.2 Failure Conditions

##### 3.1.2.1 Data Verification

Parent check 1 is unchanged.

### 3.2 Ledger Entry: `Vault`

Add a field to parent [§3.1.2](../README.md#312-fields). See parent §3.1.10.

### 3.3 Protocol Constants

New.

[parent](../README.md)
"""


class PatchTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        folder = self.root / "XLS-0065-vault"
        (folder / "65.1-lending-protocol-v1_1").mkdir(parents=True)
        (folder / "65.2-fix-cleanup-3_4_0").mkdir()
        (folder / "README.md").write_text(PARENT)
        (folder / "65.1-lending-protocol-v1_1/README.md").write_text(INDEX)
        (folder / "65.1-lending-protocol-v1_1/65.1.2-memo.md").write_text(PATCH)
        (folder / "65.1-lending-protocol-v1_1/65.1.10-later.md").write_text(preamble("65.1.10", "Later"))
        (folder / "65.2-fix-cleanup-3_4_0/README.md").write_text(
            preamble("65.2", "Fix") + "Under the `fixCleanup3_4_0` amendment, x."
        )

    def test_discovery_and_order(self):
        (doc,) = find_xls_documents(self.root)
        self.assertEqual([p.xls for p in doc.patches], ["65.1", "65.1.2", "65.1.10", "65.2"])
        self.assertEqual(doc.patches[1].source, "XLS-0065-vault/65.1-lending-protocol-v1_1/65.1.2-memo.md")

    def test_page_paths(self):
        (doc,) = find_xls_documents(self.root)
        self.assertEqual(page_path(doc), "xls/XLS-0065-vault.html")
        self.assertEqual(page_path(doc.patches[0]), "xls/XLS-0065-vault/65.1-lending-protocol-v1_1/index.html")
        self.assertEqual(page_path(doc.patches[1]), "xls/XLS-0065-vault/65.1-lending-protocol-v1_1/65.1.2-memo.html")

    def test_mapping(self):
        matches = map_patch(PATCH, parse_headings(PARENT))
        found = {(m.patch_id, m.parent_id, m.how) for m in matches if m.leaf}
        self.assertEqual(
            found,
            {
                ("3121-data-verification", "3421-data-verification", "title"),
                ("32-ledger-entry-vault", "312-fields", "link"),
                ("32-ledger-entry-vault", "3110-invariants", "section"),
            },
        )
        self.assertEqual(
            [h.name for h in unmatched_sections(PATCH, matches)], ["3.3 Protocol Constants"]
        )

    def test_amendment_name(self):
        self.assertEqual(amendment_name(INDEX), "LendingProtocolV1_1")
        self.assertEqual(amendment_name(PATCH), "")

    def test_build(self):
        site = self.root / "_site"
        (self.root / "CONTRIBUTING.md").write_text("# Contributing")
        SiteBuilder(self.root, site).build()
        parent = (site / "xls/XLS-0065-vault.html").read_text()
        patch = (site / "xls/XLS-0065-vault/65.1-lending-protocol-v1_1/65.1.2-memo.html").read_text()
        self.assertIn('href="XLS-0065-vault/65.1-lending-protocol-v1_1/65.1.2-memo.html#3121-data-verification"', parent)
        self.assertIn('data-amendment="LendingProtocolV1_1"', parent)
        self.assertIn('href="../../XLS-0065-vault.html#3421-data-verification"', patch)
        self.assertIn('href="../../XLS-0065-vault.html">parent</a>', patch)
        self.assertIn("XLS-0065-vault/65.1-lending-protocol-v1_1/65.1.2-memo.html", (site / "xls/xls-65.1.2.html").read_text())


class PatchFolderTest(unittest.TestCase):
    def folder_errors(self, folder_name):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name) / "XLS-0065-vault" / folder_name
        folder.mkdir(parents=True)
        (folder.parent / "README.md").write_text(PARENT)
        path = folder / "65.1.2-memo.md"
        path.write_text(preamble("65.1.2", "Memo"))
        validator = XLSTemplateValidator(path)
        validator.validate()
        return [e.message for e in validator.errors if "Patch folder" in e.message]

    def test_named_folder_passes(self):
        self.assertEqual(self.folder_errors("65.1-lending-protocol-v1_1"), [])

    def test_bare_number_fails(self):
        self.assertEqual(len(self.folder_errors("65.1")), 1)

    def test_wrong_number_fails(self):
        self.assertEqual(len(self.folder_errors("65.2-lending-protocol-v1_1")), 1)


if __name__ == "__main__":
    unittest.main()
