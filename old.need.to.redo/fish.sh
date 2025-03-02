#!/bin/bash

# Function to install a package if not already installed
install_package() {
    if ! command -v "$1" &> /dev/null; then
        echo "Installing $1..."
        if command -v pacman &> /dev/null; then
            sudo pacman -Sy --noconfirm "$1"
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y "$1"
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y "$1"
        elif command -v zypper &> /dev/null; then
            sudo zypper install -y "$1"
        else
            echo "Unsupported package manager. Install $1 manually."
            exit 1
        fi
    else
        echo "$1 is already installed."
    fi
}

# Function to install Fisher plugins
install_fisher_plugin() {
    fish -c "if not fisher list | grep -q '$1'; fisher install $1; end"
}

# Install fish and zsh
install_package fish
install_package zsh

# Set zsh as the default shell
if [ "$SHELL" != "$(which zsh)" ]; then
    echo "Setting zsh as the default shell..."
    chsh -s "$(which zsh)"
else
    echo "zsh is already the default shell."
fi

# Install fisher for fish shell
if command -v fish &> /dev/null; then
    echo "Installing fisher..."
    fish -c "curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher"
else
    echo "fish shell is not installed. Skipping fisher installation."
fi

# Start fish shell and ensure Fisher plugins are installed
if command -v fish &> /dev/null; then
    echo "Installing Fisher plugins..."
    install_fisher_plugin "jorgebucaran/autopair.fish"
    install_fisher_plugin "jorgebucaran/spark.fish"
    install_fisher_plugin "meaningful-ooo/sponge"
    install_fisher_plugin "decors/fish-colored-man"
    install_fisher_plugin "oakninja/MakeMeFish"
    install_fisher_plugin "ankitsumitg/docker-fish-completions"
    install_fisher_plugin "yo-goto/ggl.fish"
    install_fisher_plugin "jorgebucaran/humantime.fish"
    install_fisher_plugin "halostatue/fish-rust@v2"
    install_fisher_plugin "IlanCosman/tide@v6"
    install_fisher_plugin "franciscolourenco/done"
    install_fisher_plugin "PatrickF1/fzf.fish"
    install_fisher_plugin "joseluisq/gitnow@2.12.0"
    install_fisher_plugin "nickeb96/puffer-fish"
    install_fisher_plugin "FabioAntunes/base16-fish-shell"

    echo "Configuring Tide..."
    fish -c "tide configure --auto --style=Rainbow --prompt_colors='True color' --show_time='24-hour format' --rainbow_prompt_separators=Angled --powerline_prompt_heads=Slanted --powerline_prompt_tails=Round --powerline_prompt_style='Two lines, character and frame' --prompt_connection=Solid --powerline_right_prompt_frame=Yes --prompt_connection_andor_frame_color=Lightest --prompt_spacing=Compact --icons='Many icons' --transient=Yes"
else
    echo "fish shell is not installed. Skipping Fisher and plugin installation."
fi

# Load fish shell for the current session
exec fish
