# Guide to Setting Up Custom TLA+ Modules

A step-by-step guide to creating, compiling, and running custom Java operator overrides with `tlaplus-cli`.

---

## 1. How it Works (Dynamic Discovery)

In the standard TLC model checker, custom Java overrides are traditionally registered via a class named exactly `tlc2.overrides.TLCOverrides`. However, having the same class name across different modules causes classpath shadowing and prevents multiple sets of modules (e.g. `CommunityModules` and a custom project module) from working side-by-side.

`tlaplus-cli` solves this by introducing **Dynamic Override Discovery**:
1. **Unique Override Names**: You can name your override class uniquely (e.g., `QueueOverrides` or `ModuleAOverrides`) as long as it implements the `tlc2.overrides.ITLCOverrides` interface.
2. **Auto ServiceLoader Generation**: When you run `tla modules add`, the CLI scans your Java source files to discover all classes implementing `ITLCOverrides` and writes them into `META-INF/services/tlc2.overrides.ITLCOverrides`.
3. **Runtime Registration**: When you execute `tla tlc`, the CLI collects these classes from all cached modules and passes them directly to TLC via the JVM system property `-Dtlc2.overrides.TLCOverrides=...`.

---

## 2. Java Override Rules & Best Practices

When writing your Java classes:
* **Package**: Override classes must live in the `tlc2.overrides` package.
* **Methods**: Methods must be `public static`, accept parameter types from `tlc2.value.impl` (like `Value`, `BoolValue`, `IntValue`), and return a `Value`.
* **Suppressing Warnings**: By default, if TLC loads your override class but the TLA+ specification being run does not import your module, TLC will print a warning. Set `warn = false` in the `@TLAPlusOperator` annotation to suppress this warning when the module is not in use:
  ```java
  @TLAPlusOperator(identifier = "MyOperator", module = "MyModule", warn = false)
  ```

---

## 3. Runnable Doc Test / Integration Test

The following steps demonstrate how to set up two separate custom module sets (`module-a` and `module-b`), add them to the CLI cache, and run a specification that uses both. You can copy and run these commands directly in your terminal to verify the entire system.

### Step 1: Create the Workspace Directories
Create the directory structure for both modules and the test specification:

```bash
mkdir -p test-docs-modules/module-a/modules/tlc2/overrides
mkdir -p test-docs-modules/module-b/modules/tlc2/overrides
mkdir -p test-docs-modules/spec
```

### Step 2: Write Module A Overrides and TLA Wrapper
Create `ModuleAOverrides.java` with a unique class name:

```bash
cat << 'EOF' > test-docs-modules/module-a/modules/tlc2/overrides/ModuleAOverrides.java
package tlc2.overrides;

import tlc2.overrides.ITLCOverrides;
import tlc2.overrides.TLAPlusOperator;
import tlc2.value.impl.BoolValue;
import tlc2.value.impl.Value;

public class ModuleAOverrides implements ITLCOverrides {

    @TLAPlusOperator(identifier = "HelloA", module = "ModuleAUtils", warn = false)
    public static Value HelloA() {
        System.out.println("Java execution: Hello from Module A!");
        return BoolValue.ValTrue;
    }

    @Override
    public Class[] get() {
        return new Class[]{ModuleAOverrides.class};
    }
}
EOF
```

Create the TLA+ wrapper file `ModuleAUtils.tla`:

```bash
cat << 'EOF' > test-docs-modules/module-a/modules/ModuleAUtils.tla
---- MODULE ModuleAUtils ----
(* Handled by Java override when loaded, falls back to FALSE otherwise *)
HelloA == FALSE
=============================
EOF
```

### Step 3: Write Module B Overrides and TLA Wrapper
Create `ModuleBOverrides.java` with a unique class name:

```bash
cat << 'EOF' > test-docs-modules/module-b/modules/tlc2/overrides/ModuleBOverrides.java
package tlc2.overrides;

import tlc2.overrides.ITLCOverrides;
import tlc2.overrides.TLAPlusOperator;
import tlc2.value.impl.BoolValue;
import tlc2.value.impl.Value;

public class ModuleBOverrides implements ITLCOverrides {

    @TLAPlusOperator(identifier = "HelloB", module = "ModuleBUtils", warn = false)
    public static Value HelloB() {
        System.out.println("Java execution: Hello from Module B!");
        return BoolValue.ValTrue;
    }

    @Override
    public Class[] get() {
        return new Class[]{ModuleBOverrides.class};
    }
}
EOF
```

Create the TLA+ wrapper file `ModuleBUtils.tla`:

```bash
cat << 'EOF' > test-docs-modules/module-b/modules/ModuleBUtils.tla
---- MODULE ModuleBUtils ----
(* Handled by Java override when loaded, falls back to FALSE otherwise *)
HelloB == FALSE
=============================
EOF
```

### Step 4: Write the Combined Test Specification
Create a TLA+ specification `test_both.tla` that imports both wrapper modules:

```bash
cat << 'EOF' > test-docs-modules/spec/test_both.tla
---- MODULE test_both ----
EXTENDS ModuleAUtils, ModuleBUtils, TLC
VARIABLE x

Init == 
    /\ x = TRUE
    /\ PrintT(HelloA)
    /\ PrintT(HelloB)

Next == x' = x
==========================
EOF
```

Create the TLC configuration file `test_both.cfg`:

```bash
cat << 'EOF' > test-docs-modules/spec/test_both.cfg
INIT Init
NEXT Next
EOF
```

### Step 5: Add Modules to Cache
Add both modules to the CLI modules cache. The CLI compiles the Java classes and automatically registers their unique names in the Service Loader configuration files:

```bash
tla modules add test-docs-modules/module-a
tla modules add test-docs-modules/module-b
```

You can list loaded modules using:

```bash
tla modules list
```

### Step 6: Execute Model Checking
Run TLC on the test specification:

```bash
tla tlc test-docs-modules/spec/test_both.tla
```

**Expected Console Output:**
Verify that both Java implementations execute successfully and print their log messages:
```text
Java execution: Hello from Module A!
Java execution: Hello from Module B!
```

## 4. Cleaning Up Cache
To remove the test modules from your system cache, simply run:

```bash
tla modules remove module-a
tla modules remove module-b
rm -rf test-docs-modules
```
