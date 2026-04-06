"""Snapper integration for mados-updater."""

import re
import subprocess


class SnapperClient:
    SNAPSHOT_PREFIX = "pre-update"
    POST_SNAPSHOT_PREFIX = "post-update"
    CONFIG = "root"
    SUBVOLUME = "/"

    def create_snapshot(
        self, description: str | None = None, snapshot_type: str = "single"
    ) -> int | None:
        cmd = [
            "snapper",
            "create",
            "-t",
            snapshot_type,
            "-c",
            self.CONFIG,
            "-p",
        ]
        if description:
            cmd.extend(["-d", description])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            match = re.search(r"Created snapshot (\d+)", output)
            if match:
                return int(match.group(1))
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error creating snapshot: {e.stderr}")
            return None

    def create_post_snapshot(self, pre_num: int, description: str | None = None) -> int | None:
        cmd = [
            "snapper",
            "create",
            "-t",
            "post",
            "-c",
            self.CONFIG,
            "--pre-num",
            str(pre_num),
            "-p",
        ]
        if description:
            cmd.extend(["-d", description])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            match = re.search(r"Created snapshot (\d+)", output)
            if match:
                return int(match.group(1))
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error creating post-snapshot: {e.stderr}")
            return None

    def list_snapshots(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["snapper", "list", "-c", self.CONFIG],
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
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error listing snapshots: {e}")
            return []

    def get_local_snapshots(self) -> list[dict]:
        return self.list_snapshots()

    def get_latest_pre_snapshot(self) -> int | None:
        snapshots = self.list_snapshots()
        for snap in reversed(snapshots):
            if self.SNAPSHOT_PREFIX in snap.get("description", "").lower():
                return int(snap["number"])
        return None

    def get_snapshot_id(self, snapshot_number: int) -> str | None:
        try:
            result = subprocess.run(
                ["btrfs", "subvolume", "show", f"/.snapshots/{snapshot_number}/snapshot"],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.split("\n"):
                if "Object ID:" in line:
                    return line.split(":")[1].strip()
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error getting snapshot ID: {e.stderr}")
            return None

    def set_default_subvolume(self, snapshot_id: str) -> bool:
        try:
            subprocess.run(
                ["btrfs", "subvolume", "set-default", snapshot_id, self.SUBVOLUME],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error setting default subvolume: {e.stderr}")
            return False

    def rollback(self, snapshot_number: int) -> bool:
        try:
            subprocess.run(
                ["snapper", "rollback", str(snapshot_number)],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error rolling back: {e.stderr}")
            return False

    def rollback_with_default(self, snapshot_number: int) -> bool:
        snapshot_id = self.get_snapshot_id(snapshot_number)
        if not snapshot_id:
            print(f"Could not get ID for snapshot {snapshot_number}")
            return False

        rollback_ok = self.rollback(snapshot_number)
        if not rollback_ok:
            return False

        set_default_ok = self.set_default_subvolume(snapshot_id)
        if not set_default_ok:
            print(f"Warning: rollback succeeded but could not set default subvolume")

        return True

    def delete_snapshot(self, snapshot_number: int) -> bool:
        try:
            subprocess.run(
                ["snapper", "delete", str(snapshot_number)],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error deleting snapshot: {e.stderr}")
            return False

    def cleanup(self, keep: int = 1) -> bool:
        try:
            subprocess.run(
                ["snapper", "cleanup", "number"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error cleaning up snapshots: {e.stderr}")
            return False

    def disable_timeline(self) -> bool:
        try:
            subprocess.run(
                ["snapper", "set-config", "TIMELINE_CREATE=no"],
                capture_output=True,
                text=True,
                check=True,
            )
            subprocess.run(
                ["snapper", "set-config", "TIMELINE_LIMIT_HOURLY=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            subprocess.run(
                ["snapper", "set-config", "TIMELINE_LIMIT_DAILY=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            subprocess.run(
                ["snapper", "set-config", "TIMELINE_LIMIT_WEEKLY=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            subprocess.run(
                ["snapper", "set-config", "TIMELINE_LIMIT_MONTHLY=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            subprocess.run(
                ["snapper", "set-config", "TIMELINE_LIMIT_YEARLY=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error disabling timeline: {e.stderr}")
            return False

    def set_number_limit(self, limit: int = 10) -> bool:
        try:
            subprocess.run(
                ["snapper", "set-config", f"NUMBER_LIMIT={limit}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error setting number limit: {e.stderr}")
            return False
