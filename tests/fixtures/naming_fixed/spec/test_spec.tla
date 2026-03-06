---- MODULE test_spec ----
EXTENDS TestModule
VARIABLE x
Init == x = IsOverridden
Next == x' = x
====
