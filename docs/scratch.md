# Scratchpad

## TLC commands
TLC should be installable from config tla.urls.default.
In the default_config.yaml, the default URL is https://github.com/tlaplus/tlaplus/tags.
It is possible to get json version of all releases from:
`curl -H "Accept: application/vnd.github+json" https://api.github.com/repos/tlaplus/tlaplus/tags`
This is just an example we should write Python version of that.

- `tla tlc list`: List the available TLC installations
    The format of the list should be:
    <version name>  <short tag>  <status> <pinned>
    Version name should come from field "name" from the json that we got.
    The example: v1.8.0, v1.7.4
    Status should be "installed" if the version is installed, "upgrade" if the version is installed locally but there is a newer version available with a different short tag, and "available" otherwise.
    The short tag should be the first 7 characters from the sha field (response_json[0]['commit']['sha'][:7]).
    Pinned should display a green checkmark if the version is pinned, and display nothing otherwise.

- `tla tlc install`: Download and install TLC versions.
    It should accept version name or short tag.
    If no version name or short tag is provided, it should install the latest version.
    Currently we are using python library to determine where to store installed versions. We should make sure that each version is stored in a separate directory. Each of those subdirectoris should be called using the the version name and short tag for example v1.8.0-abcdefg.
- `tla tlc upgrade`: Upgrade installed TLC versions
    by default upgrade pinned version. If version is provided it should upgrade that version.
- `tla tlc find`: Search for a TLC installation
  Output path to the installed version. If no version is provided, it should output the path to the pinned version. Example output:
    TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
    /home/bob/.cache/tla/tlc/v1.8.0-5a47802/tla2tools.jar
- `tla tlc pin`: Pin to a specific TLC version
  Pinning should be done using the version name. If there are multiple version names we should let user choose using short tag. If no version is provided, it should pin the latest version.
- `tla tlc dir`: Show the TLC installation directory
    For example: /home/bob/.cache/tla/tlc
- `tla tlc uninstall`: Uninstall TLC versions
    It should accept version name or short tag. The directory with selected version should be removed.

## Other commands
- `tla run`:
    Run TLC model checker on a TLA+ specification. Currently the same functionality is executed by `tla tlc /path/to/spec`. We should change it to `tla run /path/to/spec.`
- `tla check-java`: Verify Java version meets the minimum requirement. Already exists.
- `tla build`: Compile custom Java modules for TLC. Already exists.