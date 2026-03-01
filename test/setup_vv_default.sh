#!/bin/bash
set -e

INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local}"

mkdir -p "$INSTALL_DIR/share/applications"
mkdir -p "$INSTALL_DIR/share/mime/packages"

cat > "$INSTALL_DIR/share/applications/vv.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=vv
Comment=Terminal Image Viewer
Exec=vv %f
Terminal=true
MimeType=image/png;image/jpeg;image/gif;image/bmp;image/tiff;image/webp;image/svg+xml;image/x-icon;image/heic;image/heif;
Icon=image-x-generic
Categories=Graphics;Viewer;
NoDisplay=false
EOF

cat > "$INSTALL_DIR/share/mime/packages/vv.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="image/png"><glob pattern="*.png"/></mime-type>
  <mime-type type="image/jpeg"><glob pattern="*.jpg"/><glob pattern="*.jpeg"/></mime-type>
  <mime-type type="image/gif"><glob pattern="*.gif"/></mime-type>
  <mime-type type="image/bmp"><glob pattern="*.bmp"/></mime-type>
  <mime-type type="image/tiff"><glob pattern="*.tiff"/><glob pattern="*.tif"/></mime-type>
  <mime-type type="image/webp"><glob pattern="*.webp"/></mime-type>
  <mime-type type="image/svg+xml"><glob pattern="*.svg"/></mime-type>
  <mime-type type="image/x-icon"><glob pattern="*.ico"/></mime-type>
</mime-info>
EOF

update-mime-database "$INSTALL_DIR/share/mime"

xdg-mime default vv.desktop image/png image/jpeg image/gif image/bmp image/tiff image/webp image/svg+xml image/x-icon

echo "vv is now the default image viewer"
