{
  description = "Modern Alternative: Reproducible Development Environment with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Development tools
            git
            curl
            wget
            
            # Languages and runtimes
            python311
            nodejs_20
            rustc
            cargo
            go
            
            # Editors
            vscode
            neovim
            
            # System tools
            tmux
            zsh
            
            # AI/ML tools
            python311Packages.torch
            python311Packages.transformers
            
            # Security tools (when needed)
            nmap
            wireshark
            
            # Container tools
            docker
            podman
          ];

          shellHook = ''
            echo "🚀 Development environment loaded!"
            echo "Available tools:"
            echo "  - Python $(python --version)"
            echo "  - Node $(node --version)"  
            echo "  - Rust $(rustc --version)"
            echo "  - Go $(go version)"
            
            # Setup git if not configured
            if ! git config user.name >/dev/null 2>&1; then
              echo "⚠️  Git not configured. Run:"
              echo "    git config --global user.name 'Your Name'"
              echo "    git config --global user.email 'your.email@example.com'"
            fi
          '';
        };

        # Pre-configured packages for different use cases
        packages = {
          ai-env = pkgs.python311.withPackages (ps: with ps; [
            torch
            transformers
            numpy
            pandas
            jupyter
          ]);
          
          security-tools = pkgs.symlinkJoin {
            name = "security-tools";
            paths = with pkgs; [
              nmap
              wireshark
              metasploit
              john
              hashcat
            ];
          };
        };
      });
}
