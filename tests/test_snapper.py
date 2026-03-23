"""Tests for mados-updater snapper module."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client"))

from lib.snapper import SnapperClient


class TestSnapperClient(unittest.TestCase):
    def setUp(self):
        self.snapper = SnapperClient()

    @patch("subprocess.run")
    def test_create_snapshot_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Created snapshot 42",
            stderr="",
        )
        result = self.snapper.create_snapshot(description="test snapshot")
        self.assertEqual(result, 42)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_create_snapshot_failure(self, mock_run):
        mock_run.side_effect = Exception("Command failed")
        result = self.snapper.create_snapshot()
        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_list_snapshots(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""# | Type   | Pre # | Date                            | Description
--+--------+-------+----------------------------------+-----------------
0  | single |       |                                 | timeline
1  | pre    |       | Sun 22 Mar 2026 10:00:00 UTC    | pre-update-42
2  | post   |     1 | Sun 22 Mar 2026 10:01:00 UTC    | post-update-42""",
            stderr="",
        )
        snapshots = self.snapper.list_snapshots()
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(snapshots[0]["number"], "1")
        self.assertIn("pre-update", snapshots[0]["description"])

    @patch("subprocess.run")
    def test_get_latest_pre_snapshot(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""# | Type   | Pre # | Date                            | Description
--+--------+-------+----------------------------------+-----------------
1  | pre    |       | Sun 22 Mar 2026 10:00:00 UTC    | pre-update-42""",
            stderr="",
        )
        result = self.snapper.get_latest_pre_snapshot()
        self.assertEqual(result, 1)

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = self.snapper.rollback(42)
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_delete_snapshot_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = self.snapper.delete_snapshot(42)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
