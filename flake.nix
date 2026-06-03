{
  description = "tlaplus-cli — TLA+ tools: download TLC, compile custom modules, run model checker";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      # Lightweight eachSystem — no extra flake-utils dependency.
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs supportedSystems (system: f {
          pkgs = nixpkgs.legacyPackages.${system};
        });
    in
    {
      # ── 1. Package (nix build / nix profile install) ────────────────────
      packages = forAllSystems ({ pkgs }:
        let
          python = pkgs.python312;
          tlaplus-cli = python.pkgs.buildPythonApplication rec {
            pname = "tlaplus-cli";
            version = "0.6.0";
            pyproject = true;

            src = ./.;

            # Build backend from [build-system].requires
            build-system = [ python.pkgs.setuptools ];

            # Runtime dependencies mapped from [project].dependencies
            dependencies = with python.pkgs; [
              typer
              requests
              pyyaml
              platformdirs
              pydantic
              truststore
              rich
            ];

            # The package bundles YAML resources — tell Nix not to strip them.
            # setuptools handles package-data inclusion via pyproject.toml already,
            # but we disable the bytecode-only optimisation to keep .yaml intact.
            dontPatchShebangs = false;

            # Skip tests during the Nix build (they need network / uv fixtures).
            doCheck = false;

            makeWrapperArgs = [
              "--prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.jre_headless ]}"
            ];

            meta = with pkgs.lib; {
              description = "TLA+ tools: download TLC, compile custom modules, run model checker";
              homepage = "https://github.com/nikolskiy/tlaplus-cli";
              license = licenses.mit;
              mainProgram = "tla";
            };
          };
        in
        {
          tlaplus-cli = tlaplus-cli;
          default = tlaplus-cli;
        }
      );

      # ── 2. Dev shell (nix develop) ──────────────────────────────────────
      devShells = forAllSystems ({ pkgs }:
        let
          python = pkgs.python312;
        in
        {
          default = pkgs.mkShell {
            buildInputs = [
              python
              pkgs.uv
              pkgs.ruff
              pkgs.jre_headless
            ];

            # "Nix outside, uv inside" — force uv to use the Nix-provided
            # Python and never download its own copy.
            env = {
              UV_PYTHON = "${python}/bin/python3";
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              echo "🔧 tlaplus-cli dev shell (Python ${python.version})"
              uv sync
              source .venv/bin/activate
            '';
          };
        }
      );
    };
}
