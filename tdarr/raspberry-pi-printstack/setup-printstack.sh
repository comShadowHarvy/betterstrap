#!/bin/bash
# Raspberry Pi Klipper + Tdarr Docker Stack Setup
# Complete installation and configuration script
set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
INSTALL_DIR="/srv/printstack"
USER_NAME="${SUDO_USER:-$(whoami)}"
USER_HOME="/home/${USER_NAME}"
HOSTNAME=$(hostname)
PI_IP=$(hostname -I | awk '{print $1}' | tr -d ' ')

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

# Check if running as root for some operations
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "This script should be run as a regular user (will use sudo when needed)"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    print_header "Installing system dependencies..."
    
    sudo apt update
    
    # Install required packages
    PACKAGES=(
        "curl"
        "git" 
        "samba"
        "samba-common-bin"
        "avahi-daemon"
        "usbutils"
    )
    
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_status "Installing $package..."
            sudo apt install -y "$package"
        else
            print_status "$package already installed"
        fi
    done
}

# Install Docker if not present
install_docker() {
    print_header "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_status "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        
        # Add user to docker group
        sudo usermod -aG docker "${USER_NAME}"
        print_warning "Added ${USER_NAME} to docker group. You may need to log out and back in."
    else
        print_status "Docker already installed"
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_status "Installing Docker Compose..."
        sudo apt install -y docker-compose-plugin
    else
        print_status "Docker Compose already installed"
    fi
}

# Create directory structure
create_directories() {
    print_header "Creating directory structure..."
    
    sudo mkdir -p "${INSTALL_DIR}"/{config/{klipper,moonraker,tdarr},data/{gcodes,timelapse,tdarr/{server,configs,logs,temp}},scripts,logs}
    
    # Set ownership to user
    sudo chown -R "${USER_NAME}:${USER_NAME}" "${INSTALL_DIR}"
    
    # Set permissions for Samba access
    chmod -R 755 "${INSTALL_DIR}"
    chmod -R 775 "${INSTALL_DIR}/data"
    
    print_status "Directory structure created at ${INSTALL_DIR}"
}

# Create Docker Compose files
create_compose_files() {
    print_header "Creating Docker Compose files..."
    
    # Klipper stack
    cat > "${INSTALL_DIR}/klipper-compose.yml" << 'EOF'
version: '3.8'

services:
  klipper:
    image: mkuf/klipper:latest
    container_name: klipper
    restart: unless-stopped
    privileged: true
    volumes:
      - /dev:/dev
      - ./config/klipper:/opt/printer_data/config
      - ./logs:/opt/printer_data/logs
      - ./data/gcodes:/opt/printer_data/gcodes
      - ./data/timelapse:/opt/printer_data/timelapse
      - run:/opt/printer_data/comms
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'

  moonraker:
    image: mkuf/moonraker:latest
    container_name: moonraker
    restart: unless-stopped
    depends_on:
      - klipper
    volumes:
      - ./config/moonraker:/opt/printer_data/config
      - ./logs:/opt/printer_data/logs
      - ./data/gcodes:/opt/printer_data/gcodes
      - ./data/timelapse:/opt/printer_data/timelapse
      - database:/opt/printer_data/database
      - run:/opt/printer_data/comms
    ports:
      - "7125:7125"
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'

  mainsail:
    image: ghcr.io/mainsail-crew/mainsail:latest
    container_name: mainsail
    restart: unless-stopped
    depends_on:
      - moonraker
    ports:
      - "80:80"
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'

  ustreamer:
    image: mkuf/ustreamer:latest
    container_name: camera
    restart: unless-stopped
    devices:
      - /dev/video0:/dev/video0
    ports:
      - "8080:8080"
    volumes:
      - ./data/timelapse:/opt/timelapse
    environment:
      - USTREAMER_DEVICE=/dev/video0
      - USTREAMER_RESOLUTION=1280x720
      - USTREAMER_FRAMERATE=15
      - USTREAMER_FORMAT=MJPEG
      - USTREAMER_QUALITY=80
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'

  samba:
    image: dperson/samba:latest
    container_name: printer-samba
    restart: unless-stopped
    ports:
      - "445:445"
      - "139:139"
    volumes:
      - ./config/klipper:/shares/printer-config
      - ./data/gcodes:/shares/printer-gcodes
      - ./data/timelapse:/shares/printer-timelapse
    environment:
      - USERID=1000
      - GROUPID=1000
    command: >
      -s "Printer-Config;/shares/printer-config;yes;no;no;all;none;none;Klipper Configuration Files" 
      -s "Printer-GCodes;/shares/printer-gcodes;yes;no;no;all;none;none;G-Code Files" 
      -s "Printer-Timelapse;/shares/printer-timelapse;yes;no;no;all;none;none;Timelapse Videos"
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'

volumes:
  run:
  database:
EOF

    # Tdarr stack - node-only to match betterstrap/tdarr/install_node.sh
    cat > "${INSTALL_DIR}/tdarr-compose.yml" << 'EOF'
version: '3.8'

services:
  # Standalone Tdarr node - connects to an existing Tdarr server.
  # Adjust serverIP/serverPort if needed. These defaults mirror betterstrap's script.
  tdarr-node:
    image: haveagitgat/tdarr_node:latest
    container_name: tdarr-node
    restart: unless-stopped
    environment:
      - TZ=America/New_York
      - PUID=1000
      - PGID=1000
      - UMASK_SET=002
      - serverIP=192.168.1.210
      - serverPort=8266
      - nodeName=${HOSTNAME}-node
      - internalNode=true
      - inContainer=true
      - LIBVA_DRIVER_NAME=iHD
    volumes:
      - /share:/media
      - /share/trans:/tmp
      - ./config/tdarr:/app/configs
      - ./logs:/app/logs
    devices:
      - /dev/dri:/dev/dri
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '3.0'
EOF
EOF

    print_status "Docker Compose files created"
}

# Create configuration files
create_config_files() {
    print_header "Creating configuration files..."
    
    # Basic printer.cfg template
    cat > "${INSTALL_DIR}/config/klipper/printer.cfg" << 'EOF'
# Klipper Configuration - EDIT THIS FILE FOR YOUR PRINTER
# This is a basic template - you MUST customize it for your specific printer

[mcu]
# CHANGE THIS: Find your printer's serial port with: ls /dev/serial/by-id/
serial: /dev/serial/by-id/usb-CHANGE_ME

[printer]
kinematics: cartesian  # Change to: cartesian, corexy, delta, etc.
max_velocity: 300
max_accel: 3000
max_z_velocity: 5
max_z_accel: 100

# EXAMPLE STEPPER CONFIGS - CUSTOMIZE FOR YOUR PRINTER
[stepper_x]
step_pin: ar54
dir_pin: ar55
enable_pin: !ar38
microsteps: 16
rotation_distance: 40
endstop_pin: ^ar3
position_endstop: 0
position_max: 200
homing_speed: 50

[stepper_y]
step_pin: ar60
dir_pin: ar61
enable_pin: !ar56
microsteps: 16
rotation_distance: 40
endstop_pin: ^ar14
position_endstop: 0
position_max: 200
homing_speed: 50

[stepper_z]
step_pin: ar46
dir_pin: ar48
enable_pin: !ar62
microsteps: 16
rotation_distance: 8
endstop_pin: ^ar18
position_endstop: 0.5
position_max: 200

[extruder]
step_pin: ar26
dir_pin: ar28
enable_pin: !ar24
microsteps: 16
rotation_distance: 33.500
nozzle_diameter: 0.400
filament_diameter: 1.750
heater_pin: ar10
sensor_type: EPCOS 100K B57560G104F
sensor_pin: analog13
control: pid
pid_Kp: 22.2
pid_Ki: 1.08
pid_Kd: 114
min_temp: 0
max_temp: 250

[heater_bed]
heater_pin: ar8
sensor_type: EPCOS 100K B57560G104F
sensor_pin: analog14
control: watermark
min_temp: 0
max_temp: 130

[fan]
pin: ar9

# Camera configuration for timelapse
[gcode_macro TIMELAPSE_TAKE_FRAME]
gcode:
    {action_call_remote_method("timelapse_take_frame")}

[gcode_macro TIMELAPSE_RENDER]
gcode:
    {action_call_remote_method("timelapse_render")}

# Include Mainsail macros
[include mainsail.cfg]

# ADD YOUR PRINTER-SPECIFIC CONFIGURATION BELOW
# Remove the example configs above and add your actual pin mappings
EOF

    # Moonraker configuration
    cat > "${INSTALL_DIR}/config/moonraker/moonraker.conf" << 'EOF'
[server]
host: 0.0.0.0
port: 7125
klippy_uds_address: /opt/printer_data/comms/klippy.sock

[file_manager]
enable_object_processing: True

[authorization]
trusted_clients:
    10.0.0.0/8
    127.0.0.0/8
    169.254.0.0/16
    172.16.0.0/12
    192.168.0.0/16
    FE80::/10
    ::1/128

cors_domains:
    *.lan
    *.local
    *://localhost
    *://localhost:*
    *://my.mainsail.xyz
    *://app.fluidd.xyz

[octoprint_compat]

[history]

[timelapse]
output_path: /opt/printer_data/timelapse/
frame_path: /tmp/timelapse/
ffmpeg_binary_path: /usr/bin/ffmpeg

[webcam camera]
location: printer
service: ustreamer
target_fps: 15
stream_url: http://127.0.0.1:8080/stream
snapshot_url: http://127.0.0.1:8080/snapshot

[spoolman]
server: http://127.0.0.1:7912
sync_rate: 5
EOF

    # Create mainsail.cfg for required macros
    cat > "${INSTALL_DIR}/config/klipper/mainsail.cfg" << 'EOF'
# Mainsail klipper definitions
[virtual_sdcard]
path: /opt/printer_data/gcodes
on_error_gcode: CANCEL_PRINT

[pause_resume]

[display_status]

[gcode_macro CANCEL_PRINT]
description: Cancel the actual running print
rename_existing: CANCEL_PRINT_BASE
gcode:
    TURN_OFF_HEATERS
    CANCEL_PRINT_BASE

[gcode_macro PAUSE]
description: Pause the actual running print
rename_existing: PAUSE_BASE
gcode:
    PAUSE_BASE
    G91
    G1 E-1 F300
    G1 Z10
    G90

[gcode_macro RESUME]
description: Resume the actual running print
rename_existing: RESUME_BASE
gcode:
    G91
    G1 E1 F300
    G90
    RESUME_BASE
EOF

    # Create Tdarr node configuration matching betterstrap setup
    cat > "${INSTALL_DIR}/config/tdarr/Tdarr_Node_Config.json" << 'EOF'
{
  "nodeName": "HOSTNAME-node",
  "serverURL": "http://192.168.1.210:8266",
  "nodeType": "mapped",
  "priority": 0,
  "handbrakePath": "",
  "ffmpegPath": "",
  "mkvpropeditPath": "",
  "pathTranslators": [
    {
      "server": "/share",
      "node": "/media"
    }
  ],
  "maxLogSizeMB": 10,
  "pollInterval": 2000,
  "startPaused": false
}
EOF

    # Replace HOSTNAME placeholder with actual hostname
    sed -i "s/HOSTNAME/${HOSTNAME}/g" "${INSTALL_DIR}/config/tdarr/Tdarr_Node_Config.json"

    print_status "Configuration files created"
}

# Create management scripts
create_scripts() {
    print_header "Creating management scripts..."
    
    # Start printing script
    cat > "${INSTALL_DIR}/scripts/start-printing.sh" << 'EOF'
#!/bin/bash
set -euo pipefail

cd /srv/printstack

echo "Setting up permissions for Samba access..."
sudo chmod -R 775 data/gcodes data/timelapse config/klipper

echo "Stopping Tdarr services..."
docker compose -f tdarr-compose.yml down 2>/dev/null || true
sleep 3

echo "Starting Klipper stack..."
docker compose -f klipper-compose.yml up -d

PI_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "✅ Klipper stack started successfully!"
echo ""
echo "🌐 Web interfaces:"
echo "   Mainsail:     http://${PI_IP}"
echo "   Camera:       http://${PI_IP}:8080"
echo "   Moonraker:    http://${PI_IP}:7125"
echo ""
echo "📁 Network shares:"
echo "   Config:       \\\\${PI_IP}\\Printer-Config"
echo "   G-codes:      \\\\${PI_IP}\\Printer-GCodes"  
echo "   Timelapse:    \\\\${PI_IP}\\Printer-Timelapse"
echo ""
echo "ℹ️  Edit /srv/printstack/config/klipper/printer.cfg for your printer"
EOF

    # Start transcoding script
    cat > "${INSTALL_DIR}/scripts/start-transcoding.sh" << 'EOF'
#!/bin/bash
set -euo pipefail

cd /srv/printstack

# Configuration (adjust these if your server is different)
SERVER_IP="192.168.1.210"
SERVER_PORT="8266"
SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"

echo "Stopping Klipper services..."
docker compose -f klipper-compose.yml down 2>/dev/null || true
sleep 3

# Verify share paths exist
echo "📁 Checking required paths..."
if [ ! -d "/share" ]; then
  echo "❌ /share directory does not exist!"
  echo "   Please ensure your SMB shares are mounted first."
  exit 1
fi

if [ ! -d "/share/trans" ]; then
  echo "🔧 Creating /share/trans directory for temporary files..."
  mkdir -p "/share/trans"
fi

echo "✅ Share paths verified"

# Test server connection
echo "🔗 Testing connection to Tdarr server at $SERVER_URL..."
if timeout 10 bash -c "</dev/tcp/$SERVER_IP/$SERVER_PORT" 2>/dev/null; then
  echo "✅ Successfully connected to Tdarr server at $SERVER_IP:$SERVER_PORT"
else
  echo "⚠️  Warning: Could not connect to Tdarr server at $SERVER_IP:$SERVER_PORT"
  echo "   Please ensure the server is running and accessible."
  echo "   You can still proceed with starting the node."
fi

echo "🚀 Starting Tdarr Node..."
docker compose -f tdarr-compose.yml up -d

# Wait for container to initialize
echo "⏳ Waiting for container to initialize..."
sleep 10

# Check container status
if docker ps --format '{{.Names}}' | grep -q "^tdarr-node$"; then
  echo "✅ Tdarr Node started successfully!"
else
  echo "❌ Container failed to start. Checking logs..."
  docker logs tdarr-node --tail 20
  exit 1
fi

PI_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "📋 Tdarr Node Configuration:"
echo "   Node Name: ${HOSTNAME}-node"
echo "   Server URL: $SERVER_URL"
echo "   Share Path: /share → /media (in container)"
echo "   Temp Path: /share/trans → /tmp (in container)"
echo ""
echo "🔧 Management Commands:"
echo "   Status:  docker ps | grep tdarr-node"
echo "   Logs:    docker logs tdarr-node -f"
echo "   Stop:    docker stop tdarr-node"
echo ""
echo "✅ Node should be connecting to server at $SERVER_URL"
echo "   Check your main Tdarr server web interface to verify the node connection."
EOF

    # Stop all services script
    cat > "${INSTALL_DIR}/scripts/stop-all.sh" << 'EOF'
#!/bin/bash
set -euo pipefail

cd /srv/printstack

echo "Stopping all services..."
docker compose -f klipper-compose.yml down 2>/dev/null || true
docker compose -f tdarr-compose.yml down 2>/dev/null || true

echo "✅ All services stopped"
echo ""
echo "To clean up unused containers and volumes:"
echo "   docker system prune -f"
echo "   docker volume prune -f"
EOF

    # Status check script
    cat > "${INSTALL_DIR}/scripts/status.sh" << 'EOF'
#!/bin/bash
set -euo pipefail

cd /srv/printstack

echo "🔍 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "💾 Disk Usage:"
df -h /srv/printstack
echo ""
echo "📁 Share Status:"
if [ -d "/share" ]; then
  echo "   /share: ✅ $(df -h /share | tail -1 | awk '{print $4" available"}')"
else
  echo "   /share: ❌ Not mounted"
fi

if [ -d "/share/trans" ]; then
  echo "   /share/trans: ✅ $(ls -la /share/trans | wc -l) items"
else
  echo "   /share/trans: ❌ Not found"
fi

echo ""
PI_IP=$(hostname -I | awk '{print $1}')
echo "🌐 Local Service URLs:"
echo "   Mainsail:     http://${PI_IP} (if running)"
echo "   Camera:       http://${PI_IP}:8080 (if running)"
echo ""
echo "🔗 Tdarr Node connects to: http://192.168.1.210:8266"
echo "   (Check your main Tdarr server to see this node)"
EOF

    # Make scripts executable
    chmod +x "${INSTALL_DIR}/scripts/"*.sh
    
    # Create symlinks in user's path
    sudo ln -sf "${INSTALL_DIR}/scripts/start-printing.sh" /usr/local/bin/start-printing
    sudo ln -sf "${INSTALL_DIR}/scripts/start-transcoding.sh" /usr/local/bin/start-transcoding
    sudo ln -sf "${INSTALL_DIR}/scripts/stop-all.sh" /usr/local/bin/stop-printstack
    sudo ln -sf "${INSTALL_DIR}/scripts/status.sh" /usr/local/bin/printstack-status
    
    print_status "Management scripts created and linked to system PATH"
}

# Create systemd services for auto-start
create_systemd_services() {
    print_header "Creating systemd services..."
    
    # Klipper service
    sudo tee /etc/systemd/system/printstack-klipper.service > /dev/null << EOF
[Unit]
Description=Printstack Klipper Services
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=${USER_NAME}
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/docker compose -f klipper-compose.yml up -d
ExecStop=/usr/bin/docker compose -f klipper-compose.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

    # Tdarr service (disabled by default)
    sudo tee /etc/systemd/system/printstack-tdarr.service > /dev/null << EOF
[Unit]
Description=Printstack Tdarr Services
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=${USER_NAME}
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/docker compose -f tdarr-compose.yml up -d
ExecStop=/usr/bin/docker compose -f tdarr-compose.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    
    print_status "Systemd services created (not enabled by default)"
}

# Create documentation
create_documentation() {
    print_header "Creating documentation..."
    
    cat > "${INSTALL_DIR}/README.md" << EOF
# Raspberry Pi Klipper + Tdarr Docker Stack

## Quick Start

### Start Printing Mode
\`\`\`bash
start-printing
# or: cd /srv/printstack && ./scripts/start-printing.sh
\`\`\`

### Start Transcoding Mode  
\`\`\`bash
start-transcoding
# or: cd /srv/printstack && ./scripts/start-transcoding.sh
\`\`\`

### Stop All Services
\`\`\`bash
stop-printstack
# or: cd /srv/printstack && ./scripts/stop-all.sh
\`\`\`

### Check Status
\`\`\`bash
printstack-status
# or: cd /srv/printstack && ./scripts/status.sh
\`\`\`

## Web Interfaces

- **Mainsail (Klipper)**: http://${PI_IP}
- **Camera Stream**: http://${PI_IP}:8080
- **Tdarr Server**: http://192.168.1.210:8265 (on your main server)

**Note**: This Pi runs a Tdarr NODE that connects to your existing Tdarr server at 192.168.1.210.

## Network Shares (Guest Access)

- **Config**: \\\\\\\\${PI_IP}\\\\Printer-Config
- **G-codes**: \\\\\\\\${PI_IP}\\\\Printer-GCodes
- **Timelapse**: \\\\\\\\${PI_IP}\\\\Printer-Timelapse

## Configuration

### Printer Setup
1. Edit \`config/klipper/printer.cfg\` with your printer's specifications
2. Find your printer's serial port: \`ls /dev/serial/by-id/\`
3. Update the \`[mcu]\` section with your serial port
4. Restart Klipper: \`start-printing\`

### Camera Setup
- Camera is configured for \`/dev/video0\`
- To use a different camera, edit \`klipper-compose.yml\`
- Change the device mapping: \`- /dev/video1:/dev/video0\`

## Directory Structure

\`\`\`
/srv/printstack/
├── config/
│   ├── klipper/           # Klipper configuration files
│   ├── moonraker/         # Moonraker configuration  
│   └── tdarr/            # Tdarr configuration
├── data/
│   ├── gcodes/           # G-code files
│   ├── timelapse/        # Timelapse videos
│   └── tdarr/            # Tdarr working files
├── logs/                 # Service logs
├── scripts/              # Management scripts
├── klipper-compose.yml   # Klipper stack definition
└── tdarr-compose.yml     # Tdarr stack definition
\`\`\`

## Updates

\`\`\`bash
cd /srv/printstack
docker compose -f klipper-compose.yml pull
docker compose -f tdarr-compose.yml pull
start-printing  # or start-transcoding
\`\`\`

## Auto-start on Boot

\`\`\`bash
# Enable Klipper auto-start
sudo systemctl enable printstack-klipper

# Enable Tdarr auto-start (optional)
sudo systemctl enable printstack-tdarr
\`\`\`

## Troubleshooting

### View Logs
\`\`\`bash
docker logs klipper
docker logs moonraker
docker logs tdarr
\`\`\`

### Check Container Status
\`\`\`bash
docker ps
printstack-status
\`\`\`

### Reset Everything
\`\`\`bash
stop-printstack
docker system prune -f
start-printing
\`\`\`

## Uninstall

\`\`\`bash
# Stop services
stop-printstack

# Remove systemd services
sudo systemctl disable --now printstack-klipper printstack-tdarr
sudo rm /etc/systemd/system/printstack-*.service
sudo systemctl daemon-reload

# Remove installation
sudo rm -rf /srv/printstack
sudo rm /usr/local/bin/{start-printing,start-transcoding,stop-printstack,printstack-status}
\`\`\`

## Support

- **Klipper**: https://www.klipper3d.org/
- **Moonraker**: https://moonraker.readthedocs.io/
- **Tdarr**: https://docs.tdarr.io/
- **Docker**: https://docs.docker.com/

Generated by setup-printstack.sh on $(date)
EOF

    print_status "Documentation created at ${INSTALL_DIR}/README.md"
}

# Main installation function
main() {
    print_header "Raspberry Pi Klipper + Tdarr Node Docker Stack Setup"
    echo "This will install and configure:"
    echo "  • Klipper 3D printer firmware"
    echo "  • Moonraker API server"  
    echo "  • Mainsail web interface"
    echo "  • Camera streaming"
    echo "  • Tdarr transcoding NODE (connects to existing server)"
    echo "  • Samba file shares (guest access)"
    echo "  • /share directory access for media transcoding"
    echo ""
    
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi
    
    check_root
    install_dependencies
    install_docker
    create_directories
    create_compose_files
    create_config_files
    create_scripts
    create_systemd_services
    create_documentation
    
    print_header "Installation completed successfully! 🎉"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Edit /srv/printstack/config/klipper/printer.cfg for your printer"
    echo "   2. Connect your printer via USB"
    echo "   3. Connect camera to /dev/video0"
    echo "   4. Run: start-printing"
    echo ""
    echo "🌐 Access points:"
    echo "   Mainsail:  http://${PI_IP}"
    echo "   Camera:    http://${PI_IP}:8080"
    echo "   Tdarr:     http://192.168.1.210:8265 (your main server)"
    echo ""
    echo "📁 Network shares: \\\\${PI_IP}\\Printer-Config"
    echo "                  \\\\${PI_IP}\\Printer-GCodes" 
    echo "                  \\\\${PI_IP}\\Printer-Timelapse"
    echo ""
    
    read -p "Would you like to start the printing stack now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting Klipper stack..."
        cd "${INSTALL_DIR}"
        ./scripts/start-printing.sh
    fi
}

# Run main function
main "$@"