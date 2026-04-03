# Compact Guide: Building and Running Custom TLC Modules

This is a quick summary for creating Java operator overrides for TLC.

## 1. Directory and Package Structure

```text
my-tla-project/
├── modules/
│   └── tlc2/
│       └── overrides/
│           └── TLCOverrides.java   <-- All operator overrides go here
├── classes/                        <-- Compiled output (javac -d)
│   ├── tlc2/
│   │   └── overrides/
│   │       └── TLCOverrides.class
│   └── META-INF/
│       └── services/
│           └── tlc2.overrides.ITLCOverrides
├── spec/
│   ├── queue.tla                   <-- Your TLA+ specification
│   └── QueueUtils.tla              <-- TLA+ wrapper module
├── lib/                            <-- Required only for manual setup
│   └── tla2tools.jar
```

## 2. Java Implementation Rules

Your Java override class has strict requirements:
* **Name & Package**: Must be exactly `tlc2.overrides.TLCOverrides`. Do not name it after your TLA+ module.
* **Interface**: Must implement `tlc2.overrides.ITLCOverrides` and return itself from `public Class[] get()`.
* **Methods**: Operator overrides must be `public static`, accept `tlc2.value.impl.Value` arguments, and return a `Value`.
* **Annotation**: Use `@TLAPlusOperator(identifier = "OperatorName", module = "TlaModuleName")` on your override methods.

**Example `TLCOverrides.java`:**
```java
package tlc2.overrides;

import tlc2.overrides.ITLCOverrides;
import tlc2.overrides.TLAPlusOperator;
import tlc2.value.impl.BoolValue;
import tlc2.value.impl.Value;

public class TLCOverrides implements ITLCOverrides {
    @TLAPlusOperator(identifier = "LogState", module = "QueueUtils")
    public static Value LogState(final Value buffer, final Value waitSet) {
        return BoolValue.ValTrue;
    }

    @Override
    public Class[] get() { return new Class[]{TLCOverrides.class}; }
}
```

## 3. TLA+ Wrapper Module

Create a `.tla` file (e.g., `QueueUtils.tla`) declaring the operators you want to override. TLC will substitute these definitions with your Java overrides during execution.

```tla
---- MODULE QueueUtils ----
LogState(buffer, wait_set) == TRUE
===========================
```

## 4. Building and Running

You need Java 11+ and `tla2tools.jar`. You can compile and run using either `tlaplus-cli` or manually.

### Using `tlaplus-cli`
The CLI automatically manages the classpath, dependency caching, and paths for you.
* **Compile:** `tla build` (Compiles Java sources from `modules/` into `classes/`)
* **Run TLC:** `tla tlc queue`

### Manual Setup (Without CLI)
You must download `tla2tools.jar` (e.g., into `lib/`) and strictly control the classpath order.

* **Compile:**
  ```bash
  javac -cp lib/tla2tools.jar -d classes modules/tlc2/overrides/TLCOverrides.java
  ```

* **Run TLC:**
  Crucially, your compiled `classes` directory **must appear before** `tla2tools.jar` in the Java classpath, otherwise TLC will ignore your overrides entirely.
  ```bash
  # Unix/Linux
  java -cp classes:lib/tla2tools.jar tlc2.TLC spec/queue.tla
  
  # Windows
  java -cp "classes;lib\tla2tools.jar" tlc2.TLC spec\queue.tla
  ```
