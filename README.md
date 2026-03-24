# madOS Updater

OTA update system for madOS with Btrfs snapshots and automatic rollback.

## Features

- **Atomic Updates** with Btrfs snapshot rollback
- **Differential Updates** via Pacman packages
- **GitHub Releases** as update hosting
- **User-friendly** notifications and confirmation dialog

## Overview

madOS Updater provides seamless system updates with automatic rollback capability. Using Btrfs copy-on-write snapshots, the system can instantly revert to a pre-update state if anything goes wrong.

```mermaid
graph LR
    A[GitHub Releases] -->|HTTPS| B[mados-updater Client]
    B --> C[Btrfs Snapshots]
    B --> D[Pacman Packages]
    C -->|Rollback| E[System Restore]
    D -->|Install| F[Updated System]
```

## Architecture

```mermaid
graph TB
    subgraph "Server Side"
        A[GitHub Releases<br/>mados-updates repo]
        A -->|releases.json| B[Release Metadata]
        A -->|*.pkg.tar.zst| C[Packages]
    end
    
    subgraph "Client Side"
        D[mados-updater] --> E[GitHub Client]
        D --> F[Snapper Client]
        D --> G[Pacman Client]
        E -->|Fetch| B
        F -->|Create/Rollback| H[Btrfs @snapshots]
        G -->|Install| I[Btrfs @ root]
    end
```

## Update Flow

```mermaid
sequenceDiagram
    participant User
    participant Client as mados-updater
    participant GitHub
    participant Snapper
    participant Pacman

    User->>Client: --check
    Client->>GitHub: Fetch releases.json
    GitHub-->>Client: Version info
    Client-->>User: Update available?

    User->>Client: --download
    Client->>GitHub: Download packages
    GitHub-->>Client: *.pkg.tar.zst
    Client->>Client: Verify checksums
    Client-->>User: Download complete

    User->>Client: --install
    Client->>Snapper: Create pre-update snapshot
    Snapper-->>Client: Snapshot #N
    Client->>Pacman: pacman -U *.pkg.tar.zst
    Pacman-->>Client: Install complete
    
    alt Success
        Client-->>User: Update successful!
    else Failure
        Client->>Snapper: snapper rollback #N
        Snapper-->>Client: Rollback done
        Client-->>User: Update failed - rolled back
    end
```

## Update Process States

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Checking: --check
    Checking --> Idle: No update
    Checking --> Downloading: Update found
    Downloading --> Downloaded: Packages ready
    Downloaded --> Installing: --install
    Installing --> SnapshotCreated: Snapshot OK
    SnapshotCreated --> InstallingPackages: pacman -U
    InstallingPackages --> Success: Install OK
    InstallingPackages --> RollingBack: Install failed
    RollingBack --> Failed: Rollback done
    Success --> Idle
    Failed --> Idle
```

## Requirements

### Server-Side

- GitHub account with `mados-updates` repository
- GitHub Releases enabled for hosting packages

### Client-Side

- Btrfs root filesystem (`/`)
- `btrfs-progs` - Btrfs utilities
- `snapper` - Snapshot management
- `pacman-contrib` - Pacman hooks support
- `curl` - HTTP client

## Installation

### System Dependencies

```bash
# Install dependencies
pacman -S btrfs-progs snapper pacman-contrib curl
```

### Development Dependencies

```bash
# Install Python development tools (for testing/linting)
pip install pytest pytest-cov ruff mypy --break-system-packages
```

### Install madOS Updater

```bash
# Clone and install
git clone https://github.com/madkoding/mados-updater.git
cd mados-updater
pacman -U mados-updater-*.pkg.tar.zst

# Enable automatic updates (checks hourly)
systemctl enable --now mados-updater.timer
```

## Usage

```bash
# Check for updates
mados-updater --check

# Download available updates
mados-updater --download

# Install downloaded updates
mados-updater --install

# Rollback to previous state
mados-updater --rollback

# Show current status
mados-updater --status

# Rollback to specific snapshot
mados-updater --rollback --snapshot 42
```

## Configuration

Edit `/etc/mados-updater.conf`:

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

| Option | Default | Description |
|--------|---------|-------------|
| `repo_url` | - | GitHub repository URL for updates |
| `channel` | stable | Release channel (stable/beta) |
| `check_interval` | 3600 | Seconds between update checks |
| `auto_download` | false | Automatically download updates |
| `auto_install` | false | Automatically install after download |
| `use_dialog` | true | Use zenity dialogs instead of notifications |

## Snapper Configuration

Ensure `/etc/snapper/configs/root` has:

```
SUBVOLUME="/"
ALLOW_USERS="root"
TIMELINE_CREATE="no"
NUMBER_LIMIT="1"
NUMBER_LIMIT_IMPORTANT="1"
```

## Release Metadata

The `releases.json` file structure:

```json
{
  "version": "1.0.1",
  "release_date": "2024-01-15",
  "min_supported_version": "1.0.0",
  "changelog": "- Bug fixes\n- Performance improvements",
  "checksum": "sha256-checksum-of-packages",
  "download_url": "https://github.com/...",
  "packages": [
    {"name": "mados-core", "version": "1.0.1-1"},
    {"name": "mados-desktop", "version": "1.0.1-1"}
  ]
}
```

## Security

- **HTTPS**: All downloads use encrypted connections
- **SHA256 Checksums**: Package integrity verification
- **GitHub Releases**: Relies on GitHub's authentication
- **Root Privileges**: Required for system modifications, tracked by snapper

## FAQ

### What happens if power is lost during an update?

The system will boot into the pre-update snapshot. Btrfs ensures all changes are atomic, and snapper provides a clean rollback path.

### How much disk space is needed?

Minimum 2x the size of packages being installed. Btrfs copy-on-write means snapshots don't duplicate data initially.

### Can I opt out of automatic updates?

Yes. Set `auto_install = false` in the configuration. You'll receive notifications but must manually approve updates.

## Demo Mode

Run without making actual changes:

```bash
DEMO_MODE=true mados-updater --check
DEMO_MODE=true mados-updater --download
DEMO_MODE=true mados-updater --install
```

## Testing

This project uses a comprehensive testing infrastructure with pytest, ruff, and mypy.

### Quick Start

```bash
# Run all tests with coverage
python3 -m pytest tests/ -v --cov=client --cov-report=term-missing

# Run only unit tests (no coverage)
python3 -m pytest tests/ -v
```

### Development Commands

```bash
# Lint code (ruff)
ruff check client/ tests/

# Auto-fix lint issues
ruff check client/ tests/ --fix

# Type checking (mypy)
mypy client/ --ignore-missing-imports

# Full verification (lint + typecheck + tests)
ruff check client/ tests/ && mypy client/ --ignore-missing-imports && python3 -m pytest tests/
```

### Pre-commit Hook

A pre-commit hook runs automatically before each commit to validate code quality:

```bash
# The hook is located at .git/hooks/pre-commit
# It runs: ruff check → mypy → pytest
git commit -m "Your commit message"
```

To manually run the pre-commit checks:
```bash
.git/hooks/pre-commit
```

### Test Coverage

Current coverage: **87%+** across all modules.

| Module | Coverage |
|--------|----------|
| `client/lib/__init__.py` | 100% |
| `client/lib/config.py` | 95% |
| `client/lib/github.py` | 96% |
| `client/lib/pacman.py` | 84% |
| `client/lib/snapper.py` | 71% |

### Demo Mode

Test the update flow without making actual system changes:

```bash
DEMO_MODE=true mados-updater --check
DEMO_MODE=true mados-updater --download
DEMO_MODE=true mados-updater --install
DEMO_MODE=true mados-updater --rollback
DEMO_MODE=true mados-updater --status
```

## Documentation

See [docs/PLAN.md](docs/PLAN.md) for detailed architecture and implementation plan.

## Related Projects

- [madOS Installer](https://github.com/madkoding/mados-installer) - madOS installation tool
- [madOS Desktop](https://github.com/madkoding/mados-desktop) - madOS desktop environment

## License

MIT
