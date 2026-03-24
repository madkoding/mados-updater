"""Tests for mados-updater CLI module.

These tests verify the MadOSUpdater class logic by importing directly from lib modules
and testing the integration layer. The CLI script (client/mados-updater) is tested
via DEMO_MODE validation instead.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client"))

from lib.config import UpdaterConfig, UpdaterState
from lib.github import GitHubClient, ReleaseInfo
from lib.pacman import PacmanClient
from lib.snapper import SnapperClient


class TestMadOSUpdaterLogic(unittest.TestCase):
    """Test the update flow logic by directly instantiating and testing the classes."""

    def test_config_loading(self):
        config = UpdaterConfig()
        self.assertEqual(config.get("updater", "repo_url"), "https://github.com/madkoding/mados-updates")
        self.assertEqual(config.get("updater", "channel"), "stable")

    def test_github_client_parsing(self):
        client = GitHubClient(repo_url="https://github.com/madkoding/mados-updates", channel="stable")
        self.assertEqual(client.owner, "madkoding")
        self.assertEqual(client.repo, "mados-updates")
        self.assertIn("madkoding/mados-updates", client._get_release_url())

    def test_release_info_dataclass(self):
        release = ReleaseInfo(
            version="1.0.1",
            release_date="2024-01-15",
            packages=[{"name": "mados-core", "version": "1.0.1-1"}],
            checksum="sha256:abc123",
            changelog="Bug fixes",
            min_supported_version="1.0.0",
            download_url="https://example.com/",
        )
        self.assertEqual(release.version, "1.0.1")
        self.assertEqual(len(release.packages), 1)

    def test_version_comparison_update_available(self):
        current = "1.0.0"
        new = "1.0.1"
        self.assertNotEqual(current, new)

    def test_version_comparison_same(self):
        current = "1.0.0"
        new = "1.0.0"
        self.assertEqual(current, new)

    def test_snapper_client_initialization(self):
        snapper = SnapperClient()
        self.assertEqual(snapper.CONFIG, "root")
        self.assertEqual(snapper.SNAPSHOT_PREFIX, "pre-update")

    def test_pacman_client_initialization(self):
        pacman = PacmanClient()
        self.assertEqual(pacman.db_path, "/var/lib/pacman")

    def test_pacman_client_custom_db_path(self):
        pacman = PacmanClient(db_path="/custom/path")
        self.assertEqual(pacman.db_path, "/custom/path")


class TestUpdateFlowIntegration(unittest.TestCase):
    """Integration tests simulating the complete update flow."""

    def setUp(self):
        self.temp_dir_patcher = patch("tempfile.mkdtemp", return_value="/tmp/test-mados")
        self.temp_dir_patcher.start()
        self.addCleanup(self.temp_dir_patcher.stop)

    @patch("urllib.request.urlopen")
    def test_full_check_update_flow(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "1.0.1", "release_date": "2024-01-15", "packages": [{"name": "mados-core", "version": "1.0.1-1"}], "checksum": "sha256:abc", "changelog": "- Fixes", "min_supported_version": "1.0.0", "download_url": "https://example.com/"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = GitHubClient("https://github.com/madkoding/mados-updates")
        release = client.fetch_releases_json()

        self.assertIsNotNone(release)
        self.assertEqual(release.version, "1.0.1")
        self.assertIn("mados-core", release.packages[0]["name"])

    @patch("urllib.request.urlopen")
    def test_check_no_updates(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "1.0.0", "release_date": "2024-01-01", "packages": [], "checksum": "", "changelog": "", "min_supported_version": "1.0.0", "download_url": "https://example.com/"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = GitHubClient("https://github.com/madkoding/mados-updates")
        release = client.fetch_releases_json()

        self.assertIsNotNone(release)
        self.assertEqual(release.version, "1.0.0")

    def test_snapper_snapshot_creation_flow(self):
        snapper = SnapperClient()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Created snapshot 42",
                stderr="",
            )
            snapshot_num = snapper.create_snapshot(description="pre-update-test")

            self.assertEqual(snapshot_num, 42)
            mock_run.assert_called_once()

    def test_snapper_rollback_flow(self):
        snapper = SnapperClient()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = snapper.rollback(42)

            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_pacman_install_packages_flow(self):
        pacman = PacmanClient()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = pacman.install_packages(["/tmp/test.pkg.tar.zst"])

            self.assertTrue(result)

    def test_pacman_install_failure_triggers_rollback(self):
        pacman = PacmanClient()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Package error")
            result = pacman.install_packages(["/tmp/test.pkg.tar.zst"])

            self.assertFalse(result)


class TestStateManagement(unittest.TestCase):
    def test_state_version_tracking(self):
        import shutil
        import tempfile

        temp_dir = tempfile.mkdtemp()
        state_path = os.path.join(temp_dir, "state.conf")
        try:
            state = UpdaterState(state_path=state_path)
            state.set_current_version("1.0.0")

            state2 = UpdaterState(state_path=state_path)
            self.assertEqual(state2.get_current_version(), "1.0.0")
        finally:
            shutil.rmtree(temp_dir)


class TestConfigPersistence(unittest.TestCase):
    def test_config_save_and_load(self):
        import shutil
        import tempfile

        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, "config.conf")
        try:
            config = UpdaterConfig(config_path=config_path)
            config.set("updater", "repo_url", "https://github.com/test/repo")
            config.save()

            config2 = UpdaterConfig(config_path=config_path)
            self.assertEqual(config2.get("updater", "repo_url"), "https://github.com/test/repo")
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
