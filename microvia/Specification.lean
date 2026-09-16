import Std
namespace Microvia
structure Gate where
  valid : Bool
  evidence : Bool
  inRange : Bool
  sameLot : Bool
def allow (g : Gate) : Bool := g.valid && g.evidence && g.inRange && g.sameLot
theorem validated (g : Gate) (h : allow g = true) : g.valid = true := by
  simp [allow, Bool.and_eq_true] at h
  exact h.1.1.1
theorem evidenced (g : Gate) (h : allow g = true) : g.evidence = true := by
  simp [allow, Bool.and_eq_true] at h
  exact h.1.1.2
theorem bounded (g : Gate) (h : allow g = true) : g.inRange = true := by
  simp [allow, Bool.and_eq_true] at h
  exact h.1.2
theorem isolated (g : Gate) (h : allow g = true) : g.sameLot = true := by
  simp [allow, Bool.and_eq_true] at h
  exact h.2
end Microvia
#print axioms Microvia.validated
#print axioms Microvia.evidenced
#print axioms Microvia.bounded
#print axioms Microvia.isolated
