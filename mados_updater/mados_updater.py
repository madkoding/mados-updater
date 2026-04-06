#!/usr/bin/env python3
"""
mados-updater - OTA update client for madOS

Usage:
    mados-updater --check          Check for updates
    mados-updater --download       Download available updates
    mados-updater --install        Install downloaded updates
    mados-updater --rollback       Rollback to previous state
    mados-updater --status         Show current status
"""

import argparse
import os
import sys
import time
import tempfile
import shutil

DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.config import UpdaterConfig, UpdaterState
from lib.github import GitHubClient
from lib.snapper import SnapperClient
from lib.pacman import PacmanClient
from lib.snapshot import DifferentialUpdater, SnapshotManager


class MadOSUpdater:
    def __init__(self, progress_callback=None):
        self.config = UpdaterConfig()
        self.state = UpdaterState()
        self.snapper = SnapperClient()
        self.pacman = PacmanClient()
        self.github = GitHubClient(
            repo_url=self.config.get("updater", "repo_url"),
            channel=self.config.get("updater", "channel", "stable"),
        )
        self.updater = DifferentialUpdater()
        self.snapshot_mgr = SnapshotManager()
        self.temp_dir = None
        self.downloaded_update_dir = None
        self.progress_callback = progress_callback

    def _report_progress(self, message: str, percent: int):
        if self.progress_callback:
            self.progress_callback(message, percent)
        else:
            print(f"[{percent}%] {message}")

    def notify(self, message: str, dialog: bool = False):
        use_dialog = self.config.get_bool("notifications", "use_dialog", True)
        if dialog and use_dialog:
            self._notify_dialog(message)
        else:
            self._notify_system(message)

    def _notify_system(self, message: str):
        os.system(f'notify-send "madOS Updater" "{message}" 2>/dev/null')

    def _notify_dialog(self, message: str):
        os.system(f'zenity --info --title="madOS Updater" --text="{message}" 2>/dev/null')

    def check(self) -> bool:
        if DEMO_MODE:
            self._report_progress("[DEMO] Checking for updates...", 0)
            self._report_progress("[DEMO] Current version: 1.0.0", 50)
            self._report_progress("[DEMO] Latest version: 1.1.0 (available)", 100)
            return True

        self._report_progress("Verificando actualizaciones...", 0)

        current_version = self.state.get_current_version()
        self._report_progress(f"Versión actual: {current_version}", 20)

        release = self.github.fetch_releases_json()

        if not release:
            self._report_progress("No se encontraron releases", 100)
            return False

        self._report_progress(f"Último release: {release.version}", 80)

        if release.version == current_version:
            self._report_progress(f"Sistema actualizado (versión {current_version})", 100)
            return False

        self._report_progress(
            f"Actualización disponible: {current_version} -> {release.version}", 100
        )
        return True

    def download(self) -> bool:
        if DEMO_MODE:
            self._report_progress("[DEMO] Downloading manifest...", 0)
            self._report_progress("[DEMO] Downloading 150 files...", 50)
            self._report_progress("[DEMO] Download complete", 100)
            return True

        release = self.github.fetch_releases_json()
        if not release:
            self._report_progress("No hay información del release disponible", 100)
            return False

        version = release.version

        def progress_cb(message: str, pct: int):
            self._report_progress(message, pct)

        self.updater.progress_callback = progress_cb

        self._report_progress("Descargando actualización...", 0)

        update_dir = self.updater.download_update(self.github, version, progress_cb)

        if not update_dir:
            self._report_progress("Error en la descarga", 100)
            return False

        self.downloaded_update_dir = update_dir
        self._report_progress("Descarga completa", 100)
        return True

    def install(self) -> bool:
        if DEMO_MODE:
            self._report_progress("[DEMO] Creando snapshot local...", 0)
            time.sleep(0.5)
            self._report_progress("[DEMO] Aplicando archivos...", 40)
            time.sleep(0.5)
            self._report_progress("[DEMO] Verificando...", 80)
            time.sleep(0.3)
            self._report_progress("[DEMO] Completado", 100)
            return True

        if not self.downloaded_update_dir:
            release = self.github.fetch_releases_json()
            version = release.version if release else "unknown"

            def progress_cb(message: str, pct: int):
                self._report_progress(message, pct)

            self.updater.progress_callback = progress_cb

            self._report_progress("Descargando actualización...", 0)
            update_dir = self.updater.download_update(self.github, version, progress_cb)

            if not update_dir:
                self._report_progress("Error en la descarga", 100)
                return False

            self.downloaded_update_dir = update_dir

        release = self.github.fetch_releases_json()
        version = release.version if release else "unknown"

        self._report_progress("Creando snapshot local del sistema actual...", 0)
        pre_snapshot = self.snapper.create_snapshot(description=f"pre-update-{version}")
        if pre_snapshot:
            self._report_progress(f"Snapshot local creado: #{pre_snapshot}", 5)
        else:
            self._report_progress("Warning: No se pudo crear snapshot local", 5)

        self._report_progress("Aplicando actualización diferencial...", 10)

        def progress_cb(message: str, pct: int):
            adjusted_pct = 10 + int(pct * 0.85)
            self._report_progress(message, adjusted_pct)

        success = self.updater.verify_and_apply(self.downloaded_update_dir, progress_cb)

        if not success:
            self._report_progress(
                "Error aplicando actualización. Puede restaurar desde snapshot.",
                100,
            )
            return False

        if release:
            self.state.set_current_version(release.version)

        self._report_progress("Actualización aplicada correctamente", 100)
        self._notify_system(f"madOS actualizado a {version}.")
        return True

    def rollback(self, snapshot_number: int = None) -> bool:
        if DEMO_MODE:
            self._report_progress("[DEMO] Rolling back to snapshot...", 0)
            self._report_progress("[DEMO] Please reboot", 100)
            return True

        if snapshot_number is None:
            snapshot_number = self.snapper.get_latest_pre_snapshot()

        if not snapshot_number:
            self._report_progress("No se encontró snapshot pre-update", 100)
            return False

        self._report_progress(f"Restaurando snapshot #{snapshot_number}...", 0)

        if self.snapper.rollback_with_default(snapshot_number):
            self._report_progress("Restauración completada. Reinicie.", 100)
            self._notify_system(
                f"Sistema restaurado al snapshot #{snapshot_number}. Reinicie para aplicar."
            )
            return True

        self._report_progress("Error en la restauración", 100)
        return False

    def status(self):
        current_version = self.state.get_current_version()
        print(f"Versión actual: {current_version}")
        print(f"Repo URL: {self.config.get('updater', 'repo_url')}")
        print(f"Canal: {self.config.get('updater', 'channel')}")

        snapshots = self.snapshot_mgr.list_local_snapshots()
        print(f"\nSnapshots locales ({len(snapshots)}):")
        for snap in snapshots[-10:]:
            print(
                f"  #{snap['number']} - {snap['type']} - {snap['date']} {snap['time']} - {snap['description']}"
            )

    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        if self.downloaded_update_dir and os.path.exists(self.downloaded_update_dir):
            shutil.rmtree(self.downloaded_update_dir, ignore_errors=True)

    def get_available_update(self) -> tuple[str, str] | None:
        release = self.github.fetch_releases_json()
        if not release:
            return None
        current_version = self.state.get_current_version()
        if release.version != current_version:
            return (current_version, release.version)
        return None


def main():
    parser = argparse.ArgumentParser(description="madOS OTA Updater")
    parser.add_argument("--check", action="store_true", help="Check for available updates")
    parser.add_argument("--download", action="store_true", help="Download available updates")
    parser.add_argument("--install", action="store_true", help="Install downloaded updates")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous state")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument(
        "--snapshot",
        type=int,
        default=None,
        help="Specify snapshot number for rollback",
    )

    args = parser.parse_args()

    updater = MadOSUpdater()

    try:
        if args.check:
            success = updater.check()
            sys.exit(0 if success else 1)
        elif args.download:
            success = updater.download()
            sys.exit(0 if success else 1)
        elif args.install:
            success = updater.install()
            sys.exit(0 if success else 1)
        elif args.rollback:
            success = updater.rollback(args.snapshot)
            sys.exit(0 if success else 1)
        elif args.status:
            updater.status()
            sys.exit(0)
        else:
            parser.print_help()
            sys.exit(1)
    finally:
        updater.cleanup()


if __name__ == "__main__":
    main()
