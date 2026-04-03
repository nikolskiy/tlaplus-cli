# Guide to Setting Up a Custom TLA+ Module

A step-by-step guide to creating Java operator overrides for use with the TLC model checker.

## 1. Project Prerequisites

- **Java Version**: Java 11 or higher.
- **Dependencies**: `tla2tools.jar` — contains the base classes (`Value`, `ITLCOverrides`) and annotations (`@TLAPlusOperator`).

### Manual Setup
Download `tla2tools.jar` from the [TLA+ GitHub releases](https://github.com/tlaplus/tlaplus/releases) or find it in your Toolbox installation. Place it in a `lib/` directory in your project.

### Using `tlaplus-cli`
Run `tla tools install` to automatically fetch the latest stable release into your system cache (`~/.cache/tla/tools/`).

---

## 2. Directory and Package Structure

Your Java override class **must** live in the `tlc2.overrides` package.

### Recommended Directory Layout

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

---

## 3. Critical: The Class Must Be Named `TLCOverrides`

> ⚠️ **This is the single most important thing to get right.**

> ✅ **Verified**: Tests confirm TLC requires the exact class name `tlc2.overrides.TLCOverrides`.

TLC discovers operator overrides by **hardcoding** the class name `tlc2.overrides.TLCOverrides`. It does *not* use Java's `ServiceLoader` mechanism for primary discovery, despite the existence of the `ITLCOverrides` interface.

This means:
- Your Java class **must** be named `TLCOverrides` (not `MyModule`, not `QueueUtils`, etc.).
- The `@TLAPlusOperator` annotation's `module` attribute maps operators to the correct TLA+ module — that's where you specify your module name.
- All operator overrides for *all* your TLA+ modules go into this single class (or are referenced via its `get()` method).

### Common Mistake

Naming the class to match your TLA+ module (e.g., `QueueUtils.java` for `QueueUtils.tla`) — TLC will silently ignore it and fall back to the pure TLA+ definition.

### Verified Class-Naming Behavior

There is conflicting information in various TLA+ discussions. The [TLA+ Wiki: codebase:idiosyncrasies](https://docs.tlapl.us/codebase:idiosyncrasies) and [tlaplus/tlaplus#1114](https://github.com/tlaplus/tlaplus/issues/1114) suggest TLC uses `SimpleFilenameToStream` to resolve class names matching module names. Our test suite explicitly verifies actual behavior for modern TLC:

| Approach | Result |
|---|---|
| Single class named `TLCOverrides` in `tlc2.overrides` | ✅ Works — overrides load for any module specified in `@TLAPlusOperator` ([#326](https://github.com/tlaplus/tlaplus/issues/326)). The class must also implement `ITLCOverrides` ([#1114](https://github.com/tlaplus/tlaplus/issues/1114)). |
| Java class named after the TLA+ module (e.g., `TestModule.java`) | ❌ Fails — TLC silently skips the override and falls back to the TLA+ definition. Contradicts the [TLA+ Wiki](https://docs.tlapl.us/codebase:idiosyncrasies). |

**Conclusion:** You must always use the `tlc2.overrides.TLCOverrides` name. TLC does not automatically discover module-named classes.

---

## 4. Java Implementation

Your class must:
1. Be named `TLCOverrides`
2. Live in the `tlc2.overrides` package
3. Implement `ITLCOverrides`
4. Return itself (and any other override classes) from the `get()` method
5. Use `@TLAPlusOperator` annotations with the correct `module` name

### Key Rules

- **Method Signature**: Methods must be `public static`, accept `Value` parameters, and return a `Value`.
- **Value Types**: Use the hierarchy in `tlc2.value.impl` — e.g., `BoolValue`, `IntValue`, `StringValue`, `TupleValue`. Modern TLC (> 1.5.8) uses this package ([Stack Overflow: module overloading](https://stackoverflow.com/questions/53908653/use-module-overloading-to-implement-a-hash-function-in-tla)).
- **Thread Safety**: TLC is multi-threaded. Treat methods as pure functions — avoid mutable static state or synchronize access. For per-thread storage, use `TLCGet`/`TLCSet` ([Learn TLA+: Modules](https://learntla.com/core/modules.html)).

  > 📝 The specific thread-safety constraints of the TLC execution model are not yet fully verified against the source code.

- **No Nested Classes**: Avoid nested classes for overrides — they can cause `NoClassDefFoundError`.

### Example: Logging Buffer and Wait-Set State

```java
package tlc2.overrides;

import tlc2.overrides.ITLCOverrides;
import tlc2.overrides.TLAPlusOperator;
import tlc2.value.impl.BoolValue;
import tlc2.value.impl.Value;

public class TLCOverrides implements ITLCOverrides {

    // "module" must match the TLA+ module name, NOT the Java class name
    @TLAPlusOperator(identifier = "LogState", module = "QueueUtils")
    public static Value LogState(final Value buffer, final Value waitSet) {
        System.out.println("State log: buffer=" + buffer + ", wait_set=" + waitSet);
        return BoolValue.ValTrue;
    }

    @Override
    public Class[] get() {
        return new Class[]{TLCOverrides.class};
    }
}
```

### Supporting Multiple TLA+ Modules

> ✅ **Verified**: Tests confirm you **cannot** create separate Java classes matching module names (e.g., `QueueUtils.java`). All overrides must be combined into the single `TLCOverrides` class.

If you have overrides for multiple TLA+ modules, put them all in `TLCOverrides`:

```java
public class TLCOverrides implements ITLCOverrides {

    @TLAPlusOperator(identifier = "LogState", module = "QueueUtils")
    public static Value LogState(final Value buffer, final Value waitSet) { ... }

    @TLAPlusOperator(identifier = "Hash", module = "CryptoUtils")
    public static Value Hash(final Value input) { ... }

    @Override
    public Class[] get() {
        return new Class[]{TLCOverrides.class};
    }
}
```

> 📝 Returning additional classes via the `get()` array (e.g., `{TLCOverrides.class, AnotherOverride.class}`) has not yet been verified.

## 5. TLA+ Wrapper Module

You need a `.tla` file that declares the operator signatures. TLC replaces these definitions with your Java overrides at runtime. This file also serves as a fallback for tools that don't support Java overrides (SANY, Apalache).

```tla
---- MODULE QueueUtils ----
(* Defines the operator interface. *)
(* TLC will ignore this definition and use the Java override instead. *)
LogState(buffer, wait_set) == TRUE
===========================
```

Place this file in the same directory as your main specification so TLC can find it.

---

## 6. Compilation

### Manual Compilation

```bash
# Compile
javac -cp lib/tla2tools.jar -d classes modules/tlc2/overrides/TLCOverrides.java

# Create the ServiceLoader service file
mkdir -p classes/META-INF/services
echo "tlc2.overrides.TLCOverrides" > classes/META-INF/services/tlc2.overrides.ITLCOverrides
```

> **Note**: TLC's primary override discovery relies on the hardcoded `TLCOverrides` class name. The `META-INF/services/` file enables `ServiceLoader` discovery but is not what TLC uses directly.

### Using `tlaplus-cli`

```bash
tla build
```

This compiles all Java files in your configured modules directory (default: `modules/`), outputs class files to `classes/`, and creates the `ServiceLoader` file automatically. It also uses the downloaded `tla2tools.jar` from your system cache.

> ✅ **Verified**: Build tests confirm `tlaplus-cli` generates the `META-INF/services/tlc2.overrides.ITLCOverrides` file automatically.

---

## 7. Execution

Your compiled classes must be on the classpath **before** `tla2tools.jar`.

### Manual Execution

**Unix/Linux** (separator is `:`):
```bash
java -cp classes:lib/tla2tools.jar tlc2.TLC spec/queue.tla
```

**Windows** (separator is `;`):
```cmd
java -cp classes;lib\tla2tools.jar tlc2.TLC spec\queue.tla
```

### Using `tlaplus-cli`

```bash
tla run queue
```

The CLI automatically constructs the correct classpath using your cached `tla2tools.jar` and your compiled `classes/` directory, and runs `tlc2.TLC` with appropriate Java garbage collection options.

### Using TLA+ Toolbox

1. Go to **File > Preferences > TLA+ Preferences > TLA+ library path locations**.
2. Add the directory containing your compiled class files or your custom JAR.

### Using VS Code

Configure the `tlaplus.java.options` setting in your `settings.json`:

```json
"tlaplus.java.options": "-cp path/to/classes:path/to/tla2tools.jar"
```

---

## 8. Console Output

> ✅ **Verified**: Integration tests confirm that `System.out.println` writes to terminal output during TLC execution, correctly interleaved with TLC's native logs.

`System.out.println` **works** from Java overrides:

```java
System.out.println("State log: buffer=" + buffer + ", wait_set=" + waitSet);
```

**If your output isn't appearing**, the most likely cause is that your override class is **not being loaded** — see [9 — Debugging](#9-debugging). TLC silently falls back to the pure TLA+ definition with no error message.

For large models producing many log lines, writing to a file is more practical:

```java
PrintWriter pw = new PrintWriter(new FileWriter("tlc_log.txt", true));
pw.println("buffer=" + buffer + ", wait_set=" + waitSet);
pw.flush();
pw.close();
```

The file path is relative to TLC's working directory (the spec directory when using `tla run`).

---

## 9. Debugging

### Override Not Loading (Silent Failure)

**Symptom**: TLC runs successfully but your Java code has no effect — TLC silently uses the TLA+ definition.

**Most likely cause**: Your class is not named `TLCOverrides`.

**How to confirm**: Look for this line in TLC's output:
```
Loading LogState operator override from tlc2.overrides.TLCOverrides with signature: ...
```
If this line is **missing**, TLC did not find your override class.

**Checklist**:
1. The Java class is named `TLCOverrides` (not your module name)
2. It's in the `tlc2.overrides` package
3. It implements `ITLCOverrides`
4. The `get()` method returns `new Class[]{TLCOverrides.class}`
5. The compiled classes are on the classpath *before* `tla2tools.jar`
6. The `@TLAPlusOperator` annotation's `module` matches the TLA+ module name exactly

> ✅ **Verified**: Tests strictly confirm this checklist. The class **must** be named `TLCOverrides`; naming it after the TLA+ module does not work.

### Verifying Class Loading

Add a static initializer to confirm the class is loaded:

```java
static {
    try {
        PrintWriter pw = new PrintWriter(new FileWriter("/tmp/tlc_debug.txt"));
        pw.println("TLCOverrides loaded at " + java.time.Instant.now());
        pw.close();
    } catch (IOException e) {
        System.err.println("Debug write failed: " + e);
    }
}
```

If `/tmp/tlc_debug.txt` is not created after running TLC, the class is not on the classpath.

### Verifying ServiceLoader Discovery (Independent Test)

You can verify that `ServiceLoader` can find your class independently of TLC:

```java
// TestOverride.java (temporary, in project root)
import java.util.ServiceLoader;
import tlc2.overrides.ITLCOverrides;

public class TestOverride {
    public static void main(String[] args) {
        ServiceLoader<ITLCOverrides> loader = ServiceLoader.load(ITLCOverrides.class);
        for (ITLCOverrides svc : loader) {
            System.out.println("Found: " + svc.getClass().getName());
        }
    }
}
```

```bash
javac -cp classes:lib/tla2tools.jar TestOverride.java
java -cp .:classes:lib/tla2tools.jar TestOverride
```

> **Note**: Even if this test succeeds, TLC may still not load your override if the class is not named `TLCOverrides`. TLC uses `Class.forName()` with the hardcoded name — not `ServiceLoader`.

### Classpath Order Matters

> ✅ **Verified**: The CLI's integration test (`test_run_tlc.py`) confirms that placing your custom classes directory strictly **before** `tla2tools.jar` allows TLC to successfully load and execute your overrides.

Your classes must appear **before** `tla2tools.jar` in the classpath. When the JVM searches for a class, the first match wins — any subsequent occurrences are shadowed ([Oracle: The java Command](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)). If reversed, TLC won't find your overrides.

> **Note**: Omitting `tla2tools.jar` entirely will cause `NoClassDefFoundError` for standard TLA classes.

### Multiple Override Classes

> 📝 Passing additional classes via the `get()` array has not yet been verified. Use with caution.

If you have overrides spread across multiple Java classes, you can attempt to return all of them from `TLCOverrides.get()`:

```java
@Override
public Class[] get() {
    return new Class[]{TLCOverrides.class, AnotherOverride.class};
}
```

> ✅ **Verified**: Testing confirms that `SimpleFilenameToStream` is **not** used by TLC to discover module classes autonomously. The `TLCOverrides` class is the sole, reliable registration entry point. Matching Java class names to TLA+ module names (as suggested by the [TLA+ Wiki](https://docs.tlapl.us/codebase:idiosyncrasies)) does not work for operator overrides.
