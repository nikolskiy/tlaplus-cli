package tlc2.overrides;

import tlc2.overrides.ITLCOverrides;
import tlc2.overrides.TLAPlusOperator;
import tlc2.value.impl.BoolValue;
import tlc2.value.impl.Value;

public class TLCOverrides implements ITLCOverrides {

    @TLAPlusOperator(identifier = "LogState", module = "QueueUtils")
    public static Value LogState(final Value buffer, final Value waitSet) {
        System.out.println("State log test: buffer=" + buffer + ", wait_set=" + waitSet);
        return BoolValue.ValTrue;
    }

    @Override
    public Class[] get() {
        return new Class[]{TLCOverrides.class};
    }
}
