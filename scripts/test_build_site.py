"""Tests for the site generator. Run: python -m unittest discover -s scripts"""

import tempfile
import unittest
from pathlib import Path

from build_site import LinkResolver, author_links, convert_markdown_to_html, strip_title_heading
from xls_parser import extract_xls_metadata, parse_author

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


if __name__ == "__main__":
    unittest.main()
