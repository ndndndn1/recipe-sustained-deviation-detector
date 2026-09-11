import Std
namespace Drift
def step (streak : Nat) (above : Bool) : Nat :=
  if above then min (streak + 1) 3 else 0
def alarm (streak : Nat) : Bool := streak == 3
theorem bounded (s : Nat) (b : Bool) : step s b ≤ 3 := by
  unfold step
  split <;> omega
theorem reset (s : Nat) : step s false = 0 := by simp [step]
theorem no_early_alarm : alarm (step (step 0 true) true) = false := by decide
theorem reachable_alarm : alarm (step (step (step 0 true) true) true) = true := by decide
end Drift
#print axioms Drift.bounded
#print axioms Drift.reset
#print axioms Drift.no_early_alarm
#print axioms Drift.reachable_alarm
