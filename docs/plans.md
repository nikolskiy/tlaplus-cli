# Plans for tlaplus-cli

tlaplus-cli goals:
1. Simplify managing available TLA+ tools such as TLC, community modules, custom modules, etc.
2. Run TLA tools in a single CLI interface.
3. Manage and display the tools outputs.

## Output Parsing

### Match the output format of the VS Code plugin.
- Research how VS code plugin parses TLC output.
- See if the parsing strategy is applicable to CLI.
- Use the same symbols for errors, warnings, and information messages.
- Implement parsing as a separate module in Python.

### Other output improvements
- Show when custom modules are used
- Show the classpath used to run TLC.
- Indicate if TLA+ versions of modules or Java versions are used for the specification.
- Show which version of `tla2tools.jar` is used for running the specification.

## Modules
- Add compiled (`.jar`) modules to the path for use during spec execution.
- Pull specific versions of `CommunityModules` from GitHub.
- Support adding multiple modules from different sources.
  - This requires management logic: all modules should be added as `.jar` files to local storage, similar to `tla2tools.jar`.
- Provide helpers to compile and experiment with modules in a local folder.
  - Only one local folder should be supported.
  - Additional modules should be supported via `.jar` files.

## Managing Local and Remote Instances
- For long-running tasks: show initial setup output and then send the process to the background.
- Query current statistics for a running instance.
- Start and stop instances.
- Support multiple independent jobs (investigate feasibility).
- Support local development where code is executed on a remote machine.

## Other Tools
- Can we integrate other tools? 
- Do we need to integrate other tools?
- What other tools are available for TLA+?

## Snapshot
- Save the results of all runs, including the specification and traces.
- Generate `.gitignore` entries.
- Store snapshots together with the main specification.

## Configuration Management
- Make different versions of `.cfg` files easy to change and maintain.

## TLC Output Artifacts
- Store TLC outputs and later display them in a predefined format (pretty-print or machine-readable).