#!/bin/bash
# ----------------------------------------------------------------------
# Script: Update Repos Script
# Author: ShadowHarvy
# Description: Iterates through the ~/git directory and pulls the latest
#              changes for each detected git repository.
# ----------------------------------------------------------------------
clear
cat << "EOF"
****************************************
*         Welcome to Update Repos      *
*  This script iterates through ~/git and*
*   pulls the latest changes for each repo*
*            Author: ShadowHarvy         *
****************************************
EOF
sleep 5

REPO_DIR=~/git

for d in "$REPO_DIR"/*; do
    if [ -d "$d/.git" ]; then
         repo=$(basename "$d")
         echo "Updating $repo..."
         git -C "$d" pull
         echo "Updated $repo."
    fi
done
