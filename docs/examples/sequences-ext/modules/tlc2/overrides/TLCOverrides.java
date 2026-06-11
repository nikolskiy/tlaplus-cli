package tlc2.overrides;

import tlc2.overrides.ITLCOverrides;

public class TLCOverrides implements ITLCOverrides {
    @Override
    public Class[] get() {
        return new Class[] { SequencesExt.class, FiniteSetsExt.class, Functions.class };
    }
}
