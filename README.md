# madOS Updater

OTA update system for madOS with Btrfs snapshots and automatic rollback.

## Features

- **Atomic Updates** with Btrfs snapshot rollback
- **Differential Updates** via Pacman packages
- **GitHub Releases** as update hosting
- **User-friendly** notifications and confirmation dialog

## Quick Start

```bash
# Install dependencies
pacman -S btrfs-progs snapper pacman-contrib curl

# Clone and install
git clone https://github.com/madkoding/mados-updater.git
cd mados-updater
pacman -U mados-updater-*.pkg.tar.zst

# Enable automatic updates
systemctl enable --now mados-updater.timer
```

## Documentation

See [docs/PLAN.md](docs/PLAN.md) for detailed architecture and implementation plan.

## License

MIT
