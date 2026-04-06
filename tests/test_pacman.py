"""Tests for mados-updater pacman module."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mados_updater.lib.pacman import PacmanClient


class TestPacmanClient(unittest.TestCase):
    def setUp(self):
        self.pacman = PacmanClient()

    @patch("subprocess.run")
    def test_install_packages_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with tempfile.NamedTemporaryFile(suffix=".pkg.tar.zst", delete=False) as f:
            temp_path = f.name

        try:
            result = self.pacman.install_packages([temp_path])
            self.assertTrue(result)
            mock_run.assert_called_once()
        finally:
            os.remove(temp_path)

    @patch("subprocess.run")
    def test_install_packages_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Package corrupted")

        result = self.pacman.install_packages(["/fake/package.pkg.tar.zst"])
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_install_packages_empty(self, mock_run):
        result = self.pacman.install_packages([])
        self.assertTrue(result)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_get_installed_version_found(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="mados-core 1.0.0-1",
            stderr="",
        )

        version = self.pacman.get_installed_version("mados-core")
        self.assertEqual(version, "1.0.0-1")

    @patch("subprocess.run")
    def test_get_installed_version_not_found(self, mock_run):
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "pacman", stderr="package not found")

        version = self.pacman.get_installed_version("nonexistent")
        self.assertIsNone(version)

    @patch("subprocess.run")
    def test_sync_packages_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = self.pacman.sync_packages(refresh=True)
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_sync_packages_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Sync failed")

        result = self.pacman.sync_packages()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_get_pending_updates_with_updates(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="mados-core 1.0.0-1 1.0.1-1\nmados-desktop 1.0.0-1 1.0.1-1",
            stderr="",
        )

        updates = self.pacman.get_pending_updates()
        self.assertEqual(len(updates), 2)
        self.assertIn("mados-core", updates)
        self.assertIn("mados-desktop", updates)

    @patch("subprocess.run")
    def test_get_pending_updates_no_updates(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        updates = self.pacman.get_pending_updates()
        self.assertEqual(len(updates), 0)

    @patch("subprocess.run")
    def test_get_pending_updates_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error", stdout="")

        updates = self.pacman.get_pending_updates()
        self.assertEqual(len(updates), 0)

    def test_is_locked_true(self):
        with patch("os.path.exists", return_value=True):
            self.assertTrue(self.pacman.is_locked())

    def test_is_locked_false(self):
        with patch("os.path.exists", return_value=False):
            self.assertFalse(self.pacman.is_locked())

    def test_remove_packages(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        self.assertTrue(os.path.exists(temp_path))
        result = self.pacman.remove_packages([temp_path])
        self.assertTrue(result)
        self.assertFalse(os.path.exists(temp_path))


if __name__ == "__main__":
    unittest.main()
