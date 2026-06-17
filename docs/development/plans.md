# Plans for tlaplus-cli

tlaplus-cli goals:
1. Simplify managing available TLA+ tools such as TLC, community modules, custom modules, etc.
2. Run TLA tools in a single CLI interface.
3. Manage and display the tools outputs.


### Output improvements
- Show when custom modules are used
- Show the classpath used to run TLC.
- Indicate if TLA+ versions of modules or Java versions are used for the specification.
- Show which version of `tla2tools.jar` is used for running the specification.

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