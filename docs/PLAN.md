# madOS Updater - OTA Update System

## Overview

madOS Updater is an OTA (Over-The-Air) update system for madOS that provides seamless system updates with automatic rollback capability using Btrfs snapshots.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  GitHub Releases│◄───────►│   madOS Client   │
│  (mados-updates)│  HTTPS  │   (notebooks/PC) │
└─────────────────┘         └──────────────────┘
                                    │
                                    ▼
                            ┌──────────────┐
                            │    Btrfs     │
                            │  @ (root)    │
                            │  @home       │
                            │  @snapshots  │
                            └──────────────┘
```

## Features

- **Atomic Updates**: Either the update fully succeeds or the system rolls back to the previous state
- **Btrfs Snapshots**: Pre-update snapshots enable instant rollback
- **Differential Updates**: Only changed packages are downloaded
- **User-Friendly**: System notifications + confirmation dialog before installing
- **GitHub-Based**: Leverages GitHub Releases as a free update hosting solution

## Requirements

### Server-Side

- GitHub account with repository for hosting updates
- `mados-updates` repository with releases hosted on GitHub Releases

### Client-Side (madOS)

- Btrfs filesystem for root partition
- `btrfs-progs` - Btrfs utilities
- `snapper` - Snapshot management tool
- `pacman-contrib` - Pacman utilities (for hooks)
- `curl` - HTTP client for downloading updates

## Repository Structure

### mados-updater (This Repository)

```
mados-updater/
├── docs/
│   ├── PLAN.md              # This document
│   └── ARCHITECTURE.md      # Detailed architecture
├── client/
│   ├── mados-updater        # Main CLI script
│   ├── lib/
│   │   ├── github.py        # GitHub API integration
│   │   ├── snapper.py       # Snapshot management
│   │   ├── pacman.py        # Pacman integration
│   │   └── config.py        # Configuration management
│   ├── hooks/
│   │   └── pre-update.hook  # Pacman transaction hook
│   └── systemd/
│       ├── mados-updater.service
│       └── mados-updater.timer
├── installer/
│   └── mados-installer/     # Integration with madOS installer
└── README.md
```

### mados-updates (Separate Repository - Hosts Updates)

```
mados-updates/
├── releases/
│   └── stable/
│       ├── releases.json      # Release metadata
│       └── mados-1.0.0.tar.gz  # Full system image
├── packages/                      # Pacman packages (optional)
│   ├── mados-core-1.0.0-1-x86_64.pkg.tar.zst
│   └── ...
└── README.md
```

## Update Flow

### 1. Check for Updates

The `mados-updater` client periodically checks GitHub for new releases:

```bash
# Using systemd timer (every hour by default)
mados-updater --check
```

### 2. Download Update

If a new version is available:

```bash
# Download release packages
mados-updater --download
```

### 3. Create Snapshot

Before applying the update, a Btrfs snapshot is created:

```bash
snapper create -p -t pre-update -c root
```

### 4. Install Update

Packages are installed via pacman:

```bash
pacman -U --noconfirm package1.pkg.tar.zst package2.pkg.tar.zst
```

### 5. Success/Failure Handling

- **Success**: Snapshot retained for potential rollback, user notified
- **Failure**: Automatic rollback to pre-update snapshot via `snapper rollback`

## Installation

### Server Setup

1. Create a GitHub repository named `mados-updates`
2. Configure GitHub Releases in the repository settings
3. Host release packages and metadata in the repository

### Client Setup

1. Install madOS with Btrfs root filesystem (handled by mados-installer)
2. Install `mados-updater` package:

```bash
pacman -U mados-updater-*.pkg.tar.zst
```

3. Enable the update timer:

```bash
systemctl enable --now mados-updater.timer
```

## Configuration

Configuration file: `/etc/mados-updater.conf`

```ini
[updater]
repo_url = https://github.com/madkoding/mados-updates
channel = stable
check_interval = 3600
auto_download = false
auto_install = false

[notifications]
enabled = true
use_dialog = true
```

## Snapper Configuration

The updater creates snapshots with the following naming:

- Pre-update snapshots: `pre-update-N`
- Post-update snapshots: `post-update-N` (optional)

Configuration in `/etc/snapper/configs/root`:

```
SUBVOLUME="/"
ALLOW_USERS="root"
TIMELINE_CREATE="no"
NUMBER_LIMIT="1"
NUMBER_LIMIT_IMPORTANT="1"
```

## Update Process Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        mados-updater                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. [CHECK] ─────► GitHub API: latest release               │
│         │                                                        │
│         ▼                                                        │
│  2. [DOWNLOAD] ──► Download packages from GitHub             │
│         │                                                        │
│         ▼                                                        │
│  3. [VERIFY] ────► SHA256 checksum verification              │
│         │                                                        │
│         ▼                                                        │
│  4. [SNAPSHOT] ──► snapper create -p -t pre-update           │
│         │                                                        │
│         ▼                                                        │
│  5. [INSTALL] ───► pacman -U packages...                     │
│         │                                                        │
│         ▼                                                        │
│    ┌─────────┐                                                  │
│    │ Success │──────────► 6. [NOTIFY] User: "Update complete" │
│    └─────────┘                          │                      │
│         │                                │                      │
│         ▼ (if fails)                     │                      │
│    ┌─────────┐                          │                      │
│    │  Error  │──────► 7. [ROLLBACK]     │                      │
│    └─────────┘         snapper rollback │                      │
│                                    ▼                          │
│                           [NOTIFY] User: "Update failed"     │
└─────────────────────────────────────────────────────────────┘
```

## Rollback Procedure

If an update fails or causes issues:

```bash
# List snapshots
snapper list

# Rollback to pre-update state
snapper rollback pre-update-N

# Reboot
reboot
```

## Security Considerations

1. **HTTPS**: All downloads use HTTPS
2. **Checksum Verification**: SHA256 checksums verify package integrity
3. **GitHub Releases**: Relies on GitHub's authentication and authorization
4. **Root Privileges**: Update process requires root, but snapper tracks changes

## FAQ

### Q: What happens if the system loses power during an update?

A: The system will boot into the pre-update snapshot. On next boot, Btrfs will automatically use the last known good snapshot, or the user can manually select the snapshot to boot from.

### Q: Can users opt-out of automatic updates?

A: Yes, set `auto_install = false` in the configuration file. Users will receive notifications but must manually approve updates.

### Q: How much disk space is needed for updates?

A: Minimum recommended free space: 2x the size of the packages being installed. The snapshot itself doesn't duplicate data (Btrfs copy-on-write).

### Q: Can updates be applied silently in the background?

A: Yes, with `auto_download = true` and `auto_install = true`, but this is not recommended for production systems.

## Development

### Testing Locally

```bash
# Clone repository
git clone https://github.com/madkoding/mados-updater.git
cd mados-updater

# Run tests
python3 -m unittest discover -s tests -v

# Run in demo mode (no actual changes)
DEMO_MODE=true ./client/mados-updater --check
```

## License

This project is licensed under the same license as madOS.

## Related Projects

- [madOS Installer](https://github.com/madkoding/mados-installer) - madOS installation tool
- [madOS Desktop](https://github.com/madkoding/mados-desktop) - madOS desktop environment
