# Rclone Google Drive Setup

Mounts Google Drive as a local directory at `~/gdrive`.

## Usage

```bash
# Run the setup script
bash setup_rclone_gdrive.sh
```

During setup you'll need to:
1. Authorize in your browser
2. Copy the verification code back to the terminal

## What It Does

1. **Installs rclone** (if not already installed)
2. **Creates mount point** at `~/gdrive`
3. **Configures Google Drive remote** named `gdrive`
4. **Creates systemd user service** for auto-mount at login
5. **Starts the mount**

## Commands

```bash
# Start/Stop/Restart
systemctl --user start rclone-gdrive.service
systemctl --user stop rclone-gdrive.service
systemctl --user restart rclone-gdrive.service

# Check status
systemctl --user status rclone-gdrive.service

# View logs
journalctl --user -u rclone-gdrive.service -f

# List drive contents (without mounting)
rclone lsd gdrive:
```

## Moving Config to Another Machine

The rclone config (`~/.config/rclone/rclone.conf`) contains your auth tokens.
Copy it to the new machine to stay logged in:

```bash
# On new machine
mkdir -p ~/.config/rclone
scp oldmachine:~/.config/rclone/rclone.conf ~/.config/rclone/
```

## Unmount

```bash
fusermount -uz ~/gdrive
# or
umount ~/gdrive
```

## Troubleshooting

**Service won't start:**
```bash
journalctl --user -u rclone-gdrive.service
```

**Reconfigure remote:**
```bash
rclone config
```

**Check if mounted:**
```bash
mount | grep gdrive
```
