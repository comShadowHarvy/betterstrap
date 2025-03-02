#!/bin/bash

# Directory to search for Git repositories
SEARCH_DIR="${1:-$HOME/git}"

# Output file
OUTPUT_FILE="git_repos_with_urls.txt"

# Check if the directory exists
if [ ! -d "$SEARCH_DIR" ]; then
  echo "Directory $SEARCH_DIR does not exist."
  exit 1
fi

# Find all Git repositories and save to output file with URLs
find "$SEARCH_DIR" -type d -name ".git" | while read -r gitdir; do
  repo_path=$(dirname "$gitdir")
  repo_url=$(git -C "$repo_path" config --get remote.origin.url)
  echo "$repo_path - $repo_url" >> "$OUTPUT_FILE"
done

echo "List of Git repositories with URLs has been saved to $OUTPUT_FILE"
