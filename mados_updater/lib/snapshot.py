"""Differential file-based updater for madOS.

Instead of replacing the entire @ subvolume, this applies a manifest
of files that changed, preserving user-installed apps and configs.
"""

import os
import subprocess
import tempfile
import shutil
import json
import hashlib
import tarfile
import urllib.request

from dataclasses import dataclass
from typing import Callable


@dataclass
class FileEntry:
    path: str
    checksum: str
    size: int
    is_dir: bool = False
    is_symlink: bool = False
    target: str = ""


@dataclass
class Manifest:
    version: str
    files: list[FileEntry]
    total_size: int


class UpdateApplyError(Exception):
    pass


class DifferentialUpdater:
    PRESERVE_DIRS = ["/home", "/var/cache/pacman", "/var/log", "/var/tmp"]
    EXCLUDE_PATTERNS = [".git", ".svn", "__pycache__", "*.pyc"]

    def __init__(self, root_part: str | None = None):
        self.root_part = root_part or self._detect_root_part()
        self.temp_dir = None
        self.progress_callback: Callable[[str, int], None] | None = None

    def _detect_root_part(self) -> str:
        try:
            result = subprocess.run(
                ["findmnt", "-n", "-o", "SOURCE", "/"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "/dev/sda2"

    def _report(self, message: str, percent: int):
        if self.progress_callback:
            self.progress_callback(message, percent)

    def create_local_snapshot(self, description: str) -> int | None:
        cmd = [
            "snapper",
            "create",
            "-t",
            "single",
            "-c",
            "root",
            "-p",
        ]
        if description:
            cmd.extend(["-d", description])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            import re

            match = re.search(r"Created snapshot (\d+)", output)
            if match:
                return int(match.group(1))
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error creating local snapshot: {e.stderr}")
            return None

    def download_manifest(self, github_client, version: str) -> Manifest | None:
        try:
            manifest_url = f"{github_client._get_release_url().replace('releases.json', '')}manifest-{version}.json"
            self._report("Descargando manifiesto...", 5)

            with urllib.request.urlopen(manifest_url, timeout=60) as resp:
                data = json.loads(resp.read().decode())

            files = []
            for entry in data.get("files", []):
                files.append(
                    FileEntry(
                        path=entry["path"],
                        checksum=entry["checksum"],
                        size=entry.get("size", 0),
                        is_dir=entry.get("is_dir", False),
                        is_symlink=entry.get("is_symlink", False),
                        target=entry.get("target", ""),
                    )
                )

            return Manifest(
                version=data.get("version", version),
                files=files,
                total_size=data.get("total_size", 0),
            )

        except Exception as e:
            print(f"Error downloading manifest: {e}")
            return None

    def download_update(
        self,
        github_client,
        version: str,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> str | None:
        self.progress_callback = progress_callback
        self.temp_dir = tempfile.mkdtemp(prefix="mados-update-")
        update_dir = os.path.join(self.temp_dir, "update")
        os.makedirs(update_dir)

        manifest = self.download_manifest(github_client, version)
        if not manifest:
            return None

        manifest_path = os.path.join(update_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(
                {
                    "version": manifest.version,
                    "files": [
                        {
                            "path": fe.path,
                            "checksum": fe.checksum,
                            "size": fe.size,
                            "is_dir": fe.is_dir,
                            "is_symlink": fe.is_symlink,
                            "target": fe.target,
                        }
                        for fe in manifest.files
                    ],
                    "total_size": manifest.total_size,
                },
                f,
                indent=2,
            )

        base_url = github_client._get_release_url().replace("releases.json", "")

        downloaded = 0
        total = len(manifest.files)

        for i, file_entry in enumerate(manifest.files):
            if file_entry.is_dir:
                continue

            filename = file_entry.path.replace("/", "_").lstrip("_") + ".dat"
            file_url = f"{base_url}files/{filename}"

            dest_path = os.path.join(update_dir, filename)

            try:
                with urllib.request.urlopen(file_url, timeout=300) as resp:
                    with open(dest_path, "wb") as out:
                        while True:
                            chunk = resp.read(1048576)
                            if not chunk:
                                break
                            out.write(chunk)
            except Exception as e:
                print(f"Error downloading {file_entry.path}: {e}")
                return None

            downloaded += 1
            pct = 10 + int((downloaded / total) * 60)
            self._report(f"Descargando archivos... {downloaded}/{total}", pct)

        self._report("Descarga completa", 75)
        return self.temp_dir

    def verify_and_apply(
        self, update_dir: str, progress_callback: Callable[[str, int], None] | None = None
    ) -> bool:
        self.progress_callback = progress_callback

        manifest_path = os.path.join(update_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            print("Manifest not found")
            return False

        with open(manifest_path) as f:
            data = json.load(f)

        manifest = Manifest(
            version=data["version"],
            files=[FileEntry(**f) for f in data["files"]],
            total_size=data.get("total_size", 0),
        )

        self._report("Verificando archivos...", 78)

        for file_entry in manifest.files:
            if file_entry.is_dir:
                continue

            filename = file_entry.path.replace("/", "_").lstrip("_") + ".dat"
            file_path = os.path.join(update_dir, filename)

            if not os.path.exists(file_path):
                print(f"Missing file: {filename}")
                return False

            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(1048576), b""):
                    sha256_hash.update(chunk)

            if sha256_hash.hexdigest() != file_entry.checksum:
                print(f"Checksum mismatch for {file_entry.path}")
                return False

        self._report("Aplicando actualizaciones...", 82)

        applied = 0
        total = len(manifest.files)

        for file_entry in manifest.files:
            dest_path = os.path.join("/mnt", file_entry.lstrip("/"))

            if file_entry.is_dir:
                os.makedirs(dest_path, exist_ok=True)
            elif file_entry.is_symlink:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                if os.path.exists(dest_path) or os.path.islink(dest_path):
                    os.remove(dest_path)
                os.symlink(file_entry.target, dest_path)
            else:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                filename = file_entry.path.replace("/", "_").lstrip("_") + ".dat"
                src_path = os.path.join(update_dir, filename)

                if os.path.exists(dest_path):
                    os.remove(dest_path)
                shutil.copy2(src_path, dest_path)

            applied += 1
            pct = 82 + int((applied / total) * 15)
            self._report(f"Aplicando... {applied}/{total}", pct)

        self._report("Limpieza...", 98)

        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        self._report("Completado", 100)
        return True

    def apply_update(
        self,
        github_client,
        version: str,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> bool:
        self._report("Creando snapshot local...", 0)

        pre_snapshot = self.create_local_snapshot(description=f"pre-update-{version}")
        if pre_snapshot:
            self._report(f"Snapshot local creado: #{pre_snapshot}", 5)
        else:
            self._report("Warning: No se pudo crear snapshot local", 5)

        self._report("Descargando actualización...", 5)

        update_dir = self.download_update(github_client, version, progress_callback)
        if not update_dir:
            self._report("Error en la descarga", 100)
            return False

        success = self.verify_and_apply(update_dir, progress_callback)

        if not success:
            self._report("Error aplicando actualización", 100)
            return False

        return True


class SnapshotManager:
    def __init__(self):
        pass

    def list_local_snapshots(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["snapper", "list", "-c", "root"],
                capture_output=True,
                text=True,
                check=True,
            )
            snapshots = []
            lines = result.stdout.strip().split("\n")
            for line in lines[2:]:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6:
                    snapshots.append(
                        {
                            "number": parts[0],
                            "type": parts[1],
                            "pre_num": parts[2],
                            "date": parts[3],
                            "time": parts[4],
                            "description": parts[5] if len(parts) > 5 else "",
                        }
                    )
            return snapshots
        except subprocess.CalledProcessError:
            return []

    def rollback_to_snapshot(self, snapshot_number: int) -> bool:
        try:
            subprocess.run(
                ["snapper", "rollback", str(snapshot_number)],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error during rollback: {e.stderr}")
            return False

    def get_latest_pre_snapshot(self) -> int | None:
        snapshots = self.list_local_snapshots()
        for snap in reversed(snapshots):
            if "pre-update" in snap.get("description", "").lower():
                return int(snap["number"])
        return None
