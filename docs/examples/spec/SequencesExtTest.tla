---- MODULE SequencesExtTest ----
EXTENDS SequencesExt, TLC, Integers

VARIABLES x

Init == x = 0
Next == x = 0 /\ x' = 1

(*
  This specification tests the SequencesExt module from CommunityModules.
  
  To distinguish whether TLC is using the Java overrides or the pure TLA+ 
  implementations, we evaluate SetToSeq on a set of size 9.
  
  - Pure TLA+ Implementation:
    SetToSeq(S) is defined as CHOOSE f \in [1..Cardinality(S) -> S] : IsInjective(f).
    For a set S of size 9, [1..9 -> 1..9] contains 9^9 = 387,420,489 elements.
    Evaluating this set is too large for TLC, so it will immediately fail with:
    "TLC computed a set of size 387420489 which is greater than the maximum allowed size of 1000000."
    
  - Java Module Override:
    The Java implementation SetToSeq(val) simply converts the set elements to a 
    tuple using setEnumValue.elems.toArray() which runs in O(N log N) time.
    It returns <<1, 2, 3, 4, 5, 6, 7, 8, 9>> instantly and model checking succeeds.
*)

ASSUME 
  /\ PrintT("Checking if Java overrides for SequencesExt are loaded...")
  /\ LET seq == SetToSeq(1..9)
     IN /\ Len(seq) = 9
        /\ seq[1] = 1
        /\ seq[9] = 9
        /\ PrintT("SUCCESS: Java overrides are loaded! SetToSeq(1..9) evaluated instantly.")

=================================
