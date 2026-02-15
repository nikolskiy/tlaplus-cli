---- MODULE queue ----
EXTENDS Sequences, Integers, QueueUtils

CONSTANTS
    BUFFER_SIZE,
    PRODUCERS,
    CONSUMERS

VARIABLES
    buffer,
    wait_set

Count == Len(buffer)

Wait(t) ==
    /\ wait_set' = wait_set \union {t}
    /\ UNCHANGED buffer

\* g - group of threads to be notified
Notify(g) ==
     \/ /\ (wait_set \intersect g) = {}
        /\ UNCHANGED wait_set
     \/ \E t \in (wait_set \intersect g): wait_set' = wait_set \ {t}


\* t - thread
Produce(t) ==
    \/ /\ Count # BUFFER_SIZE
       /\ buffer' = Append(buffer, 0)
       /\ Notify(CONSUMERS)
    \/ /\ Count = BUFFER_SIZE
       /\ Wait(t)

\* t - thread
Consume(t) ==
    \/ /\ Count # 0
       /\ buffer' = Tail(buffer)
       /\ Notify(PRODUCERS)
    \/ /\ Count = 0
       /\ Wait(t)

Init ==
    /\ buffer = <<>>
    /\ wait_set = {}

Next ==
    /\ LogState(buffer, wait_set)
    /\ \/ \E p \in (PRODUCERS \ wait_set): Produce(p)
       \/ \E c \in (CONSUMERS \ wait_set): Consume(c)
       \* Disable technical deadlock
       \/ UNCHANGED <<buffer, wait_set>>

SomeOneIsActive == wait_set # (PRODUCERS \union CONSUMERS)
NoBufferOverflow == Count <= BUFFER_SIZE

====