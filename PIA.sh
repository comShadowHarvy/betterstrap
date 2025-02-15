#!/bin/bash

# Script to install and fully configure OpenVPN with PIA inside a container
# This version:
# 1. Installs OpenVPN and necessary tools.
# 2. Downloads PIA configuration files.
# 3. Creates pia-credentials.txt with provided username and password in /etc/openvpn.
# 4. Modifies the chosen .ovpn file (ca_ontario.ovpn - lowercase) to use the credentials file with absolute path.
# 5. Starts the VPN connection (using ca_ontario.ovpn configuration).
# 6. Uses lowercase filenames for consistency (ca_ontario.ovpn).

# ** IMPORTANT: SECURITY WARNING **
# This script embeds your PIA username and password in a file (pia-credentials.txt) within the container.
# This is less secure than other methods of credential management.
# Use with caution, especially in non-public network environments.
# Consider more secure methods for sensitive deployments, even in local networks.
# While the system might not be directly accessible from the internet, local network security is still important.

# --- User Configuration ---
PIA_USERNAME="username"        # Your Private Internet Access Username
PIA_PASSWORD="password"        # Your Private Internet Access Password
DEFAULT_PIA_CONFIG_FILE="ca_ontario.ovpn" # Default PIA .ovpn config to use (lowercase ca_ontario.ovpn)
PIA_CONFIG_ZIP_URL="https://www.privateinternetaccess.com/openvpn/openvpn.zip"
PIA_CONFIG_ZIP_FILE="openvpn.zip"
OUTPUT_DIR="/etc/openvpn"
CREDENTIALS_FILE="pia-credentials.txt"
CREDENTIALS_PATH="${OUTPUT_DIR}/${CREDENTIALS_FILE}"
OVPN_CONFIG_PATH="${OUTPUT_DIR}/${DEFAULT_PIA_CONFIG_FILE}"

# --- Script Execution ---

# Helper function to install packages across multiple distributions
install_packages() {
    packages=("$@")
    if command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y "${packages[@]}"
    elif command -v apk &>/dev/null; then
        apk update && apk add --no-cache "${packages[@]}"
    elif command -v pacman &>/dev/null; then
        pacman -Sy --noconfirm "${packages[@]}"
    elif command -v dnf &>/dev/null; then
        dnf install -y "${packages[@]}"
    else
        echo "Error: No supported package manager found." >&2
        exit 1
    fi
}

# Step 1: Update package list and install necessary tools and OpenVPN
echo "Step 1: Installing OpenVPN, wget, unzip, nano..."
install_packages openvpn wget unzip nano
sleep 3  # Delay added for Step 1

# Step 2: Create /etc/openvpn directory if it doesn't exist
echo "Step 2: Creating /etc/openvpn directory..."
mkdir -p /etc/openvpn
sleep 3  # Delay added for Step 2

# Step 3: Download and extract PIA configuration files
echo "Step 3: Downloading and extracting PIA configuration files..."

echo "Downloading PIA config zip file from: ${PIA_CONFIG_ZIP_URL}..."
wget "${PIA_CONFIG_ZIP_URL}" -O "${PIA_CONFIG_ZIP_FILE}"

if [ ! -f "${PIA_CONFIG_ZIP_FILE}" ]; then
  echo "Error: Failed to download PIA configuration zip file."
  exit 1
fi

echo "Extracting PIA configuration files to: ${OUTPUT_DIR}..."
unzip -o "${PIA_CONFIG_ZIP_FILE}" -d "${OUTPUT_DIR}"

if [ $? -eq 0 ]; then
  echo "Successfully extracted PIA configuration files."
  rm "${PIA_CONFIG_ZIP_FILE}"
  echo "Removed downloaded zip file: ${PIA_CONFIG_ZIP_FILE}"
else
  echo "Error: Failed to extract PIA configuration files."
  echo "Please check if 'unzip' is installed and if there were any errors during extraction."
  exit 1
fi
sleep 5  # Delay added for Step 3

# Step 4: Create credentials file
echo "Step 4: Creating credentials file: ${CREDENTIALS_PATH}..."
echo "${PIA_USERNAME}" > "${CREDENTIALS_PATH}"
echo "${PIA_PASSWORD}" >> "${CREDENTIALS_PATH}"
chmod 600 "${CREDENTIALS_PATH}" # Set permissions to read/write for owner only (important for security)
echo "Credentials file created and permissions set."
sleep 3  # Delay added for Step 4

# Step 5: Modify the .ovpn configuration file to use the credentials file (absolute path)
echo "Step 5: Modifying .ovpn configuration file: ${OVPN_CONFIG_PATH}..."
if [ ! -f "${OVPN_CONFIG_PATH}" ]; then
  echo "Error: Default PIA configuration file '${OVPN_CONFIG_PATH}' not found."
  echo "Please ensure the .ovpn file (lowercase, e.g., ca_ontario.ovpn) exists in ${OUTPUT_DIR}."
  exit 1
fi

CREDENTIALS_ABSOLUTE_PATH="/etc/openvpn/pia-credentials.txt" # Absolute path to credentials file
sed -i "s/auth-user-pass/auth-user-pass ${CREDENTIALS_ABSOLUTE_PATH}/" "${OVPN_CONFIG_PATH}"
echo ".ovpn configuration file modified to use credentials file (absolute path)."
sleep 3  # Delay added for Step 5

# Step 6: Configure startup script (optional - example provided below)
echo "Step 6: Startup script configuration (optional)..."
echo " "
echo "Optional: To automatically start the VPN when the container boots, you can create a startup script."
echo "Example startup script (you may need to adapt this based on your container environment):"
echo " "
echo "--- START of example startup script ---"
echo "#!/bin/bash"
echo "# Uses the same PIA config file as set in DEFAULT_PIA_CONFIG_FILE in the install script (lowercase)"
echo "PIA_CONFIG_FILE=\"${DEFAULT_PIA_CONFIG_FILE}\""
echo "openvpn --config /etc/openvpn/\${PIA_CONFIG_FILE} &"
echo "echo \"OpenVPN started with \${PIA_CONFIG_FILE} configuration\""
echo "--- END of example startup script ---"
echo " "
echo "You would typically save this script (e.g., 'start_vpn.sh'), make it executable (chmod +x start_vpn.sh),"
echo "and then configure your container to run this script at startup."
echo "Consult your containerization platform's documentation on how to run scripts at startup."
echo " "
sleep 7  # Longer delay for more text in Step 6

# Step 7: Start the VPN connection
echo "Step 7: Starting the OpenVPN connection..."
echo "Using configuration file: ${OVPN_CONFIG_PATH}"
sleep 3  # Delay before launching the VPN
openvpn --config "${OVPN_CONFIG_PATH}"

echo " "
echo "OpenVPN installation and FULL configuration script completed."
echo "Check the output above for any errors. The OpenVPN connection should now be active."
echo " "
echo "Important:"
echo " - This script downloads PIA configuration files to /etc/openvpn."
echo " - It is configured to use 'ca_ontario.ovpn' (lowercase) as the default configuration file."
echo " - It creates a credentials file '${CREDENTIALS_FILE}' in /etc/openvpn and modifies the .ovpn file to use it via absolute path."
echo " - **SECURITY WARNING: Credentials are stored in plaintext in the container. Even if not internet-facing, consider local network security.**"
echo " - Consider security best practices for managing VPN credentials and configurations, especially for production."