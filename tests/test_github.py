"""Tests for mados-updater GitHub module."""

import hashlib
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client"))

from lib.github import GitHubClient, ReleaseInfo


class TestReleaseInfo(unittest.TestCase):
    def test_release_info_creation(self):
        release = ReleaseInfo(
            version="1.0.0",
            release_date="2024-01-15",
            packages=[{"name": "mados-core", "version": "1.0.0-1"}],
            checksum="abc123",
            changelog="Bug fixes",
            min_supported_version="0.9.0",
            download_url="https://example.com/",
        )
        self.assertEqual(release.version, "1.0.0")
        self.assertEqual(release.release_date, "2024-01-15")
        self.assertEqual(len(release.packages), 1)


class TestGitHubClient(unittest.TestCase):
    def setUp(self):
        self.client = GitHubClient(
            repo_url="https://github.com/madkoding/mados-updates",
            channel="stable",
        )

    def test_parse_repo_url(self):
        self.assertEqual(self.client.owner, "madkoding")
        self.assertEqual(self.client.repo, "mados-updates")

    def test_get_api_url(self):
        url = self.client._get_api_url("releases/latest")
        self.assertEqual(
            url, "https://api.github.com/repos/madkoding/mados-updates/releases/latest"
        )

    def test_get_release_url(self):
        url = self.client._get_release_url()
        self.assertEqual(
            url,
            "https://github.com/madkoding/mados-updates/releases/download/stable/releases.json",
        )

    @patch("urllib.request.urlopen")
    def test_fetch_releases_json_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "1.0.1", "release_date": "2024-01-15", "packages": [{"name": "mados-core", "version": "1.0.1-1"}], "checksum": "sha256:abc123", "changelog": "- Fixed bugs", "min_supported_version": "1.0.0", "download_url": "https://example.com/"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        release = self.client.fetch_releases_json()

        self.assertIsNotNone(release)
        self.assertEqual(release.version, "1.0.1")
        self.assertEqual(release.release_date, "2024-01-15")
        self.assertEqual(len(release.packages), 1)

    @patch("urllib.request.urlopen")
    def test_fetch_releases_json_404(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )

        release = self.client.fetch_releases_json()
        self.assertIsNone(release)

    @patch("urllib.request.urlopen")
    def test_fetch_releases_json_other_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Network error")

        release = self.client.fetch_releases_json()
        self.assertIsNone(release)

    @patch("urllib.request.urlopen")
    def test_download_file_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.side_effect = [b"test", b"data", b""]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            result = self.client.download_file("test.pkg.tar.zst", temp_path)
            self.assertTrue(result)
            with open(temp_path, "rb") as f:
                self.assertEqual(f.read(), b"testdata")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @patch("urllib.request.urlopen")
    def test_download_file_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Download failed")

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            result = self.client.download_file("test.pkg.tar.zst", temp_path)
            self.assertFalse(result)
            self.assertFalse(os.path.exists(temp_path))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_verify_checksum_success(self):
        test_content = b"test content for checksum"
        expected_checksum = hashlib.sha256(test_content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            result = self.client.verify_checksum(temp_path, expected_checksum)
            self.assertTrue(result)
        finally:
            os.remove(temp_path)

    def test_verify_checksum_failure(self):
        test_content = b"test content"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            result = self.client.verify_checksum(temp_path, "wrong_checksum")
            self.assertFalse(result)
        finally:
            os.remove(temp_path)


class TestGitHubClientLatestRelease(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_get_latest_release_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"assets": [{"name": "releases.json", "browser_download_url": "https://example.com/releases.json"}]}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with patch.object(GitHubClient, "download_file", return_value=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                releases_json_path = os.path.join(temp_dir, "releases.json")
                with open(releases_json_path, "w") as f:
                    f.write('{"version": "2.0.0", "release_date": "2024-02-01", "packages": [], "checksum": "", "changelog": "", "min_supported_version": "1.0.0", "download_url": "https://example.com/"}')

                with patch("tempfile.mkdtemp", return_value=temp_dir):
                    client = GitHubClient("https://github.com/madkoding/mados-updates")
                    client.repo_url = "https://github.com/madkoding/mados-updates"

                    result = client.get_latest_release()

                    self.assertIsNotNone(result)
                    self.assertEqual(result.version, "2.0.0")

    @patch("urllib.request.urlopen")
    def test_get_latest_release_no_json_asset(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"assets": []}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = GitHubClient("https://github.com/madkoding/mados-updates")
        result = client.get_latest_release()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
