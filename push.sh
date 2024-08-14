#!/bin/bash

# Check if a commit message was provided
if [ -z "$1" ]; then
    echo "Please provide a commit message."
    exit 1
fi

# Add all changes, commit with the provided message, and push to the remote repository
git add .
git commit -m "$1"
git push
