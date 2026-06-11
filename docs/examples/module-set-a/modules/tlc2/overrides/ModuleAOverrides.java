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
