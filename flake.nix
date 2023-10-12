{
  description = "Opinionated Camunda Platform 7 CLI";

  nixConfig = {
    extra-trusted-public-keys = "datakurre.cachix.org-1:ayZJTy5BDd8K4PW9uc9LHV+WCsdi/fu1ETIYZMooK78=";
    extra-substituters = "https://datakurre.cachix.org";
  };

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/release-22.11";
    poetry2nix = { url = "github:nix-community/poetry2nix"; inputs.nixpkgs.follows = "nixpkgs"; inputs.flake-utils.follows = "flake-utils"; };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix, ... }: flake-utils.lib.eachDefaultSystem (system: let pkgs = import nixpkgs { inherit system; overlays = [ poetry2nix.overlay ]; }; in {
    # Apps
    apps.default = {
        type = "app";
        program = self.packages.${system}.default + "/bin/ccli";
    };

    # Packages
    packages.default = (pkgs.poetry2nix.mkPoetryApplication {
      projectDir = ./.;
      propagatedBuildInputs = [
        pkgs.chromium
        pkgs.nodejs
      ];
      overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
        generic-camunda-client = super.generic-camunda-client.overridePythonAttrs(old: {
          buildInputs = old.buildInputs ++ [ self.setuptools ];
        });
      });
    });
    packages.env = (pkgs.poetry2nix.mkPoetryEnv {
      projectDir = ./.;
      overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
        generic-camunda-client = super.generic-camunda-client.overridePythonAttrs(old: {
          buildInputs = old.buildInputs ++ [ self.setuptools ];
        });
      });
    });

    # Shells
    devShells.default = pkgs.mkShell {
      buildInputs = [
        pkgs.nodejs
        pkgs.poetry
        (pkgs.poetry2nix.mkPoetryEnv {
          projectDir = ./.;
          overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
            generic-camunda-client = super.generic-camunda-client.overridePythonAttrs(old: {
              buildInputs = old.buildInputs ++ [ self.setuptools ];
            });
          });
        })
      ];
    };

  });
}
