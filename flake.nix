{
  description = "GLaDOS Automatic Check-in";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pkgsFor = system: import nixpkgs { inherit system; };
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
          pythonEnv = pkgs.python3.withPackages (ps: [ ps.requests ]);
        in
        {
          default = pkgs.stdenv.mkDerivation {
            pname = "glados-checkin";
            version = "1.1.0";
            src = ./.;
            buildInputs = [ pythonEnv ];
            nativeBuildInputs = [ pkgs.makeWrapper ];
            installPhase = ''
              mkdir -p $out/bin $out/share/glados-checkin
              cp checkin.py $out/share/glados-checkin/
              cp -r glados_checkin $out/share/glados-checkin/
              makeWrapper ${pythonEnv}/bin/python3 $out/bin/glados-checkin \
                --set PYTHONPATH "$out/share/glados-checkin" \
                --add-flags "$out/share/glados-checkin/checkin.py"
            '';
          };
        }
      );

      nixosModules.default = import ./glados-checkin.nix self;
    };
}
