#!/bin/bash
set -e

# Function to create systemd service file
create_systemd_service() {
  echo "Creating systemd service file at /etc/systemd/system/tdarr.service ..."
  sudo bash -c 'cat > /etc/systemd/system/tdarr.service << "EOF"
[Unit]
Description=Tdarr Media Processing Service
After=network.target

[Service]
Type=simple
WorkingDirectory='"$HOME"'/Tdarr
ExecStart=/usr/bin/npm run start
Restart=on-failure
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF'
  echo "Reloading systemd daemon..."
  sudo systemctl daemon-reload
  echo "Enabling and starting Tdarr service..."
  sudo systemctl enable tdarr.service
  sudo systemctl start tdarr.service
  echo "Tdarr systemd service created and started."
}

echo "Updating system and installing dependencies..."
sudo pacman -Syu --noconfirm
sudo pacman -S --noconfirm git nodejs npm ffmpeg

echo "Cloning Tdarr repository..."
if [ ! -d "$HOME/Tdarr" ]; then
  git clone https://github.com/HaveAGitGat/Tdarr.git "$HOME/Tdarr"
else
  echo "Directory $HOME/Tdarr already exists, skipping clone."
fi

echo "Installing Node.js dependencies..."
cd "$HOME/Tdarr"
npm install

echo "Starting Tdarr (in the background)..."
nohup npm run start > ~/tdarr.log 2>&1 &

echo "Tdarr is starting up in the background. Check ~/tdarr.log for output."

# Ask user if they want to create a systemd service
read -p "Would you like to create a systemd service for Tdarr so it starts on boot? (y/n) " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
  create_systemd_service
else
  echo "Skipping systemd service creation. You can create one later if desired."
fi

echo "Installation complete."
