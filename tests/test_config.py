"""Tests for mados-updater configuration module."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mados_updater.lib.config import UpdaterConfig, UpdaterState


class TestUpdaterConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test.conf")
        self.config = UpdaterConfig(config_path=self.config_path)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_default_values(self):
        self.assertEqual(
            self.config.get("updater", "repo_url"),
            "https://github.com/madkoding/mados-updates",
        )
        self.assertEqual(self.config.get("updater", "channel"), "stable")
        self.assertEqual(self.config.get_int("updater", "check_interval"), 3600)
        self.assertFalse(self.config.get_bool("updater", "auto_download"))
        self.assertFalse(self.config.get_bool("updater", "auto_install"))

    def test_get_set(self):
        self.config.set("updater", "repo_url", "https://example.com")
        self.assertEqual(self.config.get("updater", "repo_url"), "https://example.com")

    def test_save_and_reload(self):
        self.config.set("updater", "repo_url", "https://example.com")
        self.config.save()
        new_config = UpdaterConfig(config_path=self.config_path)
        self.assertEqual(new_config.get("updater", "repo_url"), "https://example.com")


class TestUpdaterState(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_path = os.path.join(self.temp_dir, "state.conf")
        self.state = UpdaterState(state_path=self.state_path)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_default_version(self):
        self.assertEqual(self.state.get_current_version(), "0.0.0")

    def test_set_version(self):
        self.state.set_current_version("1.0.0")
        self.assertEqual(self.state.get_current_version(), "1.0.0")

    def test_last_check_timestamp(self):
        self.state.set_last_check(1234567890)
        self.assertEqual(self.state.get_last_check(), 1234567890)


if __name__ == "__main__":
    unittest.main()
