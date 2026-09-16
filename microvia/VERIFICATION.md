# Verification scope

Requirements denominator is fixed in requirements.json (10 items).

| Requirement | Status | Evidence |
|---|---|---|
| R1 input validation | passed | malformed, missing, duplicate and time-order tests |
| R2 analytical balance | passed | independent 1 A/dm2, 60 min thickness reference within 0.1% |
| R3 area metric | passed | calibrated known mask, exact area fraction |
| R4 stratified analysis | passed | lot and geometry separation tests |
| R5 bounded experimental design | passed | known interval, missing geometry and invalid-data abstention |
| R6 fixed-budget benchmark | passed | 30 runs, 20 observations each, deterministic repeat |
| R7 bilingual HTML | passed | CLI and hostile-label escaping check |
| R8 offline container | passed | existing runtime image with current source mounted read-only; network none |
| R9 Lean and conformance | passed | 4 theorems, only propext; 16 Python gate cases |
| R10 real plating | not run | no bath, equipment or independent process measurements |

Do not remove pending/not-run items from the denominator. Functionality verification is separate from suitability of a physical model. Literature linkage and employment eligibility are not this table's percentages.

Result: 9/10 requirements demonstrated (90%); R10 remains in the denominator. Formal contract: 4/4 theorems accepted by Lean 4.33.1, only propext. Python tests: 12/12 including 4 existing detector regressions.

Synthetic optimization median regret in the scenario time unit: uniform 2.25, random 3.0, adaptive 0.0. These simple smooth synthetic scenarios satisfy the predeclared 10% improvement target; they do not measure real plating minutes saved. The actual-data planner remains a bounded replicated experiment design, not the synthetic optimizer or a production recipe.

The fresh image build encountered package repository DNS/proxy timeouts. Offline validation used the existing `career2026/recipe-drift-evidence:v1` image with current source mounted at `/workspace:ro`; it does not establish a successful clean image build.
