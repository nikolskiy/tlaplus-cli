---- MODULE QueueUtils ----
EXTENDS TLC
(* Defines the operator interface. *)
(* TLC will ignore this definition and use the Java override instead. *)
LogState(buffer, wait_set) == Assert(FALSE, "Error: QueueUtils Java override is not loaded!")
===========================
