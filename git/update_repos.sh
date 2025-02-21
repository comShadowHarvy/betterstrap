#!/bin/bash
# ----------------------------------------------------------------------
# Script: Update Repos Script
# Author: ShadowHarvy
# Description: Iterates through the ~/git directory and pulls the latest
#              changes for each detected git repository.
# ----------------------------------------------------------------------
clear
echo "****************************************"
echo "*         Update Repos Script          *"
echo "*    Pulls latest changes for each repo*"
echo "*            in ~/git directory        *"
echo "*                                      *"
echo "*            ShadowHarvy               *"
echo "****************************************"
sleep 5

REPO_DIR=~/git

for d in "$REPO_DIR"/*; do
    if [ -d "$d/.git" ]; then
         echo "Updating $(basename "$d")..."
         git -C "$d" pull
    fi
done
