# Custom Java Modules for TLC

TLC supports extending TLA+ specifications with custom Java operator overrides (modules). This directory contains documentation on how to create, build, register, and run these custom modules.

## Managing Modules

We support managing custom Java modules:

### 1. Recommended: Using `tlaplus-cli`

The `tla modules` command group in the CLI tool provides automated compilation, dependency loading, and class registry configuration. 

* **Add/Update a Module**: Compile your Java source files and register the module in the global CLI cache.
  ```bash
  tla modules add <path-to-module-set>
  ```
* **List Modules**: List all currently registered custom modules.
  ```bash
  tla modules list
  ```
* **Show Active Paths**: Display the active classpath and module directories.
  ```bash
  tla modules path
  ```
* **Remove a Module**: Remove a module from the global cache.
  ```bash
  tla modules remove <module-name>
  ```

For a step-by-step example demonstrating how to create, load, run, and clean up custom Java modules using the CLI, see [how-to-manage-modules-using-the-cli-tool.md](how-to-manage-modules-using-the-cli-tool.md).


### 2. Manual Module Management

If you choose not to use the CLI tool (or want to understand the underlying JVM properties and registry mechanics under the hood), you can manage and load your overrides manually using standard Java compilation and run commands.

For detailed instructions, low-level classloading details, and a runnable step-by-step manual execution example, see [how-to-manually-manage-modules.md](how-to-manually-manage-modules.md).


## Thread Safety Note

For details on writing thread-safe Java operator overrides (critical when running model checking with multiple worker threads), see [thread-safty-note.md](thread-safty-note.md).
