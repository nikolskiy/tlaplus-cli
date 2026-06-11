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
