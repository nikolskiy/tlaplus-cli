# Guide to Setting Up Custom TLA+ Modules

A step-by-step guide to creating, compiling, and running custom Java operator overrides with `tlaplus-cli`.

## 1. How it Works (Dynamic Discovery)

In the standard TLC model checker, custom Java overrides are traditionally registered via a class named exactly `tlc2.overrides.TLCOverrides`. However, having the same class name across different modules causes classpath shadowing and prevents multiple sets of modules (e.g. `CommunityModules` and a custom project module) from working side-by-side.

`tlaplus-cli` solves this by introducing **Dynamic Override Discovery**:
1. **Unique Override Names**: You can name your override class uniquely (e.g., `QueueOverrides` or `ModuleAOverrides`) as long as it implements the `tlc2.overrides.ITLCOverrides` interface.
2. **Auto ServiceLoader Generation**: When you run `tla modules add`, the CLI scans your Java source files to discover all classes implementing `ITLCOverrides` and writes them into `META-INF/services/tlc2.overrides.ITLCOverrides`.
3. **Runtime Registration**: When you execute `tla tlc`, the CLI collects these classes from all cached modules and passes them directly to TLC via the JVM system property `-Dtlc2.overrides.TLCOverrides=...`.

## 2. Java Override Rules & Best Practices

When writing your Java classes:
* **Package**: Override classes must live in the `tlc2.overrides` package.
* **Methods**: Methods must be `public static`, accept parameter types from `tlc2.value.impl` (like `Value`, `BoolValue`, `IntValue`), and return a `Value`.
* **Suppressing Warnings**: By default, if TLC loads your override class but the TLA+ specification being run does not import your module, TLC will print a warning. Set `warn = false` in the `@TLAPlusOperator` annotation to suppress this warning when the module is not in use:
  ```java
  @TLAPlusOperator(identifier = "MyOperator", module = "MyModule", warn = false)
  ```

## 3. Example Project Structure & Runnable Doc Test

The following steps demonstrate how to add module sets (`module-a` and `module-b`) to the CLI cache, and run a specification that uses both.
The module set examples and simple TLA specification can be found in the [examples](./examples/) folder.

### Module Set A

#### File: `docs/examples/module-set-a/modules/tlc2/overrides/ModuleAOverrides.java`
```java
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
```

#### File: `docs/examples/module-set-a/modules/ModuleAUtils.tla`
```tla
---- MODULE ModuleAUtils ----
(* Handled by Java override when loaded, falls back to FALSE otherwise *)
HelloA == FALSE
=============================
```

### Module Set B

#### File: `docs/examples/module-set-b/modules/tlc2/overrides/ModuleBOverrides.java`
```java
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
```

#### File: `docs/examples/module-set-b/modules/ModuleBUtils.tla`
```tla
---- MODULE ModuleBUtils ----
(* Handled by Java override when loaded, falls back to FALSE otherwise *)
HelloB == FALSE
=============================
```

### Test Specification

#### File: `docs/examples/spec/test_both.tla`
```tla
---- MODULE test_both ----
EXTENDS ModuleAUtils, ModuleBUtils, TLC
VARIABLE x

Init == 
    /\ x = TRUE
    /\ Assert(HelloA, "Error: Module A Java override is not loaded!")
    /\ Assert(HelloB, "Error: Module B Java override is not loaded!")
    /\ PrintT(HelloA)
    /\ PrintT(HelloB)

Next == x' = x
==========================
```

#### File: `docs/examples/spec/test_both.cfg`
```cfg
INIT Init
NEXT Next
```

### Step-by-Step Execution Guide

You can copy and run these commands directly in your terminal from the repository root to verify the system:

#### Step 1: Add Modules to Cache
Add both modules to the CLI modules cache. The CLI compiles the Java classes and automatically registers their unique names in the Service Loader configuration files:

```bash
tla modules add docs/examples/module-set-a
tla modules add docs/examples/module-set-b
```

You can list loaded modules using:

```bash
tla modules list
```

#### Step 2: Execute Model Checking
Run TLC on the test specification:

```bash
tla tlc docs/examples/spec/test_both.tla
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
tla modules remove module-set-a
tla modules remove module-set-b
```
