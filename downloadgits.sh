#!/bin/bash

# Input file containing repository paths and URLs
INPUT_FILE="git_repos_with_urls.txt"

# Base directory to clone repositories into
BASE_DIR="${1:-$HOME/git}"

# Check if the input file exists
if [ ! -f "$INPUT_FILE" ]; then
  echo "Input file $INPUT_FILE does not exist."
  exit 1
fi

# Create the base directory if it does not exist
mkdir -p "$BASE_DIR"

# Read the input file and clone the repositories
while IFS=' - ' read -r repo_path repo_url; do
  if [ -n "$repo_url" ]; then
    # Determine the relative path from the base directory
    relative_path=${repo_path#"$HOME/git/"}
    clone_dir="$BASE_DIR/$relative_path"

    # Create the directory if it does not exist
    mkdir -p "$(dirname "$clone_dir")"

    # Clone the repository
    git clone "$repo_url" "$clone_dir"
  fi
done < "$INPUT_FILE"

echo "Repositories have been cloned to $BASE_DIR"
