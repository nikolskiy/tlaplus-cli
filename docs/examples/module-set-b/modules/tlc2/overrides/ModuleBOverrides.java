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
