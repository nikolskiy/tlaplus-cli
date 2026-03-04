# Guide to Setting Up a Custom TLA+ Module

A step-by-step guide to creating Java operator overrides for use with the TLC model checker.

## 1. Project Prerequisites

- **Java Version**: Java 11 or higher.
- **Dependencies**: `tla2tools.jar` — contains the base classes (`Value`, `ITLCOverrides`) and annotations (`@TLAPlusOperator`).

### Manual Setup
Download `tla2tools.jar` from the [TLA+ GitHub releases](https://github.com/tlaplus/tlaplus/releases) or find it in your Toolbox installation. Place it in a `lib/` directory in your project.

### Using `tlaplus-cli`
Run `tla download` to automatically fetch the latest stable release into your system cache (`~/.cache/tla/tla2tools.jar`).

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

## 3. Critical: The Class Must Be Named `TLCOverrides`

> ⚠️ **This is the single most important thing to get right.**

TLC discovers operator overrides by **hardcoding** the class name `tlc2.overrides.TLCOverrides`. It does *not* use Java's `ServiceLoader` mechanism, despite the existence of the `ITLCOverrides` interface. The relevant code in `tlc2.tool.impl.SpecProcessor` does:

```java
Class<?> cls = tlaClass.loadClass("tlc2.overrides.TLCOverrides");
```

This means:
- Your Java class **must** be named `TLCOverrides` (not `MyModule`, not `QueueUtils`, etc.).
- The `@TLAPlusOperator` annotation's `module` attribute maps operators to the correct TLA+ module — that's where you specify your module name.
- All operator overrides for *all* your TLA+ modules go into this single class (or are referenced via its `get()` method).

### Common Mistake

Naming the class to match your TLA+ module (e.g., `QueueUtils.java` for `QueueUtils.tla`) — TLC will silently ignore it and use the pure TLA+ definition instead.

> ### 📝 Needs Verification: Class Naming
>
> According to TLA+ documentation ([TLA+ Wiki: codebase:idiosyncrasies](https://docs.tlapl.us/codebase:idiosyncrasies), [tlaplus/tlaplus#1114](https://github.com/tlaplus/tlaplus/issues/1114)), TLC dynamically resolves subclasses through `SimpleFilenameToStream`, which means **the Java class name must perfectly match the TLA+ module name** (e.g., `QueueUtils.java` for `QueueUtils.tla`). It relies on a specialized, custom class-loading mechanism (not Java's `ServiceLoader`).
>
> This means:
> - Your Java class **must** be named exactly after your TLA+ module (e.g., `QueueUtils.java` for `QueueUtils.tla`) ([TLA+ Wiki: codebase:idiosyncrasies](https://docs.tlapl.us/codebase:idiosyncrasies)).
> - It must reside within the `tlc2.overrides` package (modern convention) ([TLA+ Wiki: codebase:idiosyncrasies](https://docs.tlapl.us/codebase:idiosyncrasies)).
> - The `@TLAPlusOperator` annotation's `module` attribute must explicitly map to this target module ([tlaplus/tlaplus#326](https://github.com/tlaplus/tlaplus/issues/326)).
> - The class must implement the `tlc2.overrides.ITLCOverrides` interface ([tlaplus/tlaplus#1114](https://github.com/tlaplus/tlaplus/issues/1114)).
>
> **Potential Resolution:** Naming the class something generic like `TLCOverrides.java` might cause TLC to silently fail to bind the override and use the pure TLA+ definition instead, without crashing ([tlaplus/tlaplus#1114](https://github.com/tlaplus/tlaplus/issues/1114)).

## 4. Java Implementation

Your class must:
1. Be named `TLCOverrides`
2. Live in the `tlc2.overrides` package
3. Implement `ITLCOverrides`
4. Return itself (and any other override classes) from the `get()` method
5. Use `@TLAPlusOperator` annotations with the correct `module` name

### Key Rules

- **Method Signature**: Methods must be `public static`, accept `Value` parameters, and return a `Value`.
- **Types**: Use the value hierarchy in `tlc2.value.impl` (e.g., `BoolValue`, `IntValue`, `StringValue`, `TupleValue`).
- **Thread Safety**: TLC is multi-threaded. Methods must be thread-safe — avoid mutable static state or synchronize access.
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

If you have overrides for multiple TLA+ modules, put them all in `TLCOverrides` (or reference additional classes from `get()`):

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

> ### 📝 Needs Verification: Java Implementation
>
> **Method Signature and Values**: Modern versions (TLC > 1.5.8) use the `tlc2.value.impl` package for these types ([Stack Overflow: module overloading](https://stackoverflow.com/questions/53908653/use-module-overloading-to-implement-a-hash-function-in-tla)).
> 
> **Thread Safety Requirements**: TLC is highly parallelized. Methods must be **strictly thread-safe** (Technical Architecture of TLC Overrides). Treat methods as pure functions (Technical Architecture of TLC Overrides). For shared state, protect sections with `synchronized` or use `TLCGet`/`TLCSet` for per-thread storage ([Learn TLA+: Modules](https://learntla.com/core/modules.html)).
>
> **Supporting Multiple TLA+ Modules**: If you have overrides for multiple TLA+ modules, you might need to create a separate Java class for each module matching its name (e.g., `QueueUtils.java` and `CryptoUtils.java`), rather than combining them into one `TLCOverrides.java`.

## 5. TLA+ Wrapper Module

You need a `.tla` file that declares the operator signatures. TLC will replace these definitions with your Java overrides at runtime. This file also serves as a fallback for tools that don't support Java overrides (SANY, Apalache).

```tla
---- MODULE QueueUtils ----
(* Defines the operator interface. *)
(* TLC will ignore this definition and use the Java override instead. *)
LogState(buffer, wait_set) == TRUE
===========================
```

Place this in the same directory as your main specification so TLC can find it.

## 6. Compilation

### Manual Compilation

```bash
# Compile
javac -cp lib/tla2tools.jar -d classes modules/tlc2/overrides/TLCOverrides.java

# Create the ServiceLoader service file
mkdir -p classes/META-INF/services
echo "tlc2.overrides.TLCOverrides" > classes/META-INF/services/tlc2.overrides.ITLCOverrides
```

### Using `tlaplus-cli`

```bash
tla build
```

This compiles all Java files in your configured modules directory (default: `modules/`), outputs class files to `classes/`, and creates the `ServiceLoader` file automatically. It also automatically fetches the downloaded `tla2tools.jar` from your cache.

## 7. Execution

Your compiled classes (or JAR) must be on the classpath **before** `tla2tools.jar`.

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
tla tlc queue
```

The CLI automatically constructs the correct classpath using your cached `tla2tools.jar` and your compiled `classes/` directory, and runs `tlc2.TLC` with the appropriate Java garbage collection options.

### Using TLA+ Toolbox

1. Go to **File > Preferences > TLA+ Preferences > TLA+ library path locations**.
2. Add the directory containing your compiled class files or your custom JAR.

### Using VS Code

Configure the `tlaplus.java.options` setting in your `settings.json`:

```json
"tlaplus.java.options": "-cp path/to/classes:path/to/tla2tools.jar"
```

## 8. Console Output

`System.out.println` **works** from Java overrides. Output appears in the terminal alongside TLC's own output:

```java
System.out.println("State log: buffer=" + buffer + ", wait_set=" + waitSet);
```

> **Note**: If your print statements are not showing up, the most likely cause is that your override class is **not being loaded** (see §9 — the class must be named `TLCOverrides`). TLC silently falls back to the pure TLA+ definition with no error message.

For large models that produce thousands of log lines, writing to a file may be more practical:

```java
PrintWriter pw = new PrintWriter(new FileWriter("tlc_log.txt", true));
pw.println("buffer=" + buffer + ", wait_set=" + waitSet);
pw.flush();
pw.close();
```

The file path is relative to TLC's working directory (the spec directory when using `tla tlc`).

## 9. Debugging

### Override Not Loading (Silent Failure)

**Symptom**: TLC runs successfully but your Java code has no effect. TLC silently uses the TLA+ definition.

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

> ### 📝 Needs Verification: Debugging Configuration
> 
> If the class naming rule requires matching the TLA+ module exactly, the checklist item #1 and #4 above are likely incorrect.
>
> **Updated Checklist Approach:**
> 1. The Java class name matches the TLA+ module name perfectly (e.g. `QueueUtils.java`).
> 2. It's in the `tlc2.overrides` package.
> 3. It implements `ITLCOverrides`.
> 4. The `get()` method returns `new Class[]{QueueUtils.class}` for that specific mapping.

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

You can verify that `ServiceLoader` can find your class outside of TLC:

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

> **Note**: Even if this test succeeds, TLC may still not load your override if the class is not named `TLCOverrides`, because TLC uses `Class.forName()` with the hardcoded name - not `ServiceLoader`.

### Classpath Order Matters

Your classes must appear **before** `tla2tools.jar` in the classpath. If reversed, TLC won't find your overrides since it stops searching after loading its own classes.

> ### 📝 Needs Verification: Shadowing Details
>
> When the JVM searches for compiled class files, the first occurrence of a particular file or class shadows (hides) any subsequent occurrences ([Oracle: The javac Command](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javac.html)). Hence, your classes must appear **before** `tla2tools.jar` in the classpath to override default implementations. Note that if running from the command line, failure to include *both* your custom JAR and `tla2tools.jar` will result in a `NoClassDefFoundError` or cause the overrides to fail silently (Technical Architecture of TLC Overrides).

### Multiple Override Modules

If you have overrides spread across multiple Java classes, all classes must be returned by `TLCOverrides.get()`:

```java
@Override
public Class[] get() {
    return new Class[]{TLCOverrides.class, AnotherOverride.class};
}
```

> ### 📝 Needs Verification: Class Resolution
>
> If TLC uses `SimpleFilenameToStream` to resolve class names against module names, it will likely independently search for each class named after the target module ([TLA+ Wiki: codebase:idiosyncrasies](https://docs.tlapl.us/codebase:idiosyncrasies)). Having a central `get()` method referencing multiple unrelated classes might be ineffective.