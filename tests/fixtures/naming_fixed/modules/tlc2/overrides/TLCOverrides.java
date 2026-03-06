package tlc2.overrides;

import tlc2.overrides.ITLCOverrides;
import tlc2.overrides.TLAPlusOperator;
import tlc2.value.impl.BoolValue;
import tlc2.value.impl.Value;

public class TLCOverrides implements ITLCOverrides {
    @TLAPlusOperator(identifier = "IsOverridden", module = "TestModule")
    public static Value IsOverridden() {
        System.out.println("OVERRIDE_ACTIVE_TLCOverrides");
        return BoolValue.ValTrue;
    }

    @Override
    public Class[] get() {
        return new Class[]{TLCOverrides.class};
    }
}
