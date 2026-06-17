# Running TLC

The `tla tlc` command group allows you to run the TLC model checker on your TLA+ specifications using the pinned version of the TLA+ toolset.

## Run Model Checking

To run the TLC model checker on a specification:

```bash
tla tlc <spec_name>
```

For example, to run model checking on `queue.tla`:

```bash
tla tlc queue
```

## Inspect Commands & Versions

### Check Pinned Version
To check the currently pinned `tla2tools.jar` path and its TLC version:

```bash
tla tlc --version
```

> [!NOTE]
> The actual TLC version used is determined by the installed and pinned version of the TLA+ toolset. You can manage and pin these versions via the `tla tools` command group. See [Managing TLA+ Tools](../managing-tlaplus-tools/managing-tla2tools.md) for more information.

### Show Java Command
To inspect the exact Java command that will be executed without actually running it:

```bash
tla tlc <spec_name> --show-command
```

## Integration with Custom Modules

The `tla tlc` command automatically accounts for any custom TLA+ modules added to the CLI cache via the `tla modules add` command:

```bash
tla modules add <path_to_module>
```

When running model checking, the CLI dynamically discovers Java operator overrides and registers them. It then executes the TLC model checker including all these cached modules on the classpath.

For detailed instructions on how to create, build, and register custom Java overrides, refer to the [Guide to Setting Up Custom TLA+ Modules](../java-modules-for-tlc/how-to-manage-modules-using-the-cli-tool.md).
