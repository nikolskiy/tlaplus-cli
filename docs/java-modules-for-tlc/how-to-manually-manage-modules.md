# Guide: Building and Running Custom TLC Modules Manually

This guide explains how to manually compile and register custom Java operator overrides for TLC without using `tlaplus-cli`. It covers manual classloading registration, classpath setup, and library path configuration, using the same multi-module examples from the CLI guide.

## 1. How TLC Loads Overrides (Under the Hood)

When running TLC, custom Java overrides are resolved via two main mechanisms:

1. **Dynamic Override Registry (`-Dtlc2.overrides.TLCOverrides`)**:
   Standard TLC does not search the classpath for arbitrary override classes automatically. Instead, you must specify the fully qualified class names of your override classes to the JVM using the system property `-Dtlc2.overrides.TLCOverrides`. The value is a list of classes separated by the platform's path separator (`:` on Unix/Linux, `;` on Windows).
   
   *Example:*
   ```bash
   -Dtlc2.overrides.TLCOverrides=tlc2.overrides.ModuleAOverrides:tlc2.overrides.ModuleBOverrides
   ```

2. **ServiceLoader API (`ITLCOverrides`)**:
   TLC uses Java's standard ServiceLoader mechanism to load implementations of `tlc2.overrides.ITLCOverrides`. To register a class, you create a provider configuration file:
   - Path: `classes/META-INF/services/tlc2.overrides.ITLCOverrides`
   - Content: A list of fully qualified override class names (one per line).

3. **TLA+ Libraries (`-DTLA-Library`)**:
   TLC needs to know where to search for TLA+ library modules (like `ModuleAUtils.tla` and `ModuleBUtils.tla`) that are extended/imported by your main specification. This is configured via the `-DTLA-Library` system property, which is a list of directory paths separated by the platform's path separator.
   
   *Example:*
   ```bash
   -DTLA-Library=module-set-a/modules:module-set-b/modules
   ```

---

## 2. Directory Structure

To manage multiple modules manually, organize your project files as follows:

```text
my-tla-project/
├── module-set-a/
│   └── modules/
│       ├── tlc2/
│       │   └── overrides/
│       │       └── ModuleAOverrides.java
│       └── ModuleAUtils.tla
├── module-set-b/
│   └── modules/
│       ├── tlc2/
│       │   └── overrides/
│       │       └── ModuleBOverrides.java
│       └── ModuleBUtils.tla
├── spec/
│   ├── test_both.tla
│   └── test_both.cfg
├── classes/                        <-- Combined compiled classes target
└── lib/
    └── tla2tools.jar               <-- Standard TLC library
```

---

## 3. Java Implementation Rules

Your Java override classes must adhere to these rules:
* **Package**: Must be exactly `tlc2.overrides`.
* **Interface**: Must implement `tlc2.overrides.ITLCOverrides` and return its own class in the array returned by `public Class[] get()`.
* **Methods**: Override methods must be `public static`, take arguments from `tlc2.value.impl` (such as `Value`, `BoolValue`), and return a `Value`.
* **Annotation**: Annotate each override method with `@TLAPlusOperator(identifier = "OperatorName", module = "TlaModuleName", warn = false)`.

### Example Classes

#### Module Set A Override: `module-set-a/modules/tlc2/overrides/ModuleAOverrides.java`
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

#### Module Set B Override: `module-set-b/modules/tlc2/overrides/ModuleBOverrides.java`
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

---

## 4. TLA+ Wrapper Modules

Create the `.tla` files that correspond to the Java operators. TLC will substitute these definitions with your Java overrides during execution.

#### Module Set A Wrapper: `module-set-a/modules/ModuleAUtils.tla`
```tla
---- MODULE ModuleAUtils ----
HelloA == FALSE
=============================
```

#### Module Set B Wrapper: `module-set-b/modules/ModuleBUtils.tla`
```tla
---- MODULE ModuleBUtils ----
HelloB == FALSE
=============================
```

---

## 5. Main Test Specification

Create a test specification that imports both modules to verify they run correctly.

#### File: `spec/test_both.tla`
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

#### File: `spec/test_both.cfg`
```cfg
INIT Init
NEXT Next
```

---

## 6. Step-by-Step Manual Compilation and Execution

Follow these steps from the repository/project root to compile the sources, register the overrides, and run the specification manually. We will use a temporary sandbox directory `manual-test-temp` to keep the workspace clean.

### Step 1: Create Sandbox Directories and Download `tla2tools.jar`

Create the sandbox directories and download `tla2tools.jar` (v1.8.0) using `curl`:

```bash
# Create the temporary sandbox and lib directories
mkdir -p manual-test-temp/lib manual-test-temp/classes

# Download tla2tools.jar
curl -L -o manual-test-temp/lib/tla2tools.jar https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar
```

### Step 2: Compile the Java Sources

Compile the Java files from both module sets into the shared `manual-test-temp/classes/` output directory:

```bash
# Compile both Java source files using tla2tools.jar on the classpath
javac -cp manual-test-temp/lib/tla2tools.jar -d manual-test-temp/classes \
  docs/examples/module-set-a/modules/tlc2/overrides/ModuleAOverrides.java \
  docs/examples/module-set-b/modules/tlc2/overrides/ModuleBOverrides.java
```

### Step 3: Register Overrides via Service Loader

To support standard service loading registration, manually create the `ITLCOverrides` service provider configuration file in the `manual-test-temp/classes/` directory and list both fully qualified class names:

```bash
# Create the services directory
mkdir -p manual-test-temp/classes/META-INF/services

# Write the override classes to the service file (one per line)
cat << 'EOF' > manual-test-temp/classes/META-INF/services/tlc2.overrides.ITLCOverrides
tlc2.overrides.ModuleAOverrides
tlc2.overrides.ModuleBOverrides
EOF
```

### Step 4: Run TLC

Execute TLC by manually setting up the classpath, the `-Dtlc2.overrides.TLCOverrides` system property, and the `-DTLA-Library` system property.

> [!IMPORTANT]
> Your compiled `manual-test-temp/classes` directory **must appear before** `manual-test-temp/lib/tla2tools.jar` in the Java classpath (`-cp`) so that TLC loads the custom class definitions and service loader declarations instead of using standard defaults.

#### Unix/Linux
```bash
java \
  -Dtlc2.overrides.TLCOverrides=tlc2.overrides.ModuleAOverrides:tlc2.overrides.ModuleBOverrides \
  -DTLA-Library=docs/examples/module-set-a/modules:docs/examples/module-set-b/modules \
  -cp manual-test-temp/classes:docs/examples/module-set-a/modules:docs/examples/module-set-b/modules:manual-test-temp/lib/tla2tools.jar \
  tlc2.TLC \
  docs/examples/spec/test_both.tla
```

#### Windows
```cmd
java ^
  -Dtlc2.overrides.TLCOverrides="tlc2.overrides.ModuleAOverrides;tlc2.overrides.ModuleBOverrides" ^
  -DTLA-Library="docs/examples/module-set-a/modules;docs/examples/module-set-b/modules" ^
  -cp "manual-test-temp\classes;docs\examples\module-set-a\modules;docs\examples\module-set-b\modules;manual-test-temp\lib\tla2tools.jar" ^
  tlc2.TLC ^
  docs\examples\spec\test_both.tla
```

### Expected Output
When run successfully, you should see the print statements from the Java overrides outputted to the console:
```text
Java execution: Hello from Module A!
Java execution: Hello from Module B!
```

### Step 5: Clean Up
Once complete, delete the temporary sandbox directory:

```bash
rm -rf manual-test-temp
```
