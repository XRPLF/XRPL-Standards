"""Tests for assign_xls_number.py.

Run: python -m unittest discover -s .github/scripts -p 'test_*.py'
"""

import tempfile
import unittest
from pathlib import Path

import assign_xls_number as m


def bot(body: str) -> dict:
    return {"user": {"login": m.BOT_LOGIN}, "body": body}


class TestAssignXlsNumber(unittest.TestCase):
    def test_marker_matches_digits_from_bot_only(self):
        comments = [
            bot("x <!-- XLS_NUMBER:101 --> y"),
            {"user": {"login": "someone"}, "body": "<!-- XLS_NUMBER:200 -->"},
            {"user": None, "body": "<!-- XLS_NUMBER:300 -->"},
        ]
        self.assertEqual(m.numbers_in_comments(comments), {101})

    def test_next_number_skips_used_and_manual_range(self):
        self.assertEqual(m.get_next_xls_number(set()), 96)
        self.assertEqual(m.get_next_xls_number({1, 50, 95}), 96)
        self.assertEqual(m.get_next_xls_number({96, 97, 99}), 98)

    def test_existing_numbers_reads_directories_only(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ["XLS-0001-a", "XLS-0102-b", "XLS-draft-c", "scripts"]:
                (Path(d) / name).mkdir()
            (Path(d) / "XLS-0200-file").touch()
            self.assertEqual(m.get_existing_xls_numbers(Path(d)), {1, 102})

    def test_find_draft_dirs_rejects_unsafe_names(self):
        files = [
            "XLS-draft-foo/README.md",
            "xls-draft-bar/README.md",
            "XLS-draft-foo/extra.md",
            "XLS-0100-x/README.md",
            "XLS-draft-$(evil)/README.md",
            "XLS-draft-a`b`/README.md",
        ]
        self.assertEqual(m.find_draft_dirs(files), ["XLS-draft-foo", "xls-draft-bar"])

    def test_find_self_assigned(self):
        files = [
            "XLS-0095-old/README.md",
            "XLS-0150-new/README.md",
            "xls-0151-y/README.md",
        ]
        self.assertEqual(
            m.find_self_assigned(files), [("XLS-0150-new", 150), ("xls-0151-y", 151)]
        )

    def test_rename(self):
        self.assertEqual(
            m.numbered_dir_name("XLS-draft-My-Feature", 103), "XLS-0103-My-Feature"
        )
        self.assertEqual(m.numbered_dir_name("xls-draft-foo", 7), "XLS-0007-foo")

    def test_plan_reuses_own_reservation(self):
        result = m.plan_assignments(["XLS-draft-a"], {96, 97}, {120})
        self.assertEqual(result, [("XLS-draft-a", 120, "XLS-0120-a")])

    def test_plan_multiple_drafts_get_distinct_numbers(self):
        result = m.plan_assignments(["XLS-draft-a", "XLS-draft-b"], {96, 98}, set())
        self.assertEqual([n for _, n, _ in result], [97, 99])

    def test_assignment_comment_round_trips_markers(self):
        body = m.assignment_comment(
            [("XLS-draft-a", 97, "XLS-0097-a"), ("XLS-draft-b", 98, "XLS-0098-b")]
        )
        self.assertEqual(m.numbers_in_comments([bot(body)]), {97, 98})


if __name__ == "__main__":
    unittest.main()
