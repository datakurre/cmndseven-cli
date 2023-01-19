{
  description = "Camunda 7 CLI";

  # Flakes
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/release-22.11";
  inputs.poetry2nix = { url = "github:nix-community/poetry2nix"; inputs.nixpkgs.follows = "nixpkgs"; inputs.flake-utils.follows = "flake-utils"; };
  inputs.robot-task = { url = "github:datakurre/camunda-modeler-robot-plugin"; flake = false; };
  inputs.bpmn-to-image = { url = "github:bpmn-io/bpmn-to-image"; flake = false; };
  inputs.npmlock2nix = { url = "github:nix-community/npmlock2nix"; flake = false; };

  # Systems
  outputs = { self, nixpkgs, flake-utils, poetry2nix, bpmn-to-image, npmlock2nix, robot-task, ... }: flake-utils.lib.eachDefaultSystem (system: let pkgs = import nixpkgs { inherit system; overlays = [ poetry2nix.overlay ]; }; in {

    # Packages
    #packages.camnunda-cli 

    packages.bpmn-to-image = (import npmlock2nix { inherit pkgs; }).v1.build rec {
      src = bpmn-to-image;
      installPhase = ''
        mkdir -p $out/bin $out/lib
        cp -a node_modules $out/lib
        cp -a cli.js $out/bin/bpmn-to-image
        cp -a index.js $out/lib
        cp -a skeleton.html $out/lib
        cp ${robot-task}/dist/module-iife.js $out/lib/robot-task.js
        substituteInPlace $out/bin/bpmn-to-image \
          --replace "'./'" \
                    "'$out/lib'"
        substituteInPlace $out/lib/index.js \
          --replace "__dirname}/skeleton.html" \
                    "process.env.BPMN_TO_IMAGE_SKELETON_HTML || __dirname}/skeleton.html" \
          --replace "puppeteer.launch();" \
                    "puppeteer.launch({executablePath: '${pkgs.chromium}/bin/chromium'});" \
          --replace "await loadScript(viewerScript);"\
                    "await loadScript(viewerScript); await loadScript('$out/lib/robot-task.js')"
        substituteInPlace $out/lib/skeleton.html \
          --replace "container: '#canvas'" \
                    "container: '#canvas', additionalModules: [ RobotTaskModule ]"
        wrapProgram $out/bin/bpmn-to-image \
          --set PATH ${pkgs.lib.makeBinPath [ pkgs.nodejs ]} \
          --set NODE_PATH $out/lib/node_modules
      '';
      buildInputs = [ pkgs.makeWrapper ];
      buildCommands = [];
      node_modules_attrs = {
        PUPPETEER_SKIP_DOWNLOAD = "true";
      };
    };

    # Overlay
    overlays.default = final: prev: {
#     inherit (self.packages.${system})
#     camunda-cli
#     ;
    };

    # Shells
    devShells.default = pkgs.mkShell {
      buildInputs = [
        self.packages.${system}.bpmn-to-image
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
