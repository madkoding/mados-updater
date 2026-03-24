"""Tests for mados-updater snapper module."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

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
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "snapper", stderr="Command failed")
        result = self.snapper.create_snapshot()
        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_list_snapshots(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""# | Type   | Pre # | Date   | Hour | Description
---+--------+-------+-------+------+-----------------
0  | single |       | 03-22 | 10:00 | timeline
1  | pre    |       | 03-22 | 10:00 | pre-update-42
2  | post   |     1 | 03-22 | 10:01 | post-update-42""",
            stderr="",
        )
        snapshots = self.snapper.list_snapshots()
        self.assertEqual(len(snapshots), 3)
        self.assertEqual(snapshots[1]["number"], "1")
        self.assertEqual(snapshots[1]["type"], "pre")
        self.assertIn("pre-update", snapshots[1]["description"])

    @patch("subprocess.run")
    def test_get_latest_pre_snapshot(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""# | Type   | Pre # | Date   | Hour | Description
---+--------+-------+-------+------+-----------------
0  | single |       | 03-22 | 10:00 | timeline
1  | pre    |       | 03-22 | 10:00 | pre-update-42
2  | post   |     1 | 03-22 | 10:01 | post-update-42""",
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
